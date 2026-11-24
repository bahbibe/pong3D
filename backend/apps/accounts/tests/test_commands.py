from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from .helpers import AuthTestCase


class ResetPresenceCommandTests(TestCase):
    def test_clears_online_counts(self):
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command

        client = mock.Mock()
        with mock.patch("redis.Redis.from_url", return_value=client):
            call_command("reset_presence", stdout=StringIO())
        client.delete.assert_called_once_with("online_counts")

    def test_redis_down_does_not_fail_startup(self):
        from io import StringIO
        from unittest import mock
        import redis
        from django.core.management import call_command

        client = mock.Mock()
        client.delete.side_effect = redis.ConnectionError("down")
        err = StringIO()
        with mock.patch("redis.Redis.from_url", return_value=client):
            call_command("reset_presence", stdout=StringIO(), stderr=err)
        self.assertIn("redis unavailable", err.getvalue())


class CreateDemoUsersCommandTests(AuthTestCase):
    def run_command(self, **kwargs):
        from io import StringIO
        from django.core.management import call_command

        call_command("create_demo_users", stdout=StringIO(), **kwargs)

    def test_refuses_on_a_public_site(self):
        from django.core.management.base import CommandError
        from django.test import override_settings

        hosts = ["example.org", "localhost"]
        with override_settings(ALLOWED_HOSTS=hosts), self.assertRaises(CommandError):
            self.run_command()
        self.assertFalse(User.objects.filter(username__startswith="demo").exists())

    def test_creates_set_up_users_once(self):
        from django.test import override_settings

        with override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "backend"]):
            self.run_command(count=2)
            self.run_command(count=2)  # second run: nothing new
        users = User.objects.filter(username__startswith="demo").order_by("username")
        self.assertEqual([u.username for u in users], ["demo1", "demo2"])
        self.assertTrue(all(u.profile.is_setup for u in users))
        self.login("demo1", password="Pong-Demo-Pass-42")
