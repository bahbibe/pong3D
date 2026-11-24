"""What every API endpoint answers for each authentication case.

Walks the URL configuration, so a new endpoint is covered without being
listed here. Only the public endpoints and the two that accept a token
issued before the 2FA step are named.
"""

import re
from datetime import timedelta

from django.test import TestCase, TransactionTestCase
from django.urls import URLPattern, URLResolver, get_resolver
from django.utils import timezone

from apps.accounts.auth_utils import generate_token, revoke_tokens

from .helpers import make_user

PUBLIC = {
    "/api/auth/register/",
    "/api/auth/login/",
    "/api/auth/intra/",
    "/api/auth/intra/callback/",
}
# Reachable with a token issued after the password step only.
UNVERIFIED_TFA_OK = {"/api/auth/logout/", "/api/auth/twofa/verify/"}

NO_TOKEN = (401, "No access token found")
INVALID = (401, "Invalid access token")
NO_USER = (404, "User does not exist")
TFA_PENDING_MESSAGE = "Two factor authentication is enabled"


def api_endpoints():
    """(path, method) of every view under /api/, URL arguments filled in."""
    found = []

    def walk(patterns, prefix):
        for p in patterns:
            route = prefix + str(p.pattern)
            if isinstance(p, URLResolver):
                walk(p.url_patterns, route)
            elif isinstance(p, URLPattern) and route.startswith("api/"):
                path = re.sub(r"\(\?P<[^>]+>[^)]*\)", "1", route)  # re_path groups
                path = "/" + re.sub(r"<[^>]+>", "1", path).replace("^", "").replace("$", "")
                cls = getattr(p.callback, "cls", None)
                for method in ("get", "post", "put", "patch", "delete"):
                    if cls is not None and hasattr(cls, method):
                        found.append((path, method))

    walk(get_resolver().url_patterns, "")
    return found


class AuthContractTests(TestCase):
    def setUp(self):
        self.user = make_user("contract")
        self.tfa_user = make_user("contract2fa", is_tfa_enabled=True, tfa_secret="JBSWY3DPEHPK3PXP")
        self.endpoints = api_endpoints()

    def token(self, user_id, verified=True, ver=0):
        return generate_token(
            {
                "id": user_id,
                "is_tfa_verified": verified,
                "ver": ver,
                "exp": timezone.now() + timedelta(hours=1),
            }
        )

    def call(self, path, method, token=None):
        self.client.cookies.clear()
        if token is not None:
            self.client.cookies["access_token"] = token
        return getattr(self.client, method)(path, content_type="application/json")

    def answer(self, response):
        body = response.json()
        return response.status_code, body.get("message")

    def protected(self):
        return [(p, m) for p, m in self.endpoints if p not in PUBLIC]

    def test_walk_finds_the_endpoints(self):
        paths = {p for p, _ in self.endpoints}
        self.assertIn("/api/auth/me/", paths)
        self.assertIn("/api/game/stats/", paths)
        self.assertGreater(len(self.protected()), 30)

    def test_no_cookie(self):
        for path, method in self.protected():
            with self.subTest(path=path, method=method):
                self.assertEqual(self.answer(self.call(path, method)), NO_TOKEN)

    def test_garbage_token(self):
        for path, method in self.protected():
            with self.subTest(path=path, method=method):
                self.assertEqual(self.answer(self.call(path, method, "not-a-jwt")), INVALID)

    def test_expired_token(self):
        expired = generate_token(
            {
                "id": self.user.id,
                "is_tfa_verified": True,
                "exp": timezone.now() - timedelta(minutes=1),
            }
        )
        for path, method in self.protected():
            with self.subTest(path=path, method=method):
                self.assertEqual(self.answer(self.call(path, method, expired)), INVALID)

    def test_revoked_token(self):
        old = self.token(self.user.id)
        revoke_tokens(self.user)
        for path, method in self.protected():
            with self.subTest(path=path, method=method):
                self.assertEqual(self.answer(self.call(path, method, old)), INVALID)

    def test_deleted_user(self):
        for path, method in self.protected():
            with self.subTest(path=path, method=method):
                self.assertEqual(self.answer(self.call(path, method, self.token(999999))), NO_USER)

    def test_tfa_pending(self):
        pending = self.token(self.tfa_user.id, verified=False)
        # Logout revokes the token: call it last.
        for path, method in sorted(self.protected(), key=lambda e: e[0] == "/api/auth/logout/"):
            with self.subTest(path=path, method=method):
                response = self.call(path, method, pending)
                body = response.json()
                if path in UNVERIFIED_TFA_OK:
                    self.assertNotEqual(body.get("message"), TFA_PENDING_MESSAGE)
                    continue
                self.assertEqual(response.status_code, 200, body)
                self.assertEqual(body["message"], TFA_PENDING_MESSAGE)
                self.assertIs(body["data"]["is_tfa_verified"], False)
                self.assertEqual(body["data"]["user"]["username"], "contract2fa")

    def test_valid_token_passes(self):
        good = self.token(self.user.id)
        # Not NO_USER: views also answer it for a missing target user.
        failures = {NO_TOKEN, INVALID}
        self.assertEqual(self.call("/api/auth/me/", "get", good).status_code, 200)
        for path, method in self.protected():
            if path == "/api/auth/logout/":
                continue  # revokes the token for the next calls
            with self.subTest(path=path, method=method):
                self.assertNotIn(self.answer(self.call(path, method, good)), failures)

    def test_public_endpoints_ignore_a_bad_cookie(self):
        for path, method in self.endpoints:
            if path not in PUBLIC:
                continue
            with self.subTest(path=path, method=method):
                response = self.call(path, method, "not-a-jwt")
                self.assertNotIn(response.status_code, (401, 403), response.content)


class ErrorShapeTests(TestCase):
    """Errors raised by DRF itself use the same JSON shape as the views."""

    def setUp(self):
        self.user = make_user("shape")
        self.client.cookies["access_token"] = generate_token(
            {
                "id": self.user.id,
                "is_tfa_verified": True,
                "ver": 0,
                "exp": timezone.now() + timedelta(hours=1),
            }
        )

    def test_401_says_how_to_authenticate(self):
        self.client.cookies.clear()
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)
        self.assertIn("WWW-Authenticate", response)

    def test_wrong_method(self):
        response = self.client.get("/api/friends/send/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            response.json(), {"success": False, "message": 'Method "GET" not allowed.'}
        )
        self.assertIn("POST", response["Allow"])

    def test_malformed_json(self):
        response = self.client.post(
            "/api/friends/send/", data="{not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIs(body["success"], False)
        self.assertIn("JSON parse error", body["message"])

    def test_unexpected_error_in_a_public_view_is_json(self):
        from unittest import mock

        with (
            mock.patch("apps.accounts.services.rate_limit.check", side_effect=RuntimeError("boom")),
            self.assertLogs("core.exceptions", level="ERROR"),
        ):
            response = self.client.post(
                "/api/auth/login/",
                data={"username": "x", "password": "y"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["success"], False)
        self.assertNotIn("boom", response.content.decode())

    def test_user_without_profile_is_refused(self):
        # Every user gets a Profile from a signal; if one is missing anyway,
        # the token is refused instead of failing with a 500.
        from apps.accounts.models import Profile

        Profile.objects.filter(user=self.user).delete()
        response = self.client.get("/api/auth/me/")
        self.assertEqual(
            (response.status_code, response.json()["message"]), (401, "Invalid access token")
        )


class WebsocketSameRulesTests(TransactionTestCase):
    def test_deleted_user_and_missing_profile_get_no_user(self):
        from asgiref.sync import async_to_sync
        from apps.accounts.models import Profile
        from apps.accounts.ws_auth import user_from_cookie

        def token(user_id):
            return generate_token(
                {
                    "id": user_id,
                    "is_tfa_verified": True,
                    "ver": 0,
                    "exp": timezone.now() + timedelta(hours=1),
                }
            )

        user = make_user("wsrules")
        self.assertEqual(async_to_sync(user_from_cookie)(token(user.id)), user)
        self.assertIsNone(async_to_sync(user_from_cookie)(token(999999)))
        self.assertIsNone(async_to_sync(user_from_cookie)("not-a-jwt"))
        Profile.objects.filter(user=user).delete()
        self.assertIsNone(async_to_sync(user_from_cookie)(token(user.id)))
