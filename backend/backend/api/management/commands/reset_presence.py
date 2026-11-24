import os

import redis
from django.core.management.base import BaseCommand

from api.consumer import ONLINE_KEY


class Command(BaseCommand):
    help = (
        "Clear the online counters. Run at startup: after a crash the "
        "disconnect handlers never ran, so old counts would keep users online."
    )

    def handle(self, *args, **options):
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT") or 6379),
            socket_connect_timeout=5,
        )
        try:
            client.delete(ONLINE_KEY)
        except redis.RedisError as error:
            # Do not block startup; presence is not critical.
            self.stderr.write(f"reset_presence: redis unavailable ({error})")
            return
        self.stdout.write("reset_presence: online counters cleared")
