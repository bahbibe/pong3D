import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import Message
from .utils import get_chat_friendship

MAX_MESSAGE_LENGTH = 1000

# Close codes understood by the frontend (ws/ws.js).
CLOSE_UNAUTHORIZED = 4001
CLOSE_FORBIDDEN = 4003


@database_sync_to_async
def canonical_conversation(user, conversation):
    """Friendship uuid in canonical form, or None if the user may not chat."""
    friendship = get_chat_friendship(user, conversation)
    return str(friendship.uuid) if friendship else None


@database_sync_to_async
def save_message(user, conversation, content):
    """Store the message if `user` may still chat in `conversation`, else
    None: the friendship may have been blocked or removed after the socket
    was opened."""
    friendship = get_chat_friendship(user, conversation)
    if friendship is None:
        return None
    return Message.objects.create(
        author=user,
        content=content,
        friendship=friendship,
        # Read by the previous release (rollback); see chat migration 0010.
        conversation=str(friendship.uuid),
        timestamp=timezone.now(),
    )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = None
        self.room_group_name = None
        self.joined_group = False
        user = self.scope.get("user")

        # Accept first so the client receives the close code.
        await self.accept()

        if user is None or user.is_anonymous:
            await self.close(code=CLOSE_UNAUTHORIZED)
            return

        requested = self.scope["url_route"]["kwargs"]["conversation"]
        self.room_name = await canonical_conversation(user, requested)
        if self.room_name is None:
            await self.close(code=CLOSE_FORBIDDEN)
            return

        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.joined_group = True

    async def disconnect(self, close_code):
        if self.joined_group:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not self.joined_group or text_data is None:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return

        content = payload.get("content")
        if not isinstance(content, str):
            return
        content = content.strip()
        if not content or len(content) > MAX_MESSAGE_LENGTH:
            return

        user = self.scope["user"]
        message = await save_message(user, self.room_name, content)
        if message is None:
            await self.close(code=CLOSE_FORBIDDEN)
            return

        # Never forward client JSON: author and timestamp come from the server.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "author": user.username,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                },
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
