import json
from datetime import datetime, timedelta

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.accounts.auth_utils import generate_token
from apps.accounts.models import Profile
from apps.accounts.tests.helpers import AuthTestCase
from apps.accounts.tests.helpers import make_user as make_set_up_user
from config.asgi import application

from .models import Notification
from .services import notify


def make_user(username):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    Profile.objects.filter(user=user).update(is_setup=True)
    return user


def token_for(user):
    return generate_token(
        {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
    )


async def connect(user=None):
    headers = [(b"origin", b"http://localhost")]
    if user is not None:
        headers.append((b"cookie", f"access_token={token_for(user)}".encode()))
    communicator = WebsocketCommunicator(application, "/ws/notifications/", headers=headers)
    connected, _ = await communicator.connect()
    assert connected
    return communicator


class AnonymousSocketTests(TransactionTestCase):
    async def test_anonymous_notification_socket_is_rejected(self):
        anon = await connect()
        output = await anon.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)


class NotificationSocketTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

    async def test_pushed_notification_carries_its_uuid(self):
        from channels.db import database_sync_to_async
        from django.test import Client

        communicator = WebsocketCommunicator(
            application,
            "/ws/notifications/",
            headers=[
                (b"origin", b"http://localhost"),
                (b"cookie", f"access_token={token_for(self.alice)}".encode()),
            ],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        def bob_sends_request():
            client = Client()
            client.cookies["access_token"] = token_for(self.bob)
            return client.post(
                "/api/friends/send/",
                data=json.dumps({"target_user": self.alice.id}),
                content_type="application/json",
            ).status_code

        self.assertEqual(await database_sync_to_async(bob_sends_request)(), 200)
        message = json.loads(await communicator.receive_from(timeout=2))
        stored = await database_sync_to_async(Notification.objects.get)(user=self.alice)
        self.assertEqual(message["uuid"], str(stored.uuid))
        await communicator.disconnect()


class NotifyTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

    def test_stores_and_links_both_users(self):
        notification = notify(self.alice, self.bob, "friend_request", "hi", game_id=7)
        self.assertEqual(notification.game_id, 7)
        self.assertEqual(list(self.alice.notifications.all()), [notification])
        self.assertEqual(list(self.bob.sent_notifications.all()), [notification])

    def test_no_user_creates_nothing(self):
        # A tournament game can lack its second player.
        with self.assertLogs("apps.notifications.services", level="WARNING"):
            self.assertIsNone(notify(None, self.bob, "game_invite", "x"))
        self.assertEqual(Notification.objects.count(), 0)

    async def test_system_notification_has_no_sender(self):
        from channels.db import database_sync_to_async

        communicator = await connect(self.alice)
        await database_sync_to_async(notify)(self.alice, None, "system", "maintenance")
        message = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(
            (message["ctx"], message["sender"], message["game_id"]), ("system", None, None)
        )
        await communicator.disconnect()


class TableTests(TestCase):
    def test_table_kept_from_the_api_app(self):
        # An older image reads the same table (rollback).
        self.assertEqual(Notification._meta.db_table, "api_notification")

    def test_content_type_moved(self):
        from django.contrib.contenttypes.models import ContentType

        self.assertEqual(ContentType.objects.get_for_model(Notification).app_label, "notifications")
        self.assertFalse(ContentType.objects.filter(app_label="api", model="notification").exists())


class MarkNotificationReadTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_set_up_user("nora")
        self.other = make_set_up_user("otto")
        self.mine = Notification.objects.create(user=self.user, message="m", type="t")
        self.theirs = Notification.objects.create(user=self.other, message="m", type="t")
        self.login("nora")

    def mark(self, value):
        return self.client.post(f"/api/auth/notifications/mark_as_read/{value}/")

    def test_marks_own_notification(self):
        self.assertEqual(self.mark(self.mine.uuid).status_code, 200)
        self.mine.refresh_from_db()
        self.assertTrue(self.mine.is_read)

    def test_other_users_notification_is_not_found(self):
        self.assertEqual(self.mark(self.theirs.uuid).status_code, 404)
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.is_read)

    def test_malformed_uuid_is_not_found(self):
        self.assertEqual(self.mark("not-a-uuid").status_code, 404)
