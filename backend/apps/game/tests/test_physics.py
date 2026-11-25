"""The game rules: ball physics, scoring, the end of a game and the bot AI.

The loops are stopped right after they are created (no tick runs), and
asyncio.sleep is patched where a loop has to run to its end."""

from unittest import mock

from channels.db import database_sync_to_async
from django.test import SimpleTestCase

from apps.game import game_manager as gm
from apps.game.models import Game

from .helpers import GameTestCase


def no_sleep():
    return mock.patch.object(gm.asyncio, "sleep", mock.AsyncMock())


class BallPhysicsTests(GameTestCase):
    """The same rules for remote games (GameInstance) and bot games."""

    async def instances(self):
        remote = gm.GameInstance(self.game, mock.AsyncMock())
        remote.stop()
        bot = gm.BotInstance(self.alice, mock.AsyncMock())
        bot.stop()
        return {"remote": remote, "bot": bot}

    @staticmethod
    def place(instance, position, velocity, speed=None):
        instance.game_state["ball_position"] = list(position)
        if isinstance(instance, gm.BotInstance):
            instance.game_state["ball_velocity"] = list(velocity)
            if speed is not None:
                instance.game_state["speed"] = speed
        else:
            instance.vel = list(velocity)
            if speed is not None:
                instance.speed = speed

    @staticmethod
    def velocity(instance):
        if isinstance(instance, gm.BotInstance):
            return instance.game_state["ball_velocity"]
        return instance.vel

    async def test_side_walls_bounce(self):
        for name, instance in (await self.instances()).items():
            with self.subTest(name):
                self.place(instance, (3.36, 0), (1, 1))
                instance.update_ball_position()
                self.assertEqual(self.velocity(instance)[0], -1)
                self.place(instance, (-3.36, 0), (-1, 1))
                instance.update_ball_position()
                self.assertEqual(self.velocity(instance)[0], 1)

    async def test_ball_past_player1_scores_for_player2_and_resets(self):
        for name, instance in (await self.instances()).items():
            with self.subTest(name):
                self.place(instance, (0, 4.86), (1, 1), speed=0.2)
                instance.reset_pause = False
                instance.update_ball_position()
                self.assertEqual((instance.game.player1_score, instance.game.player2_score), (0, 1))
                self.assertEqual(instance.game_state["ball_position"], [0, 0])
                self.assertTrue(instance.reset_pause)

    async def test_ball_past_player2_scores_for_player1(self):
        for name, instance in (await self.instances()).items():
            with self.subTest(name):
                self.place(instance, (0, -4.86), (1, -1))
                instance.update_ball_position()
                self.assertEqual(instance.game.player1_score, 1)

    async def test_paddles_send_the_ball_back(self):
        for name, instance in (await self.instances()).items():
            with self.subTest(name):
                instance.game_state["player1"] = 1.0
                self.place(instance, (1.2, 4.4), (1, 1), speed=0.01)
                instance.update_ball_position()
                self.assertEqual(self.velocity(instance)[1], -1, "player1 paddle")
                instance.game_state["player2"] = -1.0
                self.place(instance, (-1.2, -4.4), (1, -1), speed=0.01)
                instance.update_ball_position()
                self.assertEqual(self.velocity(instance)[1], 1, "player2 paddle")

    async def test_a_paddle_elsewhere_misses(self):
        for name, instance in (await self.instances()).items():
            with self.subTest(name):
                instance.game_state["player1"] = -3.0
                self.place(instance, (2.0, 4.4), (1, 1), speed=0.01)
                instance.update_ball_position()
                self.assertEqual(self.velocity(instance)[1], 1)

    async def test_ball_speeds_up_every_tick(self):
        instances = await self.instances()
        remote, bot = instances["remote"], instances["bot"]
        remote.update_ball_position()
        bot.update_ball_position()
        expected = gm.BALL_SPEED + gm.BALL_SPEED_ACCELERATION
        self.assertAlmostEqual(remote.speed, expected)
        self.assertAlmostEqual(bot.game_state["speed"], expected)


class EndOfGameTests(GameTestCase):
    async def finish_with(self, score1, score2):
        self.game.player1_score, self.game.player2_score = score1, score2
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        with mock.patch.object(gm, "advance_winner") as advance:
            await instance.finish_game()
        game = await database_sync_to_async(Game.objects.get)(pk=self.game.pk)
        return game, advance

    async def test_is_finished_at_the_winning_score(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        instance.game.player1_score = gm.WINNING_SCORE - 1
        self.assertFalse(instance.is_finished)
        instance.game.player2_score = gm.WINNING_SCORE
        self.assertTrue(instance.is_finished)

    async def test_winner_is_stored_and_the_tournament_advances(self):
        game, advance = await self.finish_with(gm.WINNING_SCORE, 4)
        self.assertEqual((game.status, game.winner_id), (Game.FINISHED, self.alice.id))
        self.assertIsNotNone(game.finished_at)
        advance.assert_called_once()
        game, _ = await self.finish_with(2, gm.WINNING_SCORE)
        self.assertEqual(game.winner_id, self.bob.id)

    async def test_draw_has_no_winner(self):
        game, _ = await self.finish_with(3, 3)
        self.assertEqual(game.status, Game.FINISHED)
        self.assertIsNone(game.winner_id)

    async def test_remote_loop_ends_with_game_over(self):
        self.game.player1_score = gm.WINNING_SCORE
        layer = mock.AsyncMock()
        with no_sleep(), mock.patch.object(gm, "advance_winner"):
            instance = gm.GameInstance(self.game, layer)
            await instance.game_loop_task
        sent = [call.args[1]["type"] for call in layer.group_send.call_args_list]
        self.assertEqual(sent[-1], "send_game_end")
        game = await database_sync_to_async(Game.objects.get)(pk=self.game.pk)
        self.assertEqual((game.status, game.winner_id), (Game.FINISHED, self.alice.id))

    async def test_bot_loop_ends_with_game_over(self):
        layer = mock.AsyncMock()
        with no_sleep():
            instance = gm.BotInstance(self.alice, layer)
            instance.game.player2_score = gm.WINNING_SCORE
            await instance.game_loop_task
        sent = [call.args[1]["type"] for call in layer.group_send.call_args_list]
        self.assertEqual(sent[-1], "send_game_end")
        self.assertFalse(instance.running)

    async def test_updates_carry_the_send_time_and_the_score(self):
        for instance in (
            gm.GameInstance(self.game, mock.AsyncMock()),
            gm.BotInstance(self.alice, mock.AsyncMock()),
        ):
            instance.stop()
            instance.game.player1_score, instance.game.player2_score = 4, 7
            await instance.broadcast_state()
            first = instance.channel_layer.group_send.call_args.args[1]["game_state"]["sent_at"]
            await instance.broadcast_state()
            state = instance.channel_layer.group_send.call_args.args[1]["game_state"]
            self.assertEqual(state["score"], [4, 7])
            self.assertGreaterEqual(state["sent_at"], first)

    async def test_bot_score_changes_the_ai_skill(self):
        bot = gm.BotInstance(self.alice, mock.AsyncMock())
        bot.stop()
        skill = bot.ai.skill_level
        bot.game_state["ball_position"] = [0, -4.86]
        bot.game_state["ball_velocity"] = [1, -1]
        bot.update_ball_position()  # the player scores against the bot
        self.assertGreater(bot.ai.skill_level, skill)

    async def test_bot_paddle_stays_on_the_board(self):
        bot = gm.BotInstance(self.alice, mock.AsyncMock())
        bot.stop()
        bot.game_state["player2"] = gm.PADDLE_LIMIT
        bot.ai.move_bot_paddle = mock.Mock(return_value=1)
        bot.move_bot_paddle()
        self.assertEqual(bot.game_state["player2"], gm.PADDLE_LIMIT)


class PongAITests(SimpleTestCase):
    def setUp(self):
        self.ai = gm.PongAI()

    def state(self, position, velocity, speed=0.5, paddle=0):
        return {
            "ball_position": list(position),
            "ball_velocity": list(velocity),
            "speed": speed,
            "player2": paddle,
        }

    def test_ball_going_away_means_center(self):
        self.assertEqual(self.ai.predict_ball_intersection(self.state((1, 0), (1, 1))), 0)

    def test_prediction_follows_wall_bounces(self):
        self.ai.skill_level = 1  # no error added
        # x: 0.5 a step, bounces off 3.5 at the 8th step, ends at 2.0.
        predicted = self.ai.predict_ball_intersection(self.state((0, 0), (1, -1)))
        self.assertAlmostEqual(predicted, 2.0)

    def test_prediction_stays_on_the_board(self):
        for _ in range(50):
            predicted = self.ai.predict_ball_intersection(self.state((3.4, 4), (1, -1), speed=0.3))
            self.assertLessEqual(abs(predicted), 3.5)

    def test_difficulty_stays_in_its_bounds(self):
        for _ in range(20):
            self.ai.adjust_difficulty(True)
        self.assertEqual(self.ai.skill_level, 0.9)
        for _ in range(40):
            self.ai.adjust_difficulty(False)
        self.assertEqual(self.ai.skill_level, 0.5)
        self.assertEqual(self.ai.consecutive_misses, 0)

    def test_moves_toward_the_prediction_then_stops(self):
        self.ai.skill_level = 1
        target = 2.0
        with (
            mock.patch.object(gm.time, "time", return_value=self.ai.last_update_time + 5),
            mock.patch.object(self.ai, "predict_ball_intersection", return_value=target),
        ):
            first = self.ai.move_bot_paddle(self.state((0, 0), (1, -1)))
        self.assertEqual(first, 1)
        steps = int(target / gm.PADDLE_STEP)
        # Within the same second the AI keeps its decision, then stops.
        moves = [self.ai.move_bot_paddle(self.state((0, 0), (1, -1))) for _ in range(steps + 2)]
        self.assertEqual(moves.count(1), steps - 1)
        self.assertEqual(moves[-1], 0)
