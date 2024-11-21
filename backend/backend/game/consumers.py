import json
import uuid
import asyncio
import math
import redis

from channels.generic.websocket import AsyncWebsocketConsumer
from .game_manager import GameManager
from .models import Game, Tournament, Tournament_Participants, Tournament_Game
from channels.db import database_sync_to_async
from .serializers import TournamentGameSerializer, GameSerializer
from django.db.models import Q, F
from .views import invite_friend
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import Notification

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

        try:
            self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]
            if self.tournament_id:
                print("self.tournament_id:", self.tournament_id)
                await self.send_opponent_invite()
        except Exception as error:
            print("error", error)


        
        await self.channel_layer.group_add(self.game_id, self.channel_name)

        # Check if the game instance already exists
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        if not self.game_instance:
            # Create a new game instance
            print("gameinstance create")
            await game_manager.create_game_instance(self.game)
            self.game_instance = await game_manager.get_game_instance(self.game_id)
        
        if self.game and self.game_instance:
            self.game_instance.set_paused(False)
    
    @database_sync_to_async
    def send_opponent_invite(self):
        source_user = self.user
        target_user = self.game.player1 if self.user != self.game.player1 else self.game.player2
        Notification.objects.create(
            user_id=target_user.id,
            message="Tourament game ready",
            type="game_invite",
            sender_id=source_user.id,
            game_id = f"{self.tournament_id}/{self.game.id}"
        )
        notification_channel_layer = get_channel_layer()
        async_to_sync(notification_channel_layer.group_send)(
            f"user_{target_user.id}",
            {
                "type": "send_notification",
                "message": "Tourament game ready",
                "user_id": target_user.id,
                "sender_id": source_user.id,
                "sender_uuid": str(source_user.profile.uuid),
                "sender_username": source_user.username,
                "sender_avatar": str(source_user.profile.avatar),
                "ctx": "game_invite",
                "game_id": f"{self.tournament_id}/{self.game.id}"
            },
        )
    @database_sync_to_async
    def get_game(self):
        try:
            game = Game.objects.get(id=self.game_id)
            if self.user == game.player1:
                self.player = 'player1'
            elif self.user == game.player2:
                self.player = 'player2'
            else:
                return None
            return game
        except Game.DoesNotExist:
            print("game doesn't exist")
            return None

    async def disconnect(self, close_code):
        if self.game and self.game_instance:
            self.game_instance.set_paused(True)
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
            self.game_instance.game_state[self.player] -= 5 * 0.015 * side
        if message_type == 'left':
            self.game_instance.game_state[self.player] += 5 * 0.015 * side

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

    # Broadcast game updates to all players in the game
    async def game_update_message(self, event):
        game_state = event['game_state']
        side = self.player
        game_state['side'] = side
        event['game_state'] = game_state
        await self.send(text_data=json.dumps(event))

    async def send_game_id(self, event):
        game_id = event['game_id']
        self.game_id = game_id
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        # print(self.player, "sending game id")
        await self.join_game()
        await self.send(text_data=json.dumps(event))
    
    async def send_game_end(self, event):
        print("game_over")
        await self.send(text_data=json.dumps({
            'type': "game over"
            }))
        await game_manager.remove_game_instance(self.game_id)
        await self.qualify_next_round()
        print("game_end")
    
    @database_sync_to_async
    def qualify_next_round(self):
        try:
            print("qualify1")
            game = Tournament_Game.objects.get(game__id=self.game_id)
            if game.game.player1 == self.user and game.game.player1_score < game.game.player2_score:
                return
            if game.game.player2 == self.user and game.game.player1_score > game.game.player2_score:
                return
            print("qualify2")
            t_round = game.t_round
            print("qualify3")
            if t_round != 2:
                print("not round 2")
                return
            print("qualify4")
            final = Tournament_Game.objects.get(tournament__uuid=self.tournament_id, t_round=1)
            print("qualify5")
            games = Tournament_Game.objects.filter(tournament__uuid=self.tournament_id, t_round=2)
            print("qualify6")
            if game == games[0]:
                print("game1")
                final.game.player1 = self.user
                final.game.save()
            elif game == games[1]:
                print("game2")
                final.game.player2 = self.user
                final.game.save()
            else:
                print("qualify next round error: *didnt find the games")
            
        except Exception as error:
            print("qualify next round error:", error)
            pass

    async def join_game(self):
        self.game_instance = await game_manager.get_game_instance(self.game_id)
        self.game_instance.set_player_ready(self.player)

class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.user = self.scope["user"]
        self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]

        await self.channel_layer.group_add(self.tournament_id, self.channel_name)
        self.games = await self.create_tournament_games()
        self.t_round = await self.get_player_round()
        await self.set_game(True, self.t_round)
        await self.channel_layer.group_send(
                self.tournament_id,
                {
                    'type': 'update',
                }
            )
        
    @database_sync_to_async
    def get_player_round(self):
        t_round = 2
        games = Tournament_Game.objects.filter((Q(game__player1=self.user) | Q(game__player2=self.user)), tournament=self.tournament)
        for game in games:
            if game.game.player1 == self.user and game.game.player1_score > game.game.player2_score:
                print("won")
                t_round -= 1
            if game.game.player2 == self.user and game.game.player2_score > game.game.player1_score:
                print("won")
                t_round -= 1
        return t_round

    @database_sync_to_async
    def set_game(self, join, t_round):
        if t_round < 2:
            return
        if not join:
            game = Tournament_Game.objects.filter((Q(game__player1=self.user) | Q(game__player2=self.user)), tournament=self.tournament, t_round=t_round).first()
            if game:
                if game.game.player2 == None:
                    game.game.player1 = None
                if game.game.player1 == None:
                    game.game.player2 = None
                game.game.save()
        print("tround dd ", t_round)
        if join:
            # if already joined
            if Tournament_Game.objects.filter((Q(game__player1=self.user) | Q(game__player2=self.user)), tournament=self.tournament, t_round=t_round).exists():
                return
            # get empty seats
            game = Tournament_Game.objects.filter((Q(game__player1=None) | Q(game__player2=None)), tournament=self.tournament, t_round=t_round).order_by("id").first()
            if game:
                print("joining game")
                if game.game.player1:
                    game.game.player2 = self.user
                else:
                    game.game.player1 = self.user
                game.game.save()
            else:
                print("didnt find spot")

    @database_sync_to_async
    def call_serializer(self, games):
        return TournamentGameSerializer(games, many=True).data

    async def disconnect(self, close_code):
        await self.set_game(False, self.t_round)
        await self.channel_layer.group_send(
                self.tournament_id,
                {
                    'type': 'update',
                }
            )
        await self.channel_layer.group_discard(self.tournament_id, self.channel_name)

    async def receive(self, text_data):
        print(text_data)
    
    async def update(self, event):
        await self.send(text_data=json.dumps(event))

    async def start(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_tournament_games(self):
        self.tournament = Tournament.objects.get(uuid=self.tournament_id)
        if not Tournament_Game.objects.filter(tournament=self.tournament).exists():
            for i in range(1,3,1):
                print("i",i)
                for j in range(1,i+1,1):
                    print("j",j)
                    game = Game.objects.create(
                                player1=None,
                                player2=None,
                    )
                    Tournament_Game.objects.create(
                        tournament=self.tournament,
                        game=game,
                        t_round=i
                    )
        return Tournament_Game.objects.filter(tournament=self.tournament)
            
    def pairwise(self, iterable):
        "s -> (s0, s1), (s2, s3), (s4, s5), ..."
        a = iter(iterable)
        return zip(a, a)