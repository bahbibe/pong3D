import json
import uuid
import asyncio
import math
import redis

from channels.generic.websocket import AsyncWebsocketConsumer
from .game_1v1_manager import Game

r = redis.Redis(host="redis")

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game = None
        await self.accept()
        
        player2 = r.lpop(f'queue:1v1')
        if player2 is None:
            r.rpush(f'queue:1v1', self.channel_name)
            return

        self.game = str(uuid.uuid4())
        await self.channel_layer.group_add(self.game, self.channel_name)
        await self.channel_layer.group_add(self.game, player2.decode())
        await self.channel_layer.group_send(self.game, {
            "type": "send_game_id",
            "game_id": self.game,
            })
        game = Game(self.game)
        print(game)
        

    async def disconnect(self, close_code):
        r.lrem(f'queue:1v1', 1, self.channel_name)
        if self.game:
            await self.channel_layer.group_discard(self.game, self.channel_name)

    async def receive(self, text_data):
        self.data = json.loads(text_data)
        print(text_data)

    async def send_game_id(self, event):
        self.game = event["game_id"]
        await self.send(text_data=json.dumps({"game_id": self.game}))
