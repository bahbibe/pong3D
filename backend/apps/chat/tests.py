import json
from datetime import datetime, timedelta

import pyotp
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from apps.accounts.auth_utils import generate_token
from apps.accounts.models import Profile
from apps.friends.models import Friendship
from config.asgi import application

from .models import Message


def token_for(user, is_tfa_verified=True):
    return generate_token(
        {
            "id": user.id,
            "is_tfa_verified": is_tfa_verified,
            "exp": datetime.now() + timedelta(hours=1),
        }
    )


def make_user(username, **profile_fields):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    # Profile comes from the post_save signal.
    Profile.objects.filter(user=user).update(is_setup=True, **profile_fields)
    user.refresh_from_db()
    return user


class ChatTestCase(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.eve = make_user("eve")
        self.friendship = Friendship.objects.create(
            source_user=self.alice, target_user=self.bob, status=Friendship.ACCEPTED
        )
        self.room = str(self.friendship.uuid)

    async def connect(self, user=None, room=None, token=None):
        headers = [(b"origin", b"http://localhost")]
        if token is None and user is not None:
            token = token_for(user)
        if token is not None:
            headers.append((b"cookie", f"access_token={token}".encode()))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{room or self.room}/", headers=headers
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def assert_closed_with(self, communicator, code):
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output["type"], "websocket.close")
        self.assertEqual(output.get("code"), code)

    @database_sync_to_async
    def message_count(self):
        return Message.objects.count()

    @database_sync_to_async
    def set_status(self, status):
        Friendship.objects.filter(pk=self.friendship.pk).update(status=status)


class ChatConsumerTests(ChatTestCase):
    async def test_author_comes_from_session_not_client(self):
        alice = await self.connect(self.alice)
        bob = await self.connect(self.bob)

        await alice.send_to(
            text_data=json.dumps({"author": "bob", "content": "  hi <b>bob</b> "})
        )
        received = json.loads(await bob.receive_from(timeout=2))
        self.assertEqual(received["author"], "alice")
        self.assertEqual(received["content"], "hi <b>bob</b>")
        self.assertIn("timestamp", received)

        message = await database_sync_to_async(Message.objects.get)()
        self.assertEqual(message.author_id, self.alice.id)
        self.assertEqual(message.conversation, self.room)

        await alice.disconnect()
        await bob.disconnect()

    async def test_non_member_is_rejected(self):
        eve = await self.connect(self.eve)
        await self.assert_closed_with(eve, 4003)

    async def test_unknown_or_malformed_room_is_rejected(self):
        eve = await self.connect(self.alice, room="not-a-uuid")
        await self.assert_closed_with(eve, 4003)

    async def test_anonymous_is_rejected(self):
        anon = await self.connect()
        await self.assert_closed_with(anon, 4001)

    async def test_invalid_token_is_rejected_not_left_hanging(self):
        anon = await self.connect(token="not-a-jwt")
        await self.assert_closed_with(anon, 4001)

    async def test_blocked_friendship_cannot_connect(self):
        await self.set_status(Friendship.BLOCKED)
        bob = await self.connect(self.bob)
        await self.assert_closed_with(bob, 4003)

    async def test_block_after_connect_stops_messages(self):
        bob = await self.connect(self.bob)
        await self.set_status(Friendship.BLOCKED)
        await bob.send_to(text_data=json.dumps({"content": "still here?"}))
        await self.assert_closed_with(bob, 4003)
        self.assertEqual(await self.message_count(), 0)

    async def test_pending_friendship_cannot_chat(self):
        await self.set_status(Friendship.PENDING)
        bob = await self.connect(self.bob)
        await self.assert_closed_with(bob, 4003)

    async def test_bad_payloads_are_ignored(self):
        alice = await self.connect(self.alice)
        for payload in [
            "not json",
            json.dumps(["list"]),
            json.dumps({"content": 123}),
            json.dumps({"content": "   "}),
            json.dumps({"content": "x" * 1001}),
            json.dumps({"nothing": True}),
        ]:
            await alice.send_to(text_data=payload)
        self.assertTrue(await alice.receive_nothing(timeout=0.5))
        self.assertEqual(await self.message_count(), 0)
        await alice.disconnect()


class WebSocketOriginTests(ChatTestCase):
    async def test_foreign_origin_is_refused(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.room}/",
            headers=[
                (b"origin", b"https://evil.example"),
                (b"cookie", f"access_token={token_for(self.alice)}".encode()),
            ],
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_same_origin_is_accepted(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.room}/",
            headers=[
                (b"origin", b"https://localhost:1337"),
                (b"cookie", f"access_token={token_for(self.alice)}".encode()),
            ],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()


class ChatTwoFactorTests(ChatTestCase):
    def setUp(self):
        super().setUp()
        Profile.objects.filter(user=self.alice).update(
            is_tfa_enabled=True, tfa_secret=pyotp.random_base32()
        )

    async def test_unverified_2fa_token_is_rejected(self):
        alice = await self.connect(token=token_for(self.alice, is_tfa_verified=False))
        await self.assert_closed_with(alice, 4001)

    async def test_verified_2fa_token_is_accepted(self):
        alice = await self.connect(token=token_for(self.alice, is_tfa_verified=True))
        self.assertTrue(await alice.receive_nothing(timeout=0.3))
        await alice.disconnect()


class ChatHistoryViewTests(ChatTestCase):
    def setUp(self):
        super().setUp()
        Message.objects.create(author=self.alice, content="hello", conversation=self.room)

    def get_history(self, user, room=None):
        self.client.cookies["access_token"] = token_for(user)
        return self.client.get(f"/api/chat/messages/{room or self.room}/")

    def test_member_can_read_history(self):
        response = self.get_history(self.bob)
        self.assertEqual(response.status_code, 200)
        messages = response.json()["data"]["messages"]
        self.assertEqual([m["content"] for m in messages], ["hello"])

    def test_non_member_cannot_read_history(self):
        response = self.get_history(self.eve)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("hello", response.content.decode())

    def test_blocked_member_cannot_read_history(self):
        Friendship.objects.filter(pk=self.friendship.pk).update(status=Friendship.BLOCKED)
        response = self.get_history(self.bob)
        self.assertEqual(response.status_code, 404)

    def test_malformed_conversation_id(self):
        response = self.get_history(self.alice, room="nope")
        self.assertEqual(response.status_code, 404)
