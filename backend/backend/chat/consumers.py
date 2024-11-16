import json
from pprint import pprint
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message



@database_sync_to_async
def save_message(conversation, user, message):
    Message.objects.create(author=user, content=message, conversation=conversation)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["conversation"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        if self.scope["user"].is_anonymous:
            await self.close(code=4001)
            return

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.close(code=4001)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": text_data_json,
            },
        )
        await save_message(
            self.room_name,
            self.scope["user"],
            text_data_json["content"],
        )

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))
