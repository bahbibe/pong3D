from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Notification
from channels.db import database_sync_to_async
import json
import os
from redis import asyncio as aioredis

from utils.redis_url import redis_url

# Close code the frontend treats as "log in again".
CLOSE_UNAUTHORIZED = 4001

# Hash user_id -> number of open status sockets. A user is online while the
# count is above 0, so closing one of two tabs does not mark them offline.
ONLINE_KEY = "online_counts"

# Shared async client (sync redis calls would block the event loop that
# also runs the game loops). Tests replace it with an in-memory fake.
r = aioredis.Redis.from_url(redis_url(), decode_responses=True)


async def online_user_ids():
    counts = await r.hgetall(ONLINE_KEY)
    return [user_id for user_id, count in counts.items() if int(count) > 0]


async def reject_anonymous(consumer):
    user = consumer.scope.get("user")
    if user is None or user.is_anonymous:
        await consumer.accept()
        await consumer.close(code=CLOSE_UNAUTHORIZED)
        return True
    return False


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


@database_sync_to_async
def create_notification(user_id, sender_id, message, type):
    Notification.objects.create(
        user_id=user_id, message=message, type=type, sender_id=sender_id
    )


class NotificationConusmer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = None
        if await reject_anonymous(self):
            return
        self.user_id = self.scope["user"].id
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.user_id is None:
            return
        await self.channel_layer.group_discard(
            f"user_{self.user_id}", self.channel_name
        )

    async def send_notification(self, event):
        message = event["message"]
        ctx = event["ctx"]
        avatar = (
            "cdn.intra.42.fr" in event["sender_avatar"]
            and event["sender_avatar"]
            or f"{os.getenv('API_URL')}/{event['sender_avatar']}"
        )
        game_id = event["game_id"] if "game_id" in event else None

        await self.send(
            text_data=json.dumps(
                {
                    # Lets the client mark this one notification as read.
                    "uuid": event.get("notification_uuid"),
                    "message": message,
                    "type": "notification",
                    "ctx": ctx,
                    "sender": {
                        "uuid": event["sender_uuid"],
                        "username": event["sender_username"],
                        "avatar": avatar,
                    },
                    "game_id": game_id,
                }
            )
        )
