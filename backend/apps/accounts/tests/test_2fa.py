import pyotp
from django.utils import timezone

from apps.accounts.models import Profile

from .helpers import AuthTestCase, make_user


class TwoFactorTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.secret = pyotp.random_base32()
        self.user = make_user("alice", is_tfa_enabled=True, tfa_secret=self.secret)

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
        self.forget_used_code()

    def forget_used_code(self):
        # A code works once. Tests that need a second code inside the same
        # 30 s step act as if the next step had started.
        Profile.objects.filter(user=self.user).update(tfa_last_counter=None)

    def test_code_is_accepted_only_once(self):
        code = self.code()
        self.login("alice")
        first = self.post_json("/api/auth/twofa/verify/", {"code": code})
        self.assertEqual(first.status_code, 200, first.content)

        self.login("alice")
        replay = self.post_json("/api/auth/twofa/verify/", {"code": code})
        self.assertEqual(replay.status_code, 400)
        self.assert_blocked_by_2fa(self.client.get("/api/auth/me/"))

    def test_code_from_an_older_step_is_refused(self):
        totp = pyotp.TOTP(self.secret)
        Profile.objects.filter(user=self.user).update(
            tfa_last_counter=totp.timecode(timezone.now())
        )
        self.login("alice")
        response = self.post_json("/api/auth/twofa/verify/", {"code": self.code()})
        self.assertEqual(response.status_code, 400)

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
        self.assertEqual(self.post_json("/api/auth/twofa/verify/", {"code": good}).status_code, 200)
        self.assertEqual(
            self.post_json("/api/auth/twofa/disable/", {"code": "000000"}).status_code, 400
        )
