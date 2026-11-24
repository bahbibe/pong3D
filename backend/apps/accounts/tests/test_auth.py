import json
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.accounts.models import Profile
from .helpers import PASSWORD, make_user, AuthTestCase


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


class IntraUserTests(TestCase):
    def intra(self, intra_id, login, **extra):
        from apps.accounts.intra import find_or_create_intra_user, parse_intra_user

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
        from apps.accounts.intra import parse_intra_user

        self.assertIsNone(parse_intra_user({"login": "x"}))
        self.assertIsNone(parse_intra_user({"id": "1", "login": "x"}))
        self.assertIsNone(parse_intra_user(None))


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

        with mock.patch("apps.accounts.intra.requests.post") as post:
            response = self.client.get("/api/auth/intra/callback/?code=abc&state=forged")
            self.assertEqual(response.status_code, 400)
            post.assert_not_called()

        self.client.get("/api/auth/intra/")  # sets the cookie for another state
        with mock.patch("apps.accounts.intra.requests.post") as post:
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
        with mock.patch("apps.accounts.intra.requests.post", return_value=token), \
                mock.patch("apps.accounts.intra.requests.get", return_value=me):
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
        with mock.patch("apps.accounts.intra.requests.post", side_effect=requests_lib.Timeout()):
            response = self.client.get(f"/api/auth/intra/callback/?code=abc&state={state}")
        self.assertEqual(response.status_code, 502)


class UniqueIntraIdTests(TestCase):
    def test_duplicate_intra_id_is_rejected_by_the_database(self):
        from django.db import IntegrityError, transaction

        make_user("one", auth_method=Profile.INTRA, intra_id=9001)
        two = make_user("two", auth_method=Profile.INTRA)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.filter(user=two).update(intra_id=9001)


class TokenRevocationTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("dave")

    def test_token_copied_before_logout_is_refused(self):
        self.login("dave")
        stolen = self.client.cookies["access_token"].value
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 200)

        self.client.cookies["access_token"] = stolen
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_login_after_logout_works(self):
        self.login("dave")
        self.client.post("/api/auth/logout/")
        self.login("dave")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_password_change_ends_other_sessions_only(self):
        from django.test import Client
        from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT

        other = Client()
        other.post(
            "/api/auth/login/",
            data=json.dumps({"username": "dave", "password": PASSWORD}),
            content_type="application/json",
        )
        self.login("dave")
        response = self.client.put(
            "/api/auth/settings/update/",
            data=encode_multipart(BOUNDARY, {
                "username": "dave",
                "password": "Another-Strong-Pass-7",
                "confirm_password": "Another-Strong-Pass-7",
                "current_password": PASSWORD,
            }),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 401)

    def test_old_tokens_without_version_still_work_until_revoked(self):
        # Tokens issued before this change have no "ver" claim.
        from datetime import timedelta
        from apps.accounts.auth_utils import generate_token, revoke_tokens

        token = generate_token(
            {"id": self.user.id, "is_tfa_verified": True,
             "exp": timezone.now() + timedelta(hours=1)}
        )
        self.client.cookies["access_token"] = token
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        revoke_tokens(self.user)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)


class UniqueEmailTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user("alice")  # alice@example.com

    def register(self, username, email):
        return self.post_json("/api/auth/register/", {
            "username": username, "email": email, "password": PASSWORD,
            "confirm_password": PASSWORD, "first_name": "A", "last_name": "B",
        })

    def intra(self, intra_id, login, email):
        from apps.accounts.intra import find_or_create_intra_user, parse_intra_user

        return find_or_create_intra_user(parse_intra_user(
            {"id": intra_id, "login": login, "email": email,
             "first_name": "In", "last_name": "Tra", "image": {}}
        ))

    def test_database_refuses_same_email_in_another_case(self):
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="other", email="ALICE@example.com")

    def test_many_accounts_may_have_no_email(self):
        User.objects.create_user(username="n1", email="")
        User.objects.create_user(username="n2", email="")

    def test_register_with_taken_email_in_another_case_is_refused(self):
        response = self.register("alice2", "Alice@Example.com")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="alice2").exists())

    def test_login_by_email_ignores_case(self):
        response = self.post_json(
            "/api/auth/login/", {"email": "ALICE@example.com", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_intra_login_with_taken_email_gets_separate_account_without_email(self):
        user = self.intra(7007, "alice", "alice@EXAMPLE.com")
        self.assertNotEqual(user.id, self.alice.id)
        self.assertEqual(user.email, "")
        self.assertEqual(user.profile.intra_id, 7007)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.email, "alice@example.com")
        self.assertIsNone(self.alice.profile.intra_id)

    def test_intra_email_taken_between_check_and_insert(self):
        # The email check passes, then another request takes the email
        # before the insert: the account is still created, without email.
        from unittest import mock

        with mock.patch("apps.accounts.intra.email_taken", return_value=False):
            user = self.intra(8008, "racer", "alice@example.com")
        self.assertEqual((user.email, user.profile.intra_id), ("", 8008))

    def test_intra_login_with_free_email_keeps_it(self):
        user = self.intra(9009, "fresh", "fresh@student.42.fr")
        self.assertEqual(user.email, "fresh@student.42.fr")

    def test_settings_cannot_take_another_users_email(self):
        from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT

        make_user("bob")
        self.login("bob")
        response = self.client.put(
            "/api/auth/settings/update/",
            data=encode_multipart(BOUNDARY, {
                "username": "bob", "email": "ALICE@example.com",
                "current_password": PASSWORD,
            }),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(User.objects.get(username="bob").email, "bob@example.com")

    def test_settings_with_own_email_in_another_case_is_fine(self):
        from django.test.client import encode_multipart, BOUNDARY, MULTIPART_CONTENT

        self.login("alice")
        response = self.client.put(
            "/api/auth/settings/update/",
            data=encode_multipart(BOUNDARY, {"username": "alice", "email": "ALICE@example.com"}),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 200, response.content)


class DrfDefaultAuthTests(AuthTestCase):
    """Only the JWT cookie authenticates. DRF's default Session and Basic
    authentication must not run: Basic answered differently for a right and
    a wrong password, which let anyone guess passwords past the login rate
    limit."""

    def setUp(self):
        super().setUp()
        self.user = make_user("bob")

    def basic(self, password):
        import base64

        token = base64.b64encode(f"bob:{password}".encode()).decode()
        return self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Basic {token}")

    def test_basic_auth_gives_no_password_oracle(self):
        right = self.basic(PASSWORD)
        wrong = self.basic("wrong-password")
        self.assertEqual(right.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(right.json(), wrong.json())
        self.assertEqual(right.json()["message"], "No access token found")

    def test_basic_auth_with_a_wrong_password_does_not_block_the_cookie(self):
        self.login("bob")
        response = self.basic("wrong-password")
        self.assertEqual(response.status_code, 200, response.content)

    def test_admin_session_does_not_authenticate_the_api(self):
        self.client.force_login(self.user)  # Django session, as the admin uses
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)
