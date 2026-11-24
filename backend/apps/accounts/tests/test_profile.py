import json
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import Profile
from .helpers import PASSWORD, make_user, AuthTestCase


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
        migration = importlib.import_module(
            "apps.accounts.migrations.0015_backfill_missing_profiles"
        )
        migration.create_missing_profiles(apps, None)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps(
                {
                    "username": "gina",
                    "email": "gina@example.com",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                    "first_name": "G",
                    "last_name": "H",
                }
            ),
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
        from apps.friends.models import Friendship

        Friendship.objects.create(
            source_user=self.other,
            target_user=self.henry,
            status=Friendship.BLOCKED,
            blocked_by=self.other,
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
        from apps.notifications.models import Notification

        Notification.objects.create(user=self.henry, type="system", message="hello")
        notifications = self.me()["data"]["notifications"]
        self.assertIsNone(notifications[0]["sender"])

    def test_unexpected_error_does_not_leak_details(self):
        from unittest import mock

        with mock.patch(
            "apps.accounts.selectors.blocked_user_ids", side_effect=RuntimeError("secret detail")
        ):
            with self.assertLogs("core.exceptions", level="ERROR"):
                response = self.client.get("/api/auth/users/")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret detail", response.content.decode())


class AvatarSizeTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("erin")
        self.login("erin")

    def png(self, side):
        import io
        import os
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        # Random pixels do not compress, so the file size follows `side`.
        image = Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return SimpleUploadedFile("a.png", buffer.getvalue(), content_type="image/png")

    def test_large_avatar_is_refused(self):
        avatar = self.png(1000)  # about 3 MB
        self.assertGreater(avatar.size, 2 * 1024 * 1024)
        response = self.client.post("/api/auth/setup/", {"username": "erin", "avatar": avatar})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("avatar", response.json()["errors"])
        self.user.profile.refresh_from_db()
        self.assertEqual(str(self.user.profile.avatar), "avatars/profile_default.jpg")

    def test_small_avatar_is_saved(self):
        import shutil
        import tempfile
        from django.test import override_settings

        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, True)
        with override_settings(MEDIA_ROOT=media):
            response = self.client.post(
                "/api/auth/setup/", {"username": "erin", "avatar": self.png(64)}
            )
        self.assertEqual(response.status_code, 200, response.content)
        self.user.profile.refresh_from_db()
        self.assertTrue(str(self.user.profile.avatar).startswith("avatars/"))
        self.assertNotEqual(str(self.user.profile.avatar), "avatars/profile_default.jpg")
