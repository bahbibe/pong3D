"""Online status of users (/ws/status/)."""

import json

from channels.generic.websocket import AsyncWebsocketConsumer
from redis import asyncio as aioredis

from apps.accounts.ws_auth import reject_anonymous
from core.redis_url import redis_url

# Hash user_id -> number of open status sockets. A user is online while the
# count is above 0, so closing one of two tabs does not mark them offline.
ONLINE_KEY = "online_counts"

# Shared async client (sync redis calls would block the event loop that
# also runs the game loops). Tests replace it with an in-memory fake.
r = aioredis.Redis.from_url(redis_url(), decode_responses=True)


async def online_user_ids():
    counts = await r.hgetall(ONLINE_KEY)
    return [user_id for user_id, count in counts.items() if int(count) > 0]


class FriendsStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = None
        if await reject_anonymous(self):
            return
        self.user_id = self.scope["user"].id
        await self.accept()
        await self.channel_layer.group_add("user_status", self.channel_name)

        count = await r.hincrby(ONLINE_KEY, self.user_id, 1)
        online_users = await online_user_ids()
        if count == 1:
            # First socket of this user: tell everyone.
            await self.broadcast("online", online_users)
        else:
            # Another tab: only this socket needs the current list.
            await self.user_status_update(
                {"user_id": self.user_id, "status": "online", "online_users": online_users}
            )

    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        count = await r.hincrby(ONLINE_KEY, self.user_id, -1)
        if count <= 0:
            await r.hdel(ONLINE_KEY, self.user_id)
            await self.broadcast("offline", await online_user_ids())
        await self.channel_layer.group_discard("user_status", self.channel_name)

    async def broadcast(self, status, online_users):
        await self.channel_layer.group_send(
            "user_status",
            {
                "type": "user_status_update",
                "user_id": self.user_id,
                "status": status,
                "online_users": online_users,
            },
        )

    async def user_status_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "user_id": event["user_id"],
                    "status": event["status"],
                    "online_users": event["online_users"],
                    "type": "user_status",
                }
            )
        )
