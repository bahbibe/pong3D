import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from .game_manager import (
    DIRECTIONS,
    WINNING_SCORE,
    BotManager,
    GameManager,
    bot_group_name,
)
from .models import Game, Tournament, Tournament_Game
from . import tournament
from channels.db import database_sync_to_async
from .serializers import TournamentGameSerializer
from django.db.models import Q
from apps.notifications.services import notify

logger = logging.getLogger(__name__)

# Close codes (frontend treats 4001 as "log in again").
CLOSE_UNAUTHORIZED = 4001
CLOSE_FORBIDDEN = 4003
CLOSE_NOT_FOUND = 4004


def parse_message(text_data):
    """Return the decoded JSON object, or None for anything else."""
    if not text_data:
        return None
    try:
        payload = json.loads(text_data)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def is_anonymous(user):
    return user is None or user.is_anonymous


async def reject(consumer, code):
    """Accept then close, so the browser receives the close code."""
    await consumer.accept()
    await consumer.close(code=code)


game_manager = GameManager()
bot_manager = BotManager()


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game = None
        self.game_instance = None
        self.player = None
        self.joined_group = False
        self.user = self.scope.get("user")
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.tournament_id = self.scope["url_route"]["kwargs"].get("tournament_id")
        # Accept only once the game instance exists, so the first client
        # message always finds it.

        if is_anonymous(self.user):
            await reject(self, CLOSE_UNAUTHORIZED)
            return

        self.game = await self.get_game()
        if self.game is None:
            await reject(self, CLOSE_FORBIDDEN)
            return

        if (
            self.game.is_finished
            or self.game.player1_score >= WINNING_SCORE
            or self.game.player2_score >= WINNING_SCORE
        ):
            # Finished game: do not start a new loop (it would end at once
            # and run the end-of-game logic again).
            await self.accept()
            await self.send(text_data=json.dumps({"type": "game over"}))
            await self.close()
            return

        if self.tournament_id:
            try:
                await self.send_opponent_invite()
            except Exception:
                logger.exception("could not send tournament invite")

        await self.channel_layer.group_add(self.game_id, self.channel_name)
        self.joined_group = True

        self.game_instance = await game_manager.get_game_instance(self.game_id)
        if not self.game_instance:
            self.game_instance = await game_manager.create_game_instance(self.game)
        self.game_instance.player_connected(self.player)
        await self.accept()

    @database_sync_to_async
    def send_opponent_invite(self):
        source_user = self.user
        target_user = self.game.player1 if self.user != self.game.player1 else self.game.player2
        notify(
            target_user,
            source_user,
            "game_invite",
            "Tourament game ready",
            game_id=f"{self.tournament_id}/{self.game.id}",
        )

    @database_sync_to_async
    def get_game(self):
        """Load the game and set self.player. None if not one of its players."""
        try:
            game = Game.objects.select_related("player1", "player2").get(id=int(self.game_id))
        except (Game.DoesNotExist, ValueError):
            return None
        if game.player1_id == self.user.id:
            self.player = "player1"
        elif game.player2_id == self.user.id:
            self.player = "player2"
        else:
            return None
        return game

    async def disconnect(self, close_code):
        if self.game_instance is not None and self.player is not None:
            self.game_instance.player_disconnected(self.player)
        if self.joined_group:
            await self.channel_layer.group_discard(self.game_id, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        payload = parse_message(text_data)
        if payload is None or self.game_instance is None:
            return
        if payload.get("type") != "move":
            return
        direction = DIRECTIONS.get(payload.get("direction"))
        if direction is None:
            return
        # player2 looks at the board from the other side.
        side = 1 if self.player == "player1" else -1
        self.game_instance.set_direction(self.player, direction * side)

    async def game_update_message(self, event):
        game_state = dict(event["game_state"], side=self.player)
        await self.send(text_data=json.dumps({"type": event["type"], "game_state": game_state}))

    async def send_game_id(self, event):
        await self.join_game()
        await self.send(text_data=json.dumps(event))

    async def send_game_end(self, event):
        await self.send(text_data=json.dumps({"type": "game over"}))
        await game_manager.remove_game_instance(self.game_id)
        self.game_instance = None

    async def join_game(self):
        instance = await game_manager.get_game_instance(self.game_id)
        if instance is not None and self.player is not None:
            self.game_instance = instance
            instance.set_player_ready(self.player)


class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.t_round = None
        self.tournament = None
        self.joined_group = False
        self.user = self.scope.get("user")
        self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]

        if is_anonymous(self.user):
            await reject(self, CLOSE_UNAUTHORIZED)
            return

        try:
            self.games = await self.create_tournament_games()
        except Tournament.DoesNotExist:
            await reject(self, CLOSE_NOT_FOUND)
            return

        await self.accept()
        await self.channel_layer.group_add(self.tournament_id, self.channel_name)
        self.joined_group = True
        self.t_round = await self.get_player_round()
        await self.set_game(True, self.t_round)
        await self.channel_layer.group_send(
            self.tournament_id,
            {
                "type": "update",
            },
        )

    @database_sync_to_async
    def get_player_round(self):
        t_round = 2
        games = Tournament_Game.objects.filter(
            (Q(game__player1=self.user) | Q(game__player2=self.user)), tournament=self.tournament
        )
        for game in games:
            if game.game.player1 == self.user and game.game.player1_score > game.game.player2_score:
                logger.debug("%s won a round", self.user)
                t_round -= 1
            if game.game.player2 == self.user and game.game.player2_score > game.game.player1_score:
                logger.debug("%s won a round", self.user)
                t_round -= 1
        return t_round

    @database_sync_to_async
    def set_game(self, join, t_round):
        if t_round < tournament.FIRST_ROUND:
            return
        if join:
            tournament.take_seat(self.tournament, self.user, t_round)
        else:
            tournament.leave_seat(self.tournament, self.user, t_round)

    @database_sync_to_async
    def call_serializer(self, games):
        return TournamentGameSerializer(games, many=True).data

    async def disconnect(self, close_code):
        if self.t_round is not None:
            await self.set_game(False, self.t_round)
        if self.joined_group:
            await self.channel_layer.group_send(self.tournament_id, {"type": "update"})
            await self.channel_layer.group_discard(self.tournament_id, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Clients do not send anything on this socket.
        return

    async def update(self, event):
        await self.send(text_data=json.dumps(event))

    async def start(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_tournament_games(self):
        self.tournament = Tournament.objects.get(uuid=self.tournament_id)
        tournament.ensure_bracket(self.tournament)
        return Tournament_Game.objects.filter(tournament=self.tournament)

    def pairwise(self, iterable):
        "s -> (s0, s1), (s2, s3), (s4, s5), ..."
        a = iter(iterable)
        return zip(a, a)


class GameBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bot_instance = None
        self.group_name = None
        self.player = "player1"
        self.user = self.scope.get("user")

        if is_anonymous(self.user):
            await reject(self, CLOSE_UNAUTHORIZED)
            return

        self.group_name = bot_group_name(self.user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        self.bot_instance = await bot_manager.create_bot_instance(self.user)
        await self.accept()

    async def stop_own_instance(self):
        # Another tab may have started a newer bot game; leave that one alone.
        current = await bot_manager.get_bot_instance(self.user.id)
        if current is not None and current is self.bot_instance:
            await bot_manager.remove_bot_instance(self.user.id)
        self.bot_instance = None

    async def disconnect(self, close_code):
        if self.bot_instance is not None:
            await self.stop_own_instance()
        if self.group_name is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        payload = parse_message(text_data)
        if payload is None or self.bot_instance is None:
            return
        if payload.get("type") != "move":
            return
        direction = DIRECTIONS.get(payload.get("direction"))
        if direction is None:
            return
        self.bot_instance.set_direction(self.player, direction)

    async def game_update_message(self, event):
        game_state = dict(event["game_state"], side=self.player)
        await self.send(text_data=json.dumps({"type": event["type"], "game_state": game_state}))

    async def send_game_id(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_game_end(self, event):
        await self.send(text_data=json.dumps({"type": "game over"}))
        if self.bot_instance is not None:
            await self.stop_own_instance()
