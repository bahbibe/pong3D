"""Settings for running the test suite without Redis.

Tests need Postgres (some models use CharField without max_length, which
SQLite cannot create). Start a throwaway one, then run the tests:

    docker run -d --rm --name pong3d-test-pg -p 127.0.0.1:55432:5432 \
        -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test \
        postgres:16-alpine
    DJANGO_SETTINGS_MODULE=ft_transcendence.test_settings python manage.py test

Override the connection with TEST_POSTGRES_HOST/PORT/USER/PASSWORD/DB.
"""

import os

os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-django-secret-not-for-production")

from .settings import *  # noqa: E402,F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("TEST_POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("TEST_POSTGRES_PORT", "55432"),
        "USER": os.getenv("TEST_POSTGRES_USER", "test"),
        "PASSWORD": os.getenv("TEST_POSTGRES_PASSWORD", "test"),
        "NAME": os.getenv("TEST_POSTGRES_DB", "test"),
    }
}

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
