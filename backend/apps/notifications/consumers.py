"""Live notifications (/ws/notifications/). Rows are created by
services.notify(), which pushes to the group "user_<id>"."""

import json

from channels.generic.websocket import AsyncWebsocketConsumer

from apps.accounts.ws_auth import reject_anonymous

from .serializers import avatar_url


class NotificationConsumer(AsyncWebsocketConsumer):
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
        await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)

    async def send_notification(self, event):
        message = event["message"]
        ctx = event["ctx"]
        sender = None
        if event.get("sender_uuid") is not None:
            sender = {
                "uuid": event["sender_uuid"],
                "username": event["sender_username"],
                "avatar": avatar_url(event["sender_avatar"]),
            }
        game_id = event.get("game_id")

        await self.send(
            text_data=json.dumps(
                {
                    # Lets the client mark this one notification as read.
                    "uuid": event.get("notification_uuid"),
                    "message": message,
                    "type": "notification",
                    "ctx": ctx,
                    "sender": sender,
                    "game_id": game_id,
                }
            )
        )
