import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from redis import asyncio as aioredis

from apps.game.models import Game
from core.redis_url import redis_url

User = get_user_model()

QUEUE_KEY = "matchmaking:random"
CLOSE_UNAUTHORIZED = 4001

# Shared async client (sync calls would block the event loop).
# Tests replace it with an in-memory fake.
r = aioredis.Redis.from_url(redis_url(), decode_responses=True)


@database_sync_to_async
def get_queued_user(raw_id):
    """User for a queue entry, or None if the entry is bad or the user is gone."""
    try:
        return User.objects.filter(id=int(raw_id)).first()
    except (TypeError, ValueError):
        return None


@database_sync_to_async
def create_game(player1, player2):
    return Game.objects.create(player1=player1, player2=player2)


class Matchmaking(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.queued = False

        if self.user is None or self.user.is_anonymous:
            await self.accept()
            await self.close(code=CLOSE_UNAUTHORIZED)
            return

        await self.channel_layer.group_add(f"matchmaking_{self.user.id}", self.channel_name)

        # Drop older entries of this user (other tab, missed disconnect)
        # so a user is never matched with themselves.
        await r.lrem(QUEUE_KEY, 0, self.user.id)

        opponent = None
        while opponent is None:
            raw_id = await r.lpop(QUEUE_KEY)
            if raw_id is None:
                break
            candidate = await get_queued_user(raw_id)
            if candidate is not None and candidate.id != self.user.id:
                opponent = candidate

        if opponent is None:
            await r.rpush(QUEUE_KEY, self.user.id)
            self.queued = True
            await self.accept()
            return

        game = await create_game(player1=opponent, player2=self.user)
        await self.accept()
        for user_id in (opponent.id, self.user.id):
            await self.channel_layer.group_send(
                f"matchmaking_{user_id}", {"type": "game_found", "game_id": game.id}
            )

    async def disconnect(self, close_code):
        if self.user is None or self.user.is_anonymous:
            return
        if self.queued:
            await r.lrem(QUEUE_KEY, 0, self.user.id)
        await self.channel_layer.group_discard(f"matchmaking_{self.user.id}", self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        return

    async def game_found(self, event):
        self.queued = False
        await self.send(text_data=json.dumps(event))
