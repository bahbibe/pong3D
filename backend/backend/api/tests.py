import json

import pyotp
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase

from .models import Profile

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
        return self.client.post(
            url, data=json.dumps(data or {}), content_type="application/json"
        )

    def me(self):
        return self.client.get("/api/auth/me/").json()


class TwoFactorTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.secret = pyotp.random_base32()
        self.user = make_user(
            "alice", is_tfa_enabled=True, tfa_secret=self.secret
        )

    def code(self):
        return pyotp.TOTP(self.secret).now()

    def assert_blocked_by_2fa(self, response):
        body = response.json()
        self.assertFalse(body["data"].get("is_tfa_verified", True), body)

    def test_unverified_token_cannot_disable_2fa(self):
        self.login("alice")
        response = self.post_json("/api/auth/twofa/disable/", {"code": self.code()})
        self.assert_blocked_by_2fa(response)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_tfa_enabled)
        self.assertEqual(self.user.profile.tfa_secret, self.secret)

    def test_unverified_token_cannot_setup_profile(self):
        self.login("alice")
        response = self.client.post("/api/auth/setup/", {"username": "mallory"})
        self.assert_blocked_by_2fa(response)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "alice")

    def test_unverified_token_cannot_use_other_endpoints(self):
        self.login("alice")
        self.assert_blocked_by_2fa(self.client.get("/api/friends/"))
        self.assertFalse(self.me()["data"]["is_tfa_verified"])

    def test_unverified_token_can_verify_and_then_use_api(self):
        self.login("alice")
        wrong = self.post_json("/api/auth/twofa/verify/", {"code": "000000"})
        self.assertEqual(wrong.status_code, 400)
        response = self.post_json("/api/auth/twofa/verify/", {"code": self.code()})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn("is_tfa_verified", self.me()["data"])

    def test_unverified_token_can_logout(self):
        self.login("alice")
        response = self.post_json("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["access_token"].value, "")

    def verified_login(self):
        self.login("alice")
        self.post_json("/api/auth/twofa/verify/", {"code": self.code()})

    def test_disable_requires_a_code(self):
        self.verified_login()
        response = self.post_json("/api/auth/twofa/disable/")
        self.assertEqual(response.status_code, 400)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_tfa_enabled)

    def test_disable_rejects_wrong_code(self):
        self.verified_login()
        response = self.post_json("/api/auth/twofa/disable/", {"code": "000000"})
        self.assertEqual(response.status_code, 400)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_tfa_enabled)

    def test_disable_with_valid_code(self):
        self.verified_login()
        response = self.post_json("/api/auth/twofa/disable/", {"code": self.code()})
        self.assertEqual(response.status_code, 200, response.content)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.is_tfa_enabled)
        self.assertIsNone(self.user.profile.tfa_secret)

    def test_verify_with_missing_secret_is_a_client_error(self):
        Profile.objects.filter(user=self.user).update(tfa_secret=None)
        self.login("alice")
        response = self.post_json("/api/auth/twofa/verify/", {"code": "123456"})
        self.assertEqual(response.status_code, 400)


class EnableTwoFactorTests(AuthTestCase):
    def test_confirm_keeps_the_session_usable(self):
        user = make_user("bob")
        self.login("bob")
        response = self.post_json("/api/auth/twofa/enable/")
        self.assertEqual(response.status_code, 200)
        user.profile.refresh_from_db()
        code = pyotp.TOTP(user.profile.tfa_secret).now()

        response = self.post_json("/api/auth/twofa/confirm/", {"code": code})
        self.assertEqual(response.status_code, 200, response.content)
        user.profile.refresh_from_db()
        self.assertTrue(user.profile.is_tfa_enabled)
        # Session token was re-issued as verified, so the API still works.
        self.assertNotIn("is_tfa_verified", self.me()["data"])


class RegisterValidationTests(AuthTestCase):
    def register(self, **overrides):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": PASSWORD,
            "confirm_password": PASSWORD,
            "first_name": "New",
            "last_name": "User",
        }
        data.update(overrides)
        return self.post_json("/api/auth/register/", data)

    def test_valid_registration(self):
        response = self.register()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_rejects_html_in_username(self):
        response = self.register(username="<img src=x onerror=alert(1)>")
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json()["errors"])
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_rejects_too_long_username(self):
        response = self.register(username="a" * 151)
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json()["errors"])

    def test_rejects_weak_password(self):
        response = self.register(password="12345678", confirm_password="12345678")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json()["errors"])

    def test_rejects_password_mismatch(self):
        response = self.register(confirm_password=PASSWORD + "x")
        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json()["errors"])


class SettingsUpdateTests(AuthTestCase):
    NEW_PASSWORD = "Another-Strong-Pass-7"

    def setUp(self):
        super().setUp()
        self.user = make_user("carol")
        self.login("carol")

    def put(self, data):
        # Same encoding as the browser form (FormData -> multipart).
        from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT

        return self.client.put(
            "/api/auth/settings/update/",
            data=encode_multipart(BOUNDARY, data),
            content_type=MULTIPART_CONTENT,
        )

    def form(self, **overrides):
        data = {
            "username": "carol",
            "email": "carol@example.com",
            "password": "",
            "confirm_password": "",
            "current_password": "",
        }
        data.update(overrides)
        return data

    def assert_password(self, password):
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(password))

    def test_password_change_needs_current_password(self):
        response = self.put(
            self.form(password=self.NEW_PASSWORD, confirm_password=self.NEW_PASSWORD)
        )
        self.assertEqual(response.status_code, 400)
        self.assert_password(PASSWORD)

    def test_password_change_rejects_wrong_current_password(self):
        response = self.put(
            self.form(
                password=self.NEW_PASSWORD,
                confirm_password=self.NEW_PASSWORD,
                current_password="wrong-password",
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assert_password(PASSWORD)

    def test_password_change_with_current_password(self):
        response = self.put(
            self.form(
                password=self.NEW_PASSWORD,
                confirm_password=self.NEW_PASSWORD,
                current_password=PASSWORD,
            )
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assert_password(self.NEW_PASSWORD)

    def test_password_change_rejects_weak_password(self):
        response = self.put(
            self.form(password="1234", confirm_password="1234", current_password=PASSWORD)
        )
        self.assertEqual(response.status_code, 400)
        self.assert_password(PASSWORD)

    def test_password_change_rejects_mismatch(self):
        response = self.put(
            self.form(
                password=self.NEW_PASSWORD,
                confirm_password="something-else",
                current_password=PASSWORD,
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assert_password(PASSWORD)

    def test_email_change_needs_current_password(self):
        response = self.put(self.form(email="evil@example.com"))
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "carol@example.com")

    def test_email_change_with_current_password(self):
        response = self.put(self.form(email="carol2@example.com", current_password=PASSWORD))
        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "carol2@example.com")

    def test_username_change_does_not_need_current_password(self):
        response = self.put(self.form(username="carol_new"))
        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "carol_new")
        self.assert_password(PASSWORD)

    def test_rejects_html_username(self):
        response = self.put(self.form(username="<script>x</script>"))
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "carol")

    def test_intra_user_cannot_set_password(self):
        Profile.objects.filter(user=self.user).update(auth_method=Profile.INTRA)
        response = self.put(
            self.form(
                password=self.NEW_PASSWORD,
                confirm_password=self.NEW_PASSWORD,
                current_password=PASSWORD,
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assert_password(PASSWORD)


class CrossOriginTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        make_user("dave")

    def test_auth_cookie_flags(self):
        response = self.login("dave")
        cookie = response.cookies["access_token"]
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_foreign_origin_gets_no_cors_headers(self):
        self.login("dave")
        response = self.client.get("/api/auth/me/", HTTP_ORIGIN="https://evil.example")
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)
        self.assertNotIn("Access-Control-Allow-Credentials", response.headers)

    def test_unknown_host_is_rejected(self):
        response = self.client.get("/api/auth/me/", HTTP_HOST="evil.example")
        self.assertEqual(response.status_code, 400)


class LoginRateLimitTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        make_user("erin")

    def attempt(self, password, username="erin", ip="203.0.113.7"):
        return self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR=ip,
        )

    def test_account_is_locked_after_repeated_failures(self):
        for _ in range(10):
            self.assertEqual(self.attempt("wrong").status_code, 404)
        # Locked: even the right password is refused for now.
        self.assertEqual(self.attempt(PASSWORD).status_code, 429)

    def test_lock_applies_across_ips(self):
        for i in range(10):
            self.attempt("wrong", ip=f"198.51.100.{i}")
        self.assertEqual(self.attempt(PASSWORD, ip="192.0.2.1").status_code, 429)

    def test_success_resets_the_account_counter(self):
        for _ in range(9):
            self.attempt("wrong")
        self.assertEqual(self.attempt(PASSWORD).status_code, 200)
        self.assertEqual(self.attempt("wrong").status_code, 404)
        self.assertEqual(self.attempt(PASSWORD).status_code, 200)

    def test_ip_is_locked_after_many_failures_on_many_accounts(self):
        for i in range(30):
            self.attempt("wrong", username=f"nobody{i}")
        self.assertEqual(self.attempt(PASSWORD).status_code, 429)
        # Another client is not affected.
        self.assertEqual(self.attempt(PASSWORD, ip="192.0.2.50").status_code, 200)

    def test_spoofed_forwarded_for_does_not_bypass_ip_limit(self):
        # nginx appends the real client last; a client-set first entry is ignored.
        for i in range(30):
            self.attempt("wrong", username=f"nobody{i}", ip=f"10.0.0.{i}, 203.0.113.7")
        self.assertEqual(self.attempt(PASSWORD).status_code, 429)


class TwoFactorRateLimitTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.secret = pyotp.random_base32()
        self.user = make_user("frank", is_tfa_enabled=True, tfa_secret=self.secret)

    def test_verify_is_locked_after_five_wrong_codes(self):
        self.login("frank")
        for _ in range(5):
            response = self.post_json("/api/auth/twofa/verify/", {"code": "000000"})
            self.assertEqual(response.status_code, 400)
        good = pyotp.TOTP(self.secret).now()
        response = self.post_json("/api/auth/twofa/verify/", {"code": good})
        self.assertEqual(response.status_code, 429)

    def test_valid_code_resets_counter(self):
        self.login("frank")
        for _ in range(4):
            self.post_json("/api/auth/twofa/verify/", {"code": "000000"})
        good = pyotp.TOTP(self.secret).now()
        self.assertEqual(
            self.post_json("/api/auth/twofa/verify/", {"code": good}).status_code, 200
        )
        self.assertEqual(
            self.post_json("/api/auth/twofa/disable/", {"code": "000000"}).status_code, 400
        )


class IntraUserTests(TestCase):
    def intra(self, intra_id, login, **extra):
        from .auth_views import find_or_create_intra_user, parse_intra_user

        payload = {
            "id": intra_id,
            "login": login,
            "email": f"{login}@student.42.fr",
            "first_name": "In",
            "last_name": "Tra",
            "image": {"link": f"https://cdn.intra.42.fr/users/{login}.jpg"},
        }
        payload.update(extra)
        return find_or_create_intra_user(parse_intra_user(payload))

    def test_same_intra_id_returns_same_account(self):
        first = self.intra(1001, "victim")
        self.assertEqual(self.intra(1001, "victim").id, first.id)

    def test_renamed_account_cannot_capture_another_login(self):
        # Regression: lookup fell back to username, so an intra user who
        # renamed themselves to "victim" got victim's first intra login.
        attacker = self.intra(2002, "attacker")
        attacker.username = "victim"
        attacker.save()

        victim = self.intra(3003, "victim")
        self.assertNotEqual(victim.id, attacker.id)
        self.assertTrue(victim.username.startswith("victim_"))
        self.assertEqual(victim.profile.intra_id, 3003)

    def test_local_account_with_same_name_is_not_used(self):
        local = make_user("bob42")
        user = self.intra(4004, "bob42")
        self.assertNotEqual(user.id, local.id)
        self.assertEqual(user.profile.auth_method, Profile.INTRA)

    def test_legacy_intra_account_without_id_is_claimed_once(self):
        legacy = make_user("oldtimer", auth_method=Profile.INTRA)
        self.assertEqual(self.intra(5005, "oldtimer").id, legacy.id)
        legacy.profile.refresh_from_db()
        self.assertEqual(legacy.profile.intra_id, 5005)
        # A different intra id with the same login does not get it.
        self.assertNotEqual(self.intra(6006, "oldtimer").id, legacy.id)

    def test_missing_picture_uses_default_avatar(self):
        user = self.intra(7007, "nopic", image={"link": None})
        self.assertEqual(str(user.profile.avatar), "avatars/profile_default.jpg")
        self.assertFalse(user.has_usable_password())

    def test_bad_payload_is_rejected(self):
        from .auth_views import parse_intra_user

        self.assertIsNone(parse_intra_user({"login": "x"}))
        self.assertIsNone(parse_intra_user({"id": "1", "login": "x"}))
        self.assertIsNone(parse_intra_user(None))


class ProfileCreationTests(TestCase):
    def test_every_new_user_gets_a_profile(self):
        user = User.objects.create_superuser("root", "root@example.com", "x-Strong-Pass-1")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertFalse(user.profile.is_setup)

    def test_backfill_migration_creates_missing_profiles(self):
        import importlib

        from django.apps import apps

        user = User.objects.create_user("orphan", password="x-Strong-Pass-1")
        Profile.objects.filter(user=user).delete()
        migration = importlib.import_module("api.migrations.0015_backfill_missing_profiles")
        migration.create_missing_profiles(apps, None)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({
                "username": "gina", "email": "gina@example.com",
                "password": PASSWORD, "confirm_password": PASSWORD,
                "first_name": "G", "last_name": "H",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Profile.objects.filter(user__username="gina").count(), 1)


class PrivacyAndRobustnessTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.henry = make_user("henry")
        self.other = make_user("ivy")
        self.login("henry")

    def test_search_hides_other_users_email(self):
        users = self.client.get("/api/auth/users/?q=ivy").json()["data"]
        self.assertEqual([u["username"] for u in users], ["ivy"])
        self.assertNotIn("email", users[0])

    def test_search_does_not_match_email(self):
        users = self.client.get("/api/auth/users/?q=example.com").json()["data"]
        self.assertEqual(users, [])

    def test_search_excludes_blocked_users(self):
        from friends.models import Friendship

        Friendship.objects.create(
            source_user=self.other, target_user=self.henry,
            status=Friendship.BLOCKED, blocked_by=self.other,
        )
        users = self.client.get("/api/auth/users/?q=ivy").json()["data"]
        self.assertEqual(users, [])

    def test_profile_hides_email_and_handles_bad_uuid(self):
        data = self.client.get(f"/api/auth/profile/{self.other.profile.uuid}/").json()["data"]
        self.assertNotIn("email", data["user"])
        self.assertEqual(self.client.get("/api/auth/profile/not-a-uuid/").status_code, 404)
        self.assertEqual(self.client.get("/api/auth/user/abc/").status_code, 404)

    def test_own_user_still_has_email(self):
        self.assertEqual(self.me()["data"]["user"]["email"], "henry@example.com")

    def test_notification_without_sender(self):
        from .models import Notification

        Notification.objects.create(user=self.henry, type="system", message="hello")
        notifications = self.me()["data"]["notifications"]
        self.assertIsNone(notifications[0]["sender"])

    def test_unexpected_error_does_not_leak_details(self):
        from unittest import mock

        with mock.patch("api.views.blocked_user_ids", side_effect=RuntimeError("secret detail")):
            with self.assertLogs("api.auth_utils", level="ERROR"):
                response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret detail", response.content.decode())


class IntraStateTests(AuthTestCase):
    def test_login_url_carries_state_and_sets_cookie(self):
        from urllib.parse import parse_qs, urlparse

        response = self.client.get("/api/auth/intra/")
        url = response.json()["data"]["url"]
        state = parse_qs(urlparse(url).query)["state"][0]
        self.assertGreaterEqual(len(state), 32)
        self.assertIn("intra_oauth_state", response.cookies)

    def test_callback_without_matching_state_is_refused(self):
        from unittest import mock

        with mock.patch("api.auth_views.requests.post") as post:
            response = self.client.get("/api/auth/intra/callback/?code=abc&state=forged")
            self.assertEqual(response.status_code, 400)
            post.assert_not_called()

        self.client.get("/api/auth/intra/")  # sets the cookie for another state
        with mock.patch("api.auth_views.requests.post") as post:
            response = self.client.get("/api/auth/intra/callback/?code=abc&state=forged")
            self.assertEqual(response.status_code, 400)
            post.assert_not_called()

    def test_callback_with_matching_state_logs_in(self):
        from unittest import mock
        from urllib.parse import parse_qs, urlparse

        url = self.client.get("/api/auth/intra/").json()["data"]["url"]
        state = parse_qs(urlparse(url).query)["state"][0]
        token = mock.Mock(status_code=200, json=lambda: {"access_token": "t"})
        me = mock.Mock(status_code=200, json=lambda: {
            "id": 4242, "login": "jdoe", "email": "jdoe@student.42.fr",
            "first_name": "J", "last_name": "D", "image": {"link": None},
        })
        with mock.patch("api.auth_views.requests.post", return_value=token), \
                mock.patch("api.auth_views.requests.get", return_value=me):
            response = self.client.get(f"/api/auth/intra/callback/?code=abc&state={state}")
        self.assertEqual(response.status_code, 302)
        self.assertIn("access_token", response.cookies)
        self.assertTrue(Profile.objects.filter(intra_id=4242).exists())

    def test_intra_api_down_returns_502(self):
        from unittest import mock
        from urllib.parse import parse_qs, urlparse

        import requests as requests_lib

        url = self.client.get("/api/auth/intra/").json()["data"]["url"]
        state = parse_qs(urlparse(url).query)["state"][0]
        with mock.patch("api.auth_views.requests.post", side_effect=requests_lib.Timeout()):
            response = self.client.get(f"/api/auth/intra/callback/?code=abc&state={state}")
        self.assertEqual(response.status_code, 502)


class UniqueIntraIdTests(TestCase):
    def test_duplicate_intra_id_is_rejected_by_the_database(self):
        from django.db import IntegrityError, transaction

        make_user("one", auth_method=Profile.INTRA, intra_id=9001)
        two = make_user("two", auth_method=Profile.INTRA)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.filter(user=two).update(intra_id=9001)


class UniqueIntraIdMigrationTests(TransactionTestCase):
    def test_migration_clears_duplicates_before_adding_the_index(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        before = [("api", "0015_backfill_missing_profiles")]
        after = [("api", "0016_unique_intra_id")]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        old_apps = executor.loader.project_state(before).apps
        OldUser = old_apps.get_model("auth", "User")
        OldProfile = old_apps.get_model("api", "Profile")
        ids = []
        for name in ("dup_a", "dup_b"):
            user = OldUser.objects.create(username=name)
            ids.append(OldProfile.objects.create(user=user, intra_id=55, auth_method="intra").id)

        executor = MigrationExecutor(connection)
        executor.migrate(after)

        self.assertEqual(Profile.objects.get(id=ids[0]).intra_id, 55)
        self.assertIsNone(Profile.objects.get(id=ids[1]).intra_id)
