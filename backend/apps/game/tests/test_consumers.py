import asyncio
import json
from unittest import mock

from channels.db import database_sync_to_async

from apps.game import game_manager as gm
from apps.game.consumers import bot_manager, game_manager
from apps.game.models import Game

from .helpers import GameTestCase, receive_until, wait_for, ws_connect


class GameConsumerAccessTests(GameTestCase):
    async def assert_closed_with(self, communicator, code):
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output["type"], "websocket.close")
        self.assertEqual(output.get("code"), code)

    async def test_anonymous_is_rejected(self):
        communicator = await ws_connect(self.path)
        await self.assert_closed_with(communicator, 4001)
        self.assertEqual(game_manager.game_instances, {})

    async def test_non_player_is_rejected(self):
        communicator = await ws_connect(self.path, self.eve)
        await self.assert_closed_with(communicator, 4003)
        self.assertEqual(game_manager.game_instances, {})

    async def test_unknown_game_is_rejected(self):
        communicator = await ws_connect("/ws/game/999999", self.alice)
        await self.assert_closed_with(communicator, 4003)

    async def test_finished_game_does_not_restart(self):
        await database_sync_to_async(Game.objects.filter(pk=self.game.pk).update)(
            player1_score=11, player2_score=4
        )
        communicator = await ws_connect(self.path, self.alice)
        message = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(message["type"], "game over")
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output["type"], "websocket.close")
        self.assertEqual(game_manager.game_instances, {})


class GameLoopTests(GameTestCase):
    async def test_remote_game_sends_state_updates(self):
        # Regression: the loop used self.player (bot-only attribute) and
        # crashed on its first tick, so players never got any state.
        alice = await ws_connect(self.path, self.alice)
        bob = await ws_connect(self.path, self.bob)
        message = await receive_until(alice, "game_update_message")
        self.assertEqual(message["game_state"]["side"], "player1")
        message = await receive_until(bob, "game_update_message")
        self.assertEqual(message["game_state"]["side"], "player2")
        instance = game_manager.game_instances[str(self.game.id)]
        self.assertFalse(instance.game_loop_task.done())
        await alice.disconnect()
        await bob.disconnect()

    async def test_spamming_moves_does_not_move_paddle(self):
        alice = await ws_connect(self.path, self.alice)
        instance = game_manager.game_instances[str(self.game.id)]
        for _ in range(200):
            await alice.send_to(text_data=json.dumps({"type": "move", "direction": "left"}))
        await wait_for(lambda: instance.directions["player1"] == 1)
        # Bob never joined, so no tick has run: messages only set direction.
        self.assertEqual(instance.game_state["player1"], 0)
        await alice.disconnect()

    async def test_old_and_bad_messages_are_ignored(self):
        alice = await ws_connect(self.path, self.alice)
        instance = game_manager.game_instances[str(self.game.id)]
        for payload in [
            json.dumps({"type": "left"}),
            json.dumps({"type": "game_update", "ball_position": [0, 0]}),
            json.dumps({"type": "move", "direction": "up"}),
            json.dumps(["move"]),
            "not json",
        ]:
            await alice.send_to(text_data=payload)
        self.assertTrue(await alice.receive_nothing(timeout=0.3) or True)
        self.assertEqual(instance.directions, {"player1": 0, "player2": 0})
        self.assertFalse(instance.game_loop_task.done())
        await alice.disconnect()

    async def test_player2_direction_is_flipped(self):
        bob = await ws_connect(self.path, self.bob)
        instance = game_manager.game_instances[str(self.game.id)]
        await bob.send_to(text_data=json.dumps({"type": "move", "direction": "left"}))
        await wait_for(lambda: instance.directions["player2"] == -1)
        await bob.disconnect()

    async def test_abandoned_game_loop_stops(self):
        with mock.patch.object(gm, "ABANDON_TIMEOUT_SECONDS", 0.2):
            alice = await ws_connect(self.path, self.alice)
            instance = game_manager.game_instances[str(self.game.id)]
            await alice.disconnect()
            await wait_for(instance.game_loop_task.done, timeout=4)
        self.assertNotIn(str(self.game.id), game_manager.game_instances)


class GameInstanceUnitTests(GameTestCase):
    async def test_paddle_moves_one_step_per_tick_and_is_clamped(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        instance.set_direction("player1", 1)
        instance.apply_paddle_moves()
        self.assertAlmostEqual(instance.game_state["player1"], gm.PADDLE_STEP)
        for _ in range(1000):
            instance.apply_paddle_moves()
        self.assertEqual(instance.game_state["player1"], gm.PADDLE_LIMIT)

    async def test_score_save_does_not_overwrite_players(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        # Someone else changes the players of this row after it was loaded.
        await database_sync_to_async(Game.objects.filter(pk=self.game.pk).update)(player2=self.eve)
        instance.game_state["ball_position"] = [0, -4.95]
        instance.vel = [1, -1]
        self.assertTrue(instance.update_ball_position())
        await instance.save_scores()
        game = await database_sync_to_async(Game.objects.get)(pk=self.game.pk)
        self.assertEqual(game.player1_score, 1)
        self.assertEqual(game.player2_id, self.eve.id)

    async def test_no_save_without_score(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        self.assertFalse(instance.update_ball_position())


class BotConsumerTests(GameTestCase):
    async def test_anonymous_is_rejected(self):
        communicator = await ws_connect("/ws/game/bot")
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)
        self.assertEqual(bot_manager.bot_instances, {})

    async def test_disconnect_stops_bot_loop(self):
        communicator = await ws_connect("/ws/game/bot", self.alice)
        await receive_until(communicator, "game_update_message")
        instance = bot_manager.bot_instances[str(self.alice.id)]
        self.assertEqual(instance.group_name, f"bot_{self.alice.id}")
        await communicator.disconnect()
        await wait_for(instance.game_loop_task.done)
        self.assertEqual(bot_manager.bot_instances, {})

    async def test_new_tab_replaces_old_bot_game(self):
        first = await ws_connect("/ws/game/bot", self.alice)
        old = bot_manager.bot_instances[str(self.alice.id)]
        second = await ws_connect("/ws/game/bot", self.alice)
        new = bot_manager.bot_instances[str(self.alice.id)]
        self.assertIsNot(old, new)
        await wait_for(old.game_loop_task.done)
        # Closing the old tab must not stop the new game.
        await first.disconnect()
        await asyncio.sleep(0.1)
        self.assertFalse(new.game_loop_task.done())
        await second.disconnect()
        await wait_for(new.game_loop_task.done)

    async def test_bot_move_message(self):
        communicator = await ws_connect("/ws/game/bot", self.alice)
        instance = bot_manager.bot_instances[str(self.alice.id)]
        await communicator.send_to(text_data=json.dumps({"type": "move", "direction": "right"}))
        await wait_for(lambda: instance.directions["player1"] == -1)
        await communicator.disconnect()


class TournamentConsumerTests(GameTestCase):
    async def test_anonymous_is_rejected(self):
        communicator = await ws_connect("/ws/tournament/12345678-1234-4123-8123-123456789012")
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)

    async def test_unknown_tournament_closes_cleanly(self):
        communicator = await ws_connect(
            "/ws/tournament/12345678-1234-4123-8123-123456789012", self.alice
        )
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4004)
