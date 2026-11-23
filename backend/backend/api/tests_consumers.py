import json
from datetime import datetime, timedelta
from unittest import mock

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from ft_transcendence.asgi import application

from . import consumer
from .auth_utils import generate_token
from .models import Profile


class FakeRedis:
    """Async hash commands used by the presence consumer."""

    def __init__(self):
        self.hashes = {}

    async def hincrby(self, key, field, amount):
        h = self.hashes.setdefault(key, {})
        h[str(field)] = int(h.get(str(field), 0)) + amount
        return h[str(field)]

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def hdel(self, key, field):
        self.hashes.get(key, {}).pop(str(field), None)


def make_user(username):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    Profile.objects.filter(user=user).update(is_setup=True)
    return user


def token_for(user):
    return generate_token(
        {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
    )


class PresenceTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.redis = FakeRedis()
        patcher = mock.patch.object(consumer, "r", self.redis)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def connect(self, path, user=None):
        headers = [(b"origin", b"http://localhost")]
        if user is not None:
            headers.append((b"cookie", f"access_token={token_for(user)}".encode()))
        communicator = WebsocketCommunicator(application, path, headers=headers)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def next_status(self, communicator):
        return json.loads(await communicator.receive_from(timeout=2))

    async def test_closing_one_of_two_tabs_keeps_user_online(self):
        # Regression: the online set was per user, so closing one tab
        # marked the user offline while another tab was still open.
        watcher = await self.connect("/ws/status/", self.bob)
        await self.next_status(watcher)  # bob online

        tab1 = await self.connect("/ws/status/", self.alice)
        message = await self.next_status(watcher)
        self.assertEqual((message["status"], message["user_id"]), ("online", self.alice.id))

        tab2 = await self.connect("/ws/status/", self.alice)
        await tab2.receive_from(timeout=2)  # list sent to the new tab only
        await tab1.disconnect()
        self.assertTrue(await watcher.receive_nothing(timeout=0.3))
        self.assertIn(str(self.alice.id), await consumer.online_user_ids())

        await tab2.disconnect()
        message = await self.next_status(watcher)
        self.assertEqual((message["status"], message["user_id"]), ("offline", self.alice.id))
        self.assertNotIn(str(self.alice.id), message["online_users"])
        await watcher.disconnect()

    async def test_anonymous_status_socket_is_rejected(self):
        anon = await self.connect("/ws/status/")
        output = await anon.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)
        self.assertEqual(await consumer.online_user_ids(), [])

    async def test_anonymous_notification_socket_is_rejected(self):
        anon = await self.connect("/ws/notifications/")
        output = await anon.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)
