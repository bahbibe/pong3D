from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
import redis
from game.models import Game
import json

from channels.db import database_sync_to_async

r = redis.Redis(host="redis", decode_responses=True)

class Matchmaking(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        await self.accept()
        self.opponent_id = r.lpop(f'matchmaking:random')
        print(f"player {self.user.id} added to queue")
        await self.channel_layer.group_add(f"matchmaking_{self.user.id}", self.channel_name)
        if self.user == await self.get_user(self.opponent_id):
            r.rpush(f"matchmaking:random", self.user.id)
            return
        if self.opponent_id is None :
            r.rpush(f"matchmaking:random", self.user.id)
            return

        self.game = await self.create_game()
        await self.channel_layer.group_send(
            f"matchmaking_{self.opponent_id}",
            {
                'type': 'game_found',
                'game_id': self.game.id
            }
        )
        await self.channel_layer.group_send(
            f"matchmaking_{self.user.id}",
            {
                'type': 'game_found',
                'game_id': self.game.id
            }
        )

    @database_sync_to_async
    def get_user(self, user_id):
        if not user_id:
            return None
        user = User.objects.get(id=int(user_id))
        print(user.id)
        return user
    @database_sync_to_async
    def create_game(self):
        opponent = User.objects.get(id=int(self.opponent_id[0]))
        game = Game.objects.create(
            player1 = opponent,
            player2 = self.user,
        )

        if game is None :
            print("game not created")
        else:
            print(f"game created {game.id}")
        
        return game

    async def disconnect(self, close_code):
        # Handle the WebSocket disconnection
        print(f"player {self.user.id} removed from queue")
        r.lrem(f'matchmaking:random', 1, self.user.id)
        pass

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        pass

    async def game_found(self, event) :
        await self.send(text_data=json.dumps(event))