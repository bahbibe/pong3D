import asyncio
import json
from datetime import datetime, timedelta

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from apps.accounts.auth_utils import generate_token
from apps.accounts.models import Profile
from apps.game.consumers import bot_manager, game_manager
from apps.game.models import Game
from config.asgi import application


def make_user(username):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    # Profile comes from the post_save signal.
    Profile.objects.filter(user=user).update(is_setup=True)
    user.refresh_from_db()
    return user


def token_for(user):
    return generate_token(
        {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
    )


async def ws_connect(path, user=None):
    headers = [(b"origin", b"http://localhost")]
    if user is not None:
        headers.append((b"cookie", f"access_token={token_for(user)}".encode()))
    communicator = WebsocketCommunicator(application, path, headers=headers)
    connected, _ = await communicator.connect()
    assert connected
    return communicator


async def receive_until(communicator, message_type, timeout=5):
    """Read messages until one with `type` == message_type arrives."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise AssertionError(f"no {message_type!r} message within {timeout}s")
        message = json.loads(await communicator.receive_from(timeout=remaining))
        if message.get("type") == message_type:
            return message


async def wait_for(predicate, timeout=3):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() > deadline:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.05)


class GameTestCase(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.eve = make_user("eve")
        self.game = Game.objects.create(player1=self.alice, player2=self.bob)
        self.path = f"/ws/game/{self.game.id}"

    def tearDown(self):
        game_manager.stop_all()
        bot_manager.stop_all()
