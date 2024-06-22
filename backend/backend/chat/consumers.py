import json
from pprint import pprint
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(post_save, sender=Message)
def message_saved(sender, instance, created, **kwargs):
    if created:
        # print("----------------------")
        # print(instance)
        # print("----------------------")

        channel_layer = get_channel_layer()
        # conversation = instance.conversation
        # author = instance.author
        async_to_sync(channel_layer.group_send)(
            "notification",
            {
                "type": "notify",
                "notification": {
                    "message": instance,
                },
            },
        )

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
            self.room_name, self.scope["user"], text_data_json["content"]
        )

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notification"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        if self.scope["user"].is_anonymous:
            await self.close(code=4001)
            return

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def notify(self, event):
        notification = event["notification"]
        await self.send(text_data=json.dumps(notification))