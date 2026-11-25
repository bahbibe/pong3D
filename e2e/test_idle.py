"""Sockets left idle longer than the channel layer's 5 s blocking pop still
get messages (redis-py 8 timed out reads at 5 s by default)."""

import asyncio
import json

from helpers import befriend, register, run_async, ws_connect

IDLE_SECONDS = 12


def test_idle_notification_socket_still_receives():
    a, b = register(), register()
    befriend(a, b)

    async def run():
        async with ws_connect("/ws/notifications/", b) as notes:
            await asyncio.sleep(IDLE_SECONDS)
            assert a.api("POST", f"/api/game/invite_friend/{b.id}").ok
            message = json.loads(await asyncio.wait_for(notes.recv(), 5))
            assert message["ctx"] == "game_invite"

    run_async(run())
