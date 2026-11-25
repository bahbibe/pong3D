"""Bot game and remote games over the game websockets."""

import asyncio
import json

from helpers import register, run_async, ws_connect


async def updates(socket, count):
    n = 0
    for _ in range(count):
        message = json.loads(await asyncio.wait_for(socket.recv(), 3))
        n += message.get("type") == "game_update_message"
    return n


def test_bot_game_sends_updates():
    async def run():
        async with ws_connect("/ws/game/bot", register()) as game:
            await game.send(json.dumps({"type": "move", "direction": "left"}))
            assert await updates(game, 30) > 10

    run_async(run())


def test_matchmaking_pairs_two_players():
    a, b = register(), register()

    async def run():
        async with ws_connect("/ws/matchmaking", a) as qa, ws_connect("/ws/matchmaking", b) as qb:
            found_a = json.loads(await asyncio.wait_for(qa.recv(), 5))
            found_b = json.loads(await asyncio.wait_for(qb.recv(), 5))
        assert found_a["type"] == found_b["type"] == "game_found"
        assert found_a["game_id"] == found_b["game_id"]
        game_id = found_a["game_id"]
        async with ws_connect(f"/ws/game/{game_id}", a) as ga, ws_connect(f"/ws/game/{game_id}", b):
            assert await updates(ga, 20) > 5

    run_async(run())
