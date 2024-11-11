from channels.generic.websocket import AsyncWebsocketConsumer
import json
import redis


class FriendsStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        await self.accept()

        # Connect to Redis
        self.redis = redis.Redis(host="redis", port=6379, db=0)

        # Join the global user status channel
        await self.channel_layer.group_add("user_status", self.channel_name)

        # Add user to online users set in Redis
        self.redis.sadd("online_users", self.user_id)

        # Send an initial online status update, including all online users
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
        # Remove user from online users set in Redis
        self.redis.srem("online_users", self.user_id)

        # Send an offline status update, including all remaining online users
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

        # Leave the global user status channel
        await self.channel_layer.group_discard("user_status", self.channel_name)

    async def user_status_update(self, event):
        user_id = event["user_id"]
        status = event["status"]
        online_users = event["online_users"]

        # Update the UI based on the received user status and online user list
        await self.send(
            text_data=json.dumps(
                {"user_id": user_id, "status": status, "online_users": online_users, "type": "user_status"}
            )
        )

class NotificationConusmer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        await self.accept()
        print("-- user_id --> ", self.user_id)
        # Join the user's notification channel
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)

    async def disconnect(self, close_code):
        # Leave the user's notification channel
        await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)

    async def send_notification(self, event):
        message = event["message"]
        print("-- notification message --> ", message)

        # Send the notification to the user
        await self.send(
            text_data=json.dumps({"message": message, "type": "notification"})
        )