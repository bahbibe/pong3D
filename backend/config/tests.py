import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase, TestCase


class AsgiImportTests(SimpleTestCase):
    def test_asgi_module_imports_without_prior_setup(self):
        # Plain daphne imports the module before Django is set up.
        # Importing models first used to raise AppRegistryNotReady.
        backend_dir = Path(__file__).resolve().parent.parent
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(backend_dir),
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "test",
            "JWT_SECRET": "test",
        }
        result = subprocess.run(
            [sys.executable, "-c", "import config.asgi"],
            cwd="/", env=env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])


class HealthzTests(TestCase):
    def test_ok_when_db_and_redis_answer(self):
        from unittest import mock

        with mock.patch("redis.Redis.ping", return_value=True):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "db": "ok", "redis": "ok"})

    def test_503_when_redis_is_down(self):
        from unittest import mock
        import redis

        with mock.patch("redis.Redis.ping", side_effect=redis.ConnectionError("down")), \
                self.assertLogs("config.health", level="ERROR"):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["redis"], "down")

    def test_503_when_database_is_down(self):
        from unittest import mock
        from django.db import OperationalError

        with mock.patch("redis.Redis.ping", return_value=True), mock.patch(
            "config.health.connection.cursor", side_effect=OperationalError("down")
        ), self.assertLogs("config.health", level="ERROR"):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["db"], "down")

    def test_post_is_refused(self):
        self.assertEqual(self.client.post("/healthz").status_code, 405)


class RedisUrlTests(SimpleTestCase):
    def test_redis_url_wins_and_db_can_be_changed(self):
        from unittest import mock
        from core.redis_url import redis_url

        with mock.patch.dict("os.environ", {"REDIS_URL": "redis://:s3cret@redis:6379/0"}):
            self.assertEqual(redis_url(), "redis://:s3cret@redis:6379/0")
            self.assertEqual(redis_url(db=1), "redis://:s3cret@redis:6379/1")

    def test_old_env_without_redis_url(self):
        from unittest import mock
        from core.redis_url import redis_url

        env = {"REDIS_PORT": "6380"}
        with mock.patch.dict("os.environ", env, clear=True):
            self.assertEqual(redis_url(), "redis://redis:6380/0")
