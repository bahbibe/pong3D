import json
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import Profile


PASSWORD = "Correct-Horse-42"


def make_user(username, password=PASSWORD, **profile_fields):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
        first_name="Test",
        last_name="User",
    )
    # Profile comes from the post_save signal.
    Profile.objects.filter(user=user).update(is_setup=True, **profile_fields)
    user.refresh_from_db()
    return user


class AuthTestCase(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()  # rate-limit counters

    def login(self, username, password=PASSWORD):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response

    def post_json(self, url, data=None):
        return self.client.post(url, data=json.dumps(data or {}), content_type="application/json")

    def me(self):
        return self.client.get("/api/auth/me/").json()
