import json
import pprint
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        pprint.pprint(self.scope)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        if  self.scope['user'].is_anonymous:
            await self.close(code=4001)
            return

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(json.dumps(text_data_json, indent=4))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'data' : text_data_json
            }
        )

    async def chat_message(self, event):
        data = event['data']
        await self.send(text_data=json.dumps({
            'data': data
        }))
       
       
