"""Accounts services and selectors directly, plus the JSON shape of the
service errors that carry field errors."""

import json

from django.test import TestCase

from apps.accounts import selectors, services, twofa
from core.errors import NotFound, ServiceError, TooManyAttempts

from .helpers import PASSWORD, AuthTestCase, make_user


class LoginServiceTests(AuthTestCase):
    def test_needs_email_or_username(self):
        with self.assertRaisesMessage(ServiceError, "An email or username is required"):
            services.login(PASSWORD, ip="1.2.3.4")

    def test_email_is_case_insensitive_and_failures_lock(self):
        user = make_user("lena")
        self.assertEqual(services.login(PASSWORD, ip="1.2.3.4", email="LENA@example.com"), user)
        for _ in range(10):
            with self.assertRaises(ServiceError) as caught:
                services.login("wrong", ip="1.2.3.4", username="lena")
            self.assertEqual(caught.exception.status_code, 404)
        with self.assertRaises(TooManyAttempts):
            services.login(PASSWORD, ip="5.6.7.8", username="lena")


class ProfileSelectorTests(TestCase):
    def test_lookup_errors(self):
        viewer = make_user("viewer")
        for bad in ("not-a-uuid", "00000000-0000-0000-0000-000000000000"):
            with self.assertRaisesMessage(NotFound, "User does not exist"):
                selectors.user_by_profile_uuid(bad, viewer)
        for bad in ("abc", "999999"):
            with self.assertRaises(NotFound):
                selectors.user_by_profile_id(bad, viewer)
        self.assertEqual(selectors.user_by_profile_id(str(viewer.profile.id), viewer), viewer)

    def test_search_is_capped(self):
        viewer = make_user("viewer")
        for i in range(selectors.MAX_SEARCH_RESULTS + 5):
            make_user(f"many{i}")
        self.assertEqual(len(selectors.search_users(viewer, "many")), selectors.MAX_SEARCH_RESULTS)


class TwoFactorServiceTests(AuthTestCase):
    def test_order_of_checks(self):
        user = make_user("tina")
        with self.assertRaisesMessage(ServiceError, "No code found"):
            twofa.confirm(user, "")
        with self.assertRaisesMessage(ServiceError, "2FA is not enabled"):
            twofa.confirm(user, "123456")
        with self.assertRaisesMessage(ServiceError, "2FA is not enabled"):
            twofa.verify(user, "123456")
        self.assertTrue(twofa.start(user).startswith("data:image/png;base64,"))
        with self.assertRaisesMessage(ServiceError, "Invalid code"):
            twofa.confirm(user, "000000")


class FieldErrorShapeTests(AuthTestCase):
    def test_wrong_current_password_lists_the_field(self):
        from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

        make_user("fred")
        self.login("fred")
        response = self.client.put(
            "/api/auth/settings/update/",
            data=encode_multipart(
                BOUNDARY, {"password": "New-Strong-Pass-8", "current_password": "nope"}
            ),
            content_type=MULTIPART_CONTENT,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.content),
            {
                "success": False,
                "message": "Current password is incorrect.",
                "errors": {"current_password": "Current password is incorrect."},
            },
        )
