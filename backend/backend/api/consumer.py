from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Notification
from channels.db import database_sync_to_async
import json
import redis
import os


class FriendsStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        await self.accept()

        self.redis = redis.Redis(host="redis", port=6379, db=0)

        await self.channel_layer.group_add("user_status", self.channel_name)

        self.redis.sadd("online_users", self.user_id)

        online_users = self.redis.smembers("online_users")
        online_users_list = [user_id.decode("utf-8") for user_id in online_users]
        await self.channel_layer.group_send(
            "user_status",
            {
                "type": "user_status_update",
                "user_id": self.user_id,
                "status": "online",
                "online_users": online_users_list,
            },
        )

    async def disconnect(self, close_code):
        self.redis.srem("online_users", self.user_id)

        online_users = self.redis.smembers("online_users")
        online_users_list = [user_id.decode("utf-8") for user_id in online_users]
        await self.channel_layer.group_send(
            "user_status",
            {
                "type": "user_status_update",
                "user_id": self.user_id,
                "status": "offline",
                "online_users": online_users_list,
            },
        )

        await self.channel_layer.group_discard("user_status", self.channel_name)

    async def user_status_update(self, event):
        user_id = event["user_id"]
        status = event["status"]
        online_users = event["online_users"]

        await self.send(
            text_data=json.dumps(
                {
                    "user_id": user_id,
                    "status": status,
                    "online_users": online_users,
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
        self.user_id = self.scope["user"].id
        await self.accept()

        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"user_{self.user_id}", self.channel_name
        )

    async def send_notification(self, event):
        message = event["message"]
        user_id = event["user_id"]
        sender_id = event["sender_id"]
        ctx = event["ctx"]
        avatar = (
            "intra.42.fr" in event["sender_avatar"]
            and event["sender_avatar"]
            or f"{os.getenv('API_URL')}/{event['sender_avatar']}"
        )

        await create_notification(user_id, sender_id, message, "friend_request")

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "type": "notification",
                    "ctx": ctx,
                    "sender": {
                        "uuid": event["sender_uuid"],
                        "username": event["sender_username"],
                        "avatar": avatar,
                    },
                }
            )
        )
