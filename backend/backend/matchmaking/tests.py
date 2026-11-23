import json
from datetime import datetime, timedelta
from unittest import mock

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from api.auth_utils import generate_token
from api.models import Profile
from ft_transcendence.asgi import application
from game.models import Game

from . import consumers


class FakeRedis:
    """The few list commands the matchmaking consumer uses."""

    def __init__(self):
        self.lists = {}

    def lpop(self, key):
        items = self.lists.get(key, [])
        return items.pop(0) if items else None

    def rpush(self, key, value):
        self.lists.setdefault(key, []).append(str(value))

    def lrem(self, key, count, value):
        items = self.lists.get(key, [])
        self.lists[key] = [item for item in items if item != str(value)]


def token_for(user):
    return generate_token(
        {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
    )


class MatchmakingTests(TransactionTestCase):
    def setUp(self):
        self.users = []
        for i in range(12):
            user = User.objects.create_user(username=f"player{i}", password="x-Strong-Pass-1")
            # Profile comes from the post_save signal.
            Profile.objects.filter(user=user).update(is_setup=True)
            user.refresh_from_db()
            self.users.append(user)
        self.redis = FakeRedis()
        patcher = mock.patch.object(consumers, "r", self.redis)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def connect(self, user=None):
        headers = [(b"origin", b"http://localhost")]
        if user is not None:
            headers.append((b"cookie", f"access_token={token_for(user)}".encode()))
        communicator = WebsocketCommunicator(application, "/ws/matchmaking", headers=headers)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    def queue(self):
        return self.redis.lists.get(consumers.QUEUE_KEY, [])

    async def test_users_with_two_digit_ids_are_matched_correctly(self):
        # Regression: the opponent id was read as opponent_id[0], the first
        # character, so user 10 became user 1.
        first, second = self.users[10], self.users[11]
        self.assertGreaterEqual(first.id, 10)
        a = await self.connect(first)
        self.assertEqual(self.queue(), [str(first.id)])
        b = await self.connect(second)

        found_a = json.loads(await a.receive_from(timeout=2))
        found_b = json.loads(await b.receive_from(timeout=2))
        self.assertEqual(found_a["type"], "game_found")
        self.assertEqual(found_a["game_id"], found_b["game_id"])

        game = await database_sync_to_async(Game.objects.get)(id=found_a["game_id"])
        self.assertEqual({game.player1_id, game.player2_id}, {first.id, second.id})
        self.assertEqual(self.queue(), [])
        await a.disconnect()
        await b.disconnect()

    async def test_same_user_twice_is_not_matched_with_itself(self):
        user = self.users[3]
        a = await self.connect(user)
        b = await self.connect(user)
        self.assertEqual(self.queue(), [str(user.id)])
        self.assertEqual(await database_sync_to_async(Game.objects.count)(), 0)
        await a.disconnect()
        await b.disconnect()

    async def test_disconnect_leaves_queue(self):
        a = await self.connect(self.users[0])
        await a.disconnect()
        self.assertEqual(self.queue(), [])

    async def test_bad_and_deleted_entries_are_skipped(self):
        gone = self.users[5]
        gone_id = gone.id
        await database_sync_to_async(gone.delete)()
        self.redis.rpush(consumers.QUEUE_KEY, "None")
        self.redis.rpush(consumers.QUEUE_KEY, gone_id)
        a = await self.connect(self.users[0])
        self.assertEqual(self.queue(), [str(self.users[0].id)])
        self.assertEqual(await database_sync_to_async(Game.objects.count)(), 0)
        await a.disconnect()

    async def test_anonymous_is_rejected(self):
        a = await self.connect()
        output = await a.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)
        self.assertEqual(self.queue(), [])
