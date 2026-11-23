"""
Small failure counter for login and 2FA, stored in the Django cache.

Only failed attempts are counted. When a counter is over its limit the
endpoint answers 429 until the window ends, even for correct credentials,
so guessing a password or a 6-digit TOTP code stops being practical.

The default cache is per process (LocMemCache). That is enough while the
backend runs as one process; use a shared cache (Redis) if it is scaled out.
"""

from django.core.cache import cache
from rest_framework import status

from utils.responses import ErrorResponse

# scope: (max failures, window in seconds)
LIMITS = {
    "login-account": (10, 15 * 60),
    "login-ip": (30, 15 * 60),
    "tfa-user": (5, 5 * 60),
}


def _key(scope, ident):
    return f"ratelimit:{scope}:{ident}"


def client_ip(request):
    """
    Client address. nginx appends the real client to X-Forwarded-For, so the
    last entry is the one we can trust (earlier ones come from the client).
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def is_blocked(scope, ident):
    limit, _ = LIMITS[scope]
    return (cache.get(_key(scope, ident)) or 0) >= limit


def record_failure(scope, ident):
    _, window = LIMITS[scope]
    key = _key(scope, ident)
    if cache.add(key, 1, timeout=window):
        return
    try:
        cache.incr(key)
    except ValueError:
        # Expired between add() and incr().
        cache.set(key, 1, timeout=window)


def reset(scope, ident):
    cache.delete(_key(scope, ident))


def too_many_attempts():
    return ErrorResponse(
        message="Too many failed attempts. Please wait a few minutes and try again.",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )
