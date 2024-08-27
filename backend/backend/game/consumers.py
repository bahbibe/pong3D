import json
import uuid
import asyncio
import math
import redis

from channels.generic.websocket import AsyncWebsocketConsumer
from .game_manager import GameManager

game_manager = GameManager()

r = redis.Redis(host="redis")

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = None
        self.player = 'player2'
        self.game_instance = None
        await self.accept()
        print(self.scope["user"])
        
        player2 = r.lpop(f'queue:1v1')
        if player2 is None:
            self.player = 'player1'
            r.rpush(f'queue:1v1', self.channel_name)
            return

        self.game_id = str(uuid.uuid4())
        await self.channel_layer.group_add(self.game_id, self.channel_name)
        await self.channel_layer.group_add(self.game_id, player2.decode())

        # Check if the game instance already exists
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        if not self.game_instance:
            # Create a new game instance
            await game_manager.create_game_instance(self.game_id, self.scope['user'])
            self.game_instance = await game_manager.get_game_instance(self.game_id)
        

    async def disconnect(self, close_code):
        r.lrem(f'queue:1v1', 1, self.channel_name)
        if self.game_id:
            await self.channel_layer.group_discard(self.game_id, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        print("receive type", message_type)

        if not self.game_instance:
            return
        if message_type == 'right':
            self.game_instance.game_state[self.player] -= 5 * self.game_instance.speed
            if self.game_instance.game_state[self.player] < -1.6:
                self.game_instance.game_state[self.player] = -1.6

        if message_type == 'left':
            self.game_instance.game_state[self.player] += 5 * self.game_instance.speed
            if self.game_instance.game_state[self.player] > 1.6:
                self.game_instance.game_state[self.player] = 1.6
        
        if message_type == 'game_update':
            # Update the game state based on the received data
            await self.update_game_state(text_data_json)

            # Broadcast the updated game state to all players in the game
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_update_message',
                    'game_state': text_data_json
                }
            )

    # Handle game state updates
    async def update_game_state(self, game_state):
        # Update the game state based on the received data
        pass

    # Broadcast game updates to all players in the game
    async def game_update_message(self, event):
        game_state = event['game_state']
        await self.send(text_data=json.dumps(game_state))

    async def send_game_id(self, event):
        game_id = event['game_id']
        self.game_id = game_id
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        print(self.player, "sending game id")
        await self.join_game()
        await self.send(text_data=json.dumps(game_id))

    async def join_game(self):
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        if self.player == 'player1':
            self.game_instance.setPlayer1(self.scope['user'])
        if self.player == 'player2':
            self.game_instance.setPlayer2(self.scope['user'])