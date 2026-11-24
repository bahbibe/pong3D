"""
Where Redis is. One place for every client (channel layer, cache, presence,
matchmaking, reset_presence).

REDIS_URL (redis://:password@redis:6379/0) wins. Without it, REDIS_HOST and
REDIS_PORT are used with no password (older .env files).
"""

import os
from urllib.parse import urlsplit, urlunsplit


def redis_url(db=None):
    """Redis URL, optionally pointing at another logical database `db`."""
    url = os.getenv("REDIS_URL")
    if not url:
        host = os.getenv("REDIS_HOST") or "redis"
        port = os.getenv("REDIS_PORT") or "6379"
        url = f"redis://{host}:{port}/0"
    if db is None:
        return url
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{int(db)}", parts.query, parts.fragment))
