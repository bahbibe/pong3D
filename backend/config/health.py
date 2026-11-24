"""GET /healthz for the container healthcheck. Not proxied by nginx."""

import logging

import redis
from django.db import Error as DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from core.redis_url import redis_url

logger = logging.getLogger(__name__)


def database_ok():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except DatabaseError:
        logger.exception("healthz: database check failed")
        return False


def redis_ok():
    try:
        client = redis.Redis.from_url(redis_url(), socket_connect_timeout=2, socket_timeout=2)
        return bool(client.ping())
    except redis.RedisError:
        logger.exception("healthz: redis check failed")
        return False


@require_GET
def healthz(request):
    checks = {"db": database_ok(), "redis": redis_ok()}
    healthy = all(checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "down",
         **{name: "ok" if ok else "down" for name, ok in checks.items()}},
        status=200 if healthy else 503,
    )
