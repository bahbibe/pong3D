import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept(),
        print("Connected")
    async def receive(self, text_data):
        data_json = json.loads(text_data)
        texto = data_json['message']
        await self.send(text_data=json.dumps({
            "type": "chat-message",
            "message": texto
            }))
       
       
