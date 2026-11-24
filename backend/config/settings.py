import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from core.redis_url import redis_url


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# The key that used to be hardcoded here is in git history; never reuse it.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is not set (see .env.example).")

# Signs the access tokens (apps/accounts/auth_utils.py).
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ImproperlyConfigured("JWT_SECRET is not set (see .env.example).")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DJANGO_DEBUG", default=False)

# Also used by channels' AllowedHostsOriginValidator to check the Origin of
# WebSocket handshakes, so "*" would let any site open sockets as the user.
# "backend" is the Docker service name (Prometheus scrapes backend:8000).
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend")
# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "channels",
    "django_prometheus",
    # Project apps (backend/apps/). Labels are unchanged: accounts is "api".
    "apps.accounts.apps.AccountsConfig",
    "apps.friends.apps.FriendsConfig",
    "apps.chat.apps.ChatConfig",
    "apps.game.apps.GameConfig",
    "apps.matchmaking.apps.MatchmakingConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.presence.apps.PresenceConfig",
]


MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

# The frontend is served by nginx on the same origin as the API, so no CORS
# is needed by default. Add extra origins (scheme://host:port, comma
# separated) only for a frontend served elsewhere.
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "https://localhost:1337")

# nginx terminates TLS and sets X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

# HSTS: 0 (off) by default. Browsers apply HSTS to a host on every port, so
# turning it on for localhost would also force HTTPS on other local apps.
# Set it (e.g. 31536000) for a real domain.
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS") or 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS")

SILENCED_SYSTEM_CHECKS = [
    # SECURE_SSL_REDIRECT: nginx already redirects port 80 to HTTPS, and
    # Django only sees plain HTTP from nginx and from in-container calls.
    "security.W008",
    # SECURE_HSTS_PRELOAD: asks browsers to hard-code HTTPS for the domain,
    # which is hard to undo. Opt in by hand once the prod domain is final.
    "security.W021",
]

# API authentication: the JWT access token cookie only (no session, no
# Basic auth: Basic answered differently for a right and a wrong password,
# a password oracle past the login rate limit). Every view needs a token
# past the 2FA step unless it says otherwise (see apps/accounts/).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["apps.accounts.permissions.IsTfaVerified"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.handler",
}

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "config.asgi.application"

# Redis: DB 0 for channels, presence and matchmaking; DB 1 for the cache.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [redis_url()],
        },
    },
}

# Shared by every request handler and kept across backend restarts (the
# login and 2FA failure counters live here, see api/rate_limit.py).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": redis_url(db=1),
    }
}


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files. nginx serves the frontend; Django's own static files (the
# admin's CSS) are not served, the admin is only reached through a tunnel.
STATIC_URL = "/django-static/"

# Uploads. Avatars are saved as "avatars/<name>" relative to MEDIA_ROOT
# (backend/media/avatars/, a named volume in prod). nginx serves them at
# /avatars/. MEDIA_URL stays empty: the API returns the relative path.
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT") or BASE_DIR / "media")


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


ACCESS_TOKEN_LIFETIME = timedelta(days=1)  # 1 day

# Auth cookie (see api.auth_utils.set_access_token). Secure needs HTTPS;
# browsers also accept it on http://localhost.
AUTH_COOKIE_SECURE = SESSION_COOKIE_SECURE
AUTH_COOKIE_SAMESITE = "Lax"

# Where the intra OAuth callback sends the browser after login.
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://localhost:1337/")


# Everything goes to stdout (docker compose logs). DJANGO_LOG_LEVEL sets the
# level of the project's own loggers (apps.*, config.*); libraries log at
# WARNING and above.
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "apps": {"level": LOG_LEVEL},
        "config": {"level": LOG_LEVEL},
        "core": {"level": LOG_LEVEL},
        "django.request": {"level": "ERROR"},
    },
}
