import json
import uuid
import asyncio
import math
import redis

from channels.generic.websocket import AsyncWebsocketConsumer
from .game_manager import GameManager
from .models import Game, Tournament, Tournament_Participants
from channels.db import database_sync_to_async

game_manager = GameManager()

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.user = self.scope["user"]
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.player = 'player2'

        self.game = await self.get_game()
        if self.game is None:
            print("game doesn't exist 2")
            await self.close()
            return
        
        await self.channel_layer.group_add(self.game_id, self.channel_name)

        # Check if the game instance already exists
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        if not self.game_instance:
            # Create a new game instance
            await game_manager.create_game_instance(self.game)
            self.game_instance = await game_manager.get_game_instance(self.game_id)
        
    @database_sync_to_async
    def get_game(self):
        try:
            game = Game.objects.get(id=self.game_id)
            if self.user == game.player1:
                self.player = 'player1'
            return game
        except Game.DoesNotExist:
            print("game doesn't exist")
            return None

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_id, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        # print("receive type", message_type)

        if not self.game_instance:
            return

        side = -1
        if self.game.player1 == self.user :
            side = 1
        if message_type == 'right':
            self.game_instance.game_state[self.player] -= 5 * self.game_instance.speed * side
        if message_type == 'left':
            self.game_instance.game_state[self.player] += 5 * self.game_instance.speed * side

        if self.game_instance.game_state[self.player] < -3:
            self.game_instance.game_state[self.player] = -3
        if self.game_instance.game_state[self.player] > 3:
            self.game_instance.game_state[self.player] = 3
        
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
        side = self.player
        game_state['side'] = side
        await self.send(text_data=json.dumps(game_state))

    async def send_game_id(self, event):
        game_id = event['game_id']
        self.game_id = game_id
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        print(self.player, "sending game id")
        await self.join_game()
        await self.send(text_data=json.dumps(game_id))
    
    async def send_game_end(self, event):
        await self.send(text_data=json.dumps("game over"))

    async def join_game(self):
        self.game_instance = await game_manager.get_game_instance(self.game_id)



class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.user = self.scope["user"]
        self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]
        self.participant = await self.get_participant(self.tournament_id)
        if self.participant is None:
            await self.close()
            print("didnt find")
            return
        
        await self.channel_layer.group_add(self.tournament_id, self.channel_name)
        await self.set_participant_ready(True)
        await self.channel_layer.group_send(
                self.tournament_id,
                {
                    'type': 'update',
                }
            )

    @database_sync_to_async
    def get_participant(self, tournament_id):
        try:
            tournament = Tournament.objects.get(uuid=tournament_id)
            return Tournament_Participants.objects.select_related('tournament').get(
                tournament=tournament,
                player=self.user
            )
        except (Tournament.DoesNotExist, Tournament_Participants.DoesNotExist):
            return None
    
    @database_sync_to_async
    def set_participant_ready(self, ready_status):
        if self.participant:
            self.participant.ready = ready_status
            self.participant.save()
            print(f"Set to {self.participant.id, self.participant.tournament, self.participant.player}")
        print("participant is empty")

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
                self.tournament_id,
                {
                    'type': 'update',
                }
            )
        await self.set_participant_ready(False)
        await self.channel_layer.group_discard(self.tournament_id, self.channel_name)

    async def receive(self, text_data):
        print(text_data)
    
    async def update(self, event):
        await self.send(text_data=json.dumps(event["type"]))
