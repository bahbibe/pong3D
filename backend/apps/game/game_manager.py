# game_manager.py
import asyncio
import logging
import random
import time

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Game
from .tournament import advance_winner

logger = logging.getLogger(__name__)

BALL_SPEED = 0.07
BALL_SPEED_ACCELERATION = 0.00001
TICK_SECONDS = 1 / 60
WINNING_SCORE = 11

# Paddle step per tick. Clients only send which way they are pushing; the
# server moves the paddle at this fixed speed, so sending more messages does
# not make a paddle faster.
PADDLE_STEP = 5 * 0.015
PADDLE_LIMIT = 3

# Stop a game loop when no player has been connected for this long.
ABANDON_TIMEOUT_SECONDS = 30

# Direction names sent by the client. Values are for player1; player2 sees
# the board from the other side, so its value is flipped.
DIRECTIONS = {"left": 1, "right": -1, "none": 0}


def _log_task_exception(task):
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error("game loop crashed", exc_info=error)


def clamp_paddle(value):
    return max(-PADDLE_LIMIT, min(PADDLE_LIMIT, value))


class GameInstance:
    def __init__(self, game, channel_layer, on_finish=None):
        self.game_id = str(game.id)
        self.game = game
        self.game_state = {
            "ball_position": [0, 0],
            "player1": 0,
            "player2": 0,
            "score": [game.player1_score, game.player2_score],
        }
        self.vel = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.speed = BALL_SPEED
        self.limit = [3.5, 5]
        self.channel_layer = channel_layer
        self.on_finish = on_finish
        self.running = True
        self.paused = False
        self.ready = {"player1": False, "player2": False}
        self.directions = {"player1": 0, "player2": 0}
        self.connected = {"player1": 0, "player2": 0}
        self.last_seen = time.monotonic()
        self.reset_pause = True
        self.marked_playing = game.status == Game.PLAYING
        # Start the loop last, after every attribute it reads exists.
        self.game_loop_task = asyncio.create_task(self.game_loop())
        self.game_loop_task.add_done_callback(_log_task_exception)

    @property
    def is_finished(self):
        return self.game.player1_score >= WINNING_SCORE or self.game.player2_score >= WINNING_SCORE

    async def broadcast_state(self):
        self.game_state["score"] = [self.game.player1_score, self.game.player2_score]
        await self.channel_layer.group_send(
            self.game_id,
            {"type": "game_update_message", "game_state": self.game_state},
        )

    def is_abandoned(self):
        if any(self.connected.values()):
            self.last_seen = time.monotonic()
            return False
        return time.monotonic() - self.last_seen > ABANDON_TIMEOUT_SECONDS

    async def game_loop(self):
        try:
            while self.running:
                if self.is_abandoned():
                    logger.info("game %s abandoned, stopping loop", self.game_id)
                    return
                if self.reset_pause:
                    self.reset_pause = False
                    await self.broadcast_state()
                    await asyncio.sleep(1)
                if self.is_finished:
                    await self.finish_game()
                    await self.broadcast_state()
                    await asyncio.sleep(1)
                    await self.send_game_end_notification()
                    return
                if not self.paused and self.ready["player1"] and self.ready["player2"]:
                    if not self.marked_playing:
                        await self.mark_playing()
                    self.apply_paddle_moves()
                    if self.update_ball_position():
                        await self.save_scores()
                    await self.broadcast_state()
                else:
                    await self.channel_layer.group_send(
                        self.game_id, {"type": "send_game_id", "game_id": self.game_id}
                    )
                    await asyncio.sleep(1)
                await asyncio.sleep(TICK_SECONDS)
        finally:
            self.running = False
            if self.on_finish is not None:
                self.on_finish(self)

    def stop(self):
        self.running = False
        if not self.game_loop_task.done():
            self.game_loop_task.cancel()

    def set_player_ready(self, player):
        self.ready[player] = True

    def set_direction(self, player, direction):
        self.directions[player] = direction

    def player_connected(self, player):
        self.connected[player] += 1
        self.paused = False

    def player_disconnected(self, player):
        self.connected[player] = max(0, self.connected[player] - 1)
        self.directions[player] = 0
        self.paused = True

    def apply_paddle_moves(self):
        for player in ("player1", "player2"):
            step = PADDLE_STEP * self.directions[player]
            self.game_state[player] = clamp_paddle(self.game_state[player] + step)

    @database_sync_to_async
    def save_scores(self):
        # Only the score columns: other code (tournament qualification) may
        # have changed the players of this row since it was loaded.
        self.game.save(update_fields=["player1_score", "player2_score"])

    @database_sync_to_async
    def mark_playing(self):
        self.marked_playing = True
        self.game.status = Game.PLAYING
        self.game.save(update_fields=["status"])

    @database_sync_to_async
    def finish_game(self):
        game = self.game
        if game.player1_score > game.player2_score:
            game.winner_id = game.player1_id
        elif game.player2_score > game.player1_score:
            game.winner_id = game.player2_id
        game.status = Game.FINISHED
        game.finished_at = timezone.now()
        game.save(
            update_fields=[
                "player1_score",
                "player2_score",
                "status",
                "winner",
                "finished_at",
            ]
        )
        advance_winner(game)

    async def send_game_end_notification(self):
        await self.channel_layer.group_send(
            self.game_id, {"type": "send_game_end", "game_id": self.game_id}
        )

    def update_ball_position(self):
        """Advance the ball one tick. Return True when a point was scored."""
        scored = False
        self.speed += BALL_SPEED_ACCELERATION
        self.player_padding = [0.5, 0.1]
        self.ball_padding = 0.125
        self.game_state["ball_position"][0] += self.vel[0] * self.speed
        self.game_state["ball_position"][1] += self.vel[1] * self.speed

        if self.game_state["ball_position"][0] > self.limit[0] - self.ball_padding:
            self.vel[0] *= -1
        if self.game_state["ball_position"][0] < -self.limit[0] + self.ball_padding:
            self.vel[0] *= -1

        if self.game_state["ball_position"][1] > self.limit[1] - self.ball_padding:  # player 1 lost
            self.game.player2_score += 1
            self.reset_game()
            scored = True

        if (
            self.game_state["ball_position"][1] < -self.limit[1] + self.ball_padding
        ):  # player 2 lost
            self.game.player1_score += 1
            self.reset_game()
            scored = True

        if (
            self.game_state["ball_position"][1] > 4.5 - self.player_padding[1] - self.ball_padding
            and self.game_state["ball_position"][1]
            < 4.5 + self.player_padding[1] + self.ball_padding
        ):
            if (
                self.game_state["ball_position"][0] - self.ball_padding
                < self.game_state["player1"] + self.player_padding[0]
                and self.game_state["ball_position"][0] + self.ball_padding
                > self.game_state["player1"] - self.player_padding[0]
            ):
                self.vel[1] = -1

        if (
            self.game_state["ball_position"][1] < -4.5 + self.player_padding[1] + self.ball_padding
            and self.game_state["ball_position"][1]
            > -4.5 - self.player_padding[1] - self.ball_padding
        ):
            if (
                self.game_state["ball_position"][0] - self.ball_padding
                < self.game_state["player2"] + self.player_padding[0]
                and self.game_state["ball_position"][0] + self.ball_padding
                > self.game_state["player2"] - self.player_padding[0]
            ):
                self.vel[1] = 1
        return scored

    def reset_game(self):
        self.game_state["ball_position"][0] = 0
        self.game_state["ball_position"][1] = 0
        self.vel = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.speed = BALL_SPEED
        self.reset_pause = True

    def set_paused(self, state):
        self.paused = state


class GameManager:
    def __init__(self):
        self.game_instances = {}
        self.channel_layer = get_channel_layer()

    def _forget(self, instance):
        # Called when a loop ends; only drop the entry if it still points
        # at that instance (a newer one may have replaced it).
        if self.game_instances.get(instance.game_id) is instance:
            del self.game_instances[instance.game_id]

    async def create_game_instance(self, game):
        old = self.game_instances.get(str(game.id))
        if old is not None:
            old.stop()
        instance = GameInstance(game, self.channel_layer, on_finish=self._forget)
        self.game_instances[instance.game_id] = instance
        return instance

    async def get_game_instance(self, game_id):
        return self.game_instances.get(str(game_id))

    async def remove_game_instance(self, game_id):
        instance = self.game_instances.pop(str(game_id), None)
        if instance is not None:
            instance.stop()

    def stop_all(self):
        for instance in list(self.game_instances.values()):
            instance.stop()
        self.game_instances.clear()


def bot_group_name(user_id):
    # Channels group names allow only ASCII letters, digits, - _ . so they
    # must not be built from usernames.
    return f"bot_{user_id}"


class BotInstance:
    def __init__(self, player, channel_layer, on_finish=None):
        self.ai = PongAI()
        self.ai_action = 0
        self.player = player
        self.group_name = bot_group_name(player.id)
        self.game = Game(
            player1=player,
            player2=None,
        )
        self.game_state = {
            "ball_position": [0, 0],
            "player1": 0,
            "player2": 0,
            "ball_velocity": [random.choice([-1, 1]), random.choice([-1, 1])],
            "speed": BALL_SPEED,  # initial ball speed
            "score": [0, 0],
        }
        self.limit = [3.5, 5]  # board limit -3.5, 3.5 width -5, 5 lenght
        self.channel_layer = channel_layer
        self.on_finish = on_finish
        self.running = True
        self.paused = False
        self.ready = {
            "player1": False,
            "player2": True,
        }
        self.directions = {"player1": 0}
        self.reset_pause = True
        self.game_loop_task = asyncio.create_task(self.game_loop())
        self.game_loop_task.add_done_callback(_log_task_exception)

    async def game_loop(self):
        try:
            while self.running:
                if self.reset_pause:
                    self.reset_pause = False
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "game_update_message",
                            "game_state": self.game_state,
                        },
                    )
                    await asyncio.sleep(1)
                if (
                    self.game.player1_score >= WINNING_SCORE
                    or self.game.player2_score >= WINNING_SCORE
                ):
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "game_update_message",
                            "game_state": self.game_state,
                        },
                    )
                    await asyncio.sleep(1)
                    await self.send_game_end_notification()
                    return
                if not self.paused:
                    self.apply_paddle_moves()
                    self.update_ball_position()
                    self.move_bot_paddle()
                    self.game_state["score"] = [self.game.player1_score, self.game.player2_score]
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "game_update_message",
                            "game_state": self.game_state,
                        },
                    )
                else:
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "send_game_id",
                            "game_id": self.group_name,
                        },
                    )
                    await asyncio.sleep(1)
                await asyncio.sleep(TICK_SECONDS)
        finally:
            self.running = False
            if self.on_finish is not None:
                self.on_finish(self)

    def stop(self):
        self.running = False
        if not self.game_loop_task.done():
            self.game_loop_task.cancel()

    def set_player_ready(self, player):
        self.ready[player] = True

    def set_direction(self, player, direction):
        if player in self.directions:
            self.directions[player] = direction

    def apply_paddle_moves(self):
        step = PADDLE_STEP * self.directions["player1"]
        self.game_state["player1"] = clamp_paddle(self.game_state["player1"] + step)

    async def send_game_end_notification(self):
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_game_end",
                "game_id": self.group_name,
            },
        )

    def update_ball_position(self):
        self.game_state["speed"] += BALL_SPEED_ACCELERATION
        self.player_padding = [0.5, 0.1]
        self.ball_padding = 0.125
        self.game_state["ball_position"][0] += (
            self.game_state["ball_velocity"][0] * self.game_state["speed"]
        )
        self.game_state["ball_position"][1] += (
            self.game_state["ball_velocity"][1] * self.game_state["speed"]
        )

        if self.game_state["ball_position"][0] > self.limit[0] - self.ball_padding:
            self.game_state["ball_velocity"][0] *= -1
        if self.game_state["ball_position"][0] < -self.limit[0] + self.ball_padding:
            self.game_state["ball_velocity"][0] *= -1

        if self.game_state["ball_position"][1] > self.limit[1] - self.ball_padding:  # player 1 lost
            self.game.player2_score += 1  # add point to player 2
            self.ai.adjust_difficulty(False)
            self.reset_game()

        if (
            self.game_state["ball_position"][1] < -self.limit[1] + self.ball_padding
        ):  # player 2 lost
            self.game.player1_score += 1  # add point to player 1
            self.ai.adjust_difficulty(True)
            self.reset_game()

        if (
            self.game_state["ball_position"][1] > 4.5 - self.player_padding[1] - self.ball_padding
            and self.game_state["ball_position"][1]
            < 4.5 + self.player_padding[1] + self.ball_padding
        ):
            if (
                self.game_state["ball_position"][0] - self.ball_padding
                < self.game_state["player1"] + self.player_padding[0]
                and self.game_state["ball_position"][0] + self.ball_padding
                > self.game_state["player1"] - self.player_padding[0]
            ):
                self.game_state["ball_velocity"][1] = -1

        if (
            self.game_state["ball_position"][1] < -4.5 + self.player_padding[1] + self.ball_padding
            and self.game_state["ball_position"][1]
            > -4.5 - self.player_padding[1] - self.ball_padding
        ):
            if (
                self.game_state["ball_position"][0] - self.ball_padding
                < self.game_state["player2"] + self.player_padding[0]
                and self.game_state["ball_position"][0] + self.ball_padding
                > self.game_state["player2"] - self.player_padding[0]
            ):
                self.game_state["ball_velocity"][1] = 1

    def move_bot_paddle(self):
        self.ai_action = self.ai.move_bot_paddle(self.game_state)
        self.game_state["player2"] += PADDLE_STEP * self.ai_action
        self.game_state["player2"] = clamp_paddle(self.game_state["player2"])

    def reset_game(self):
        self.game_state["ball_position"][0] = 0
        self.game_state["ball_position"][1] = 0
        self.game_state["ball_velocity"] = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.game_state["speed"] = BALL_SPEED
        self.reset_pause = True

    def set_paused(self, state):
        self.paused = state


class BotManager:
    def __init__(self):
        self.bot_instances = {}
        self.channel_layer = get_channel_layer()

    def _forget(self, instance):
        key = str(instance.player.id)
        if self.bot_instances.get(key) is instance:
            del self.bot_instances[key]

    async def create_bot_instance(self, player):
        # One bot game per user: a new connection replaces the old game.
        await self.remove_bot_instance(player.id)
        instance = BotInstance(player, self.channel_layer, on_finish=self._forget)
        self.bot_instances[str(player.id)] = instance
        return instance

    async def get_bot_instance(self, player_id):
        return self.bot_instances.get(str(player_id))

    async def remove_bot_instance(self, player_id):
        instance = self.bot_instances.pop(str(player_id), None)
        if instance is not None:
            instance.stop()

    def stop_all(self):
        for instance in list(self.bot_instances.values()):
            instance.stop()
        self.bot_instances.clear()


class PongAI:
    def __init__(self):
        self.last_update_time = time.time()
        self.update_interval = 1.0  # AI updates view every 1 second
        self.bot_target = 0
        self.predicted_ball_position = 0
        self.current_direction = 0
        self.consecutive_misses = 0
        self.skill_level = 0.7
        self.board_width = 3.5
        self.board_length = 5
        self.moves = 0

    def predict_ball_intersection(self, game_state):
        ball_pos = game_state["ball_position"].copy()
        ball_vel = game_state["ball_velocity"].copy()
        speed = game_state.get("speed", 1)  # Get current ball speed

        # If ball is moving towards player's side (positive y), return center
        if ball_vel[1] > 0:
            return 0

        predicted_x = ball_pos[0]
        predicted_y = ball_pos[1]

        # Simulate ball movement until it reaches AI's side
        while predicted_y > -5:
            next_x = predicted_x + ball_vel[0] * speed
            next_y = predicted_y + ball_vel[1] * speed

            # Check for wall bounces
            if abs(next_x) > 3.5:
                ball_vel[0] *= -1
                overflow = abs(next_x) - 3.5
                next_x = 3.5 * (next_x / abs(next_x)) - overflow * (next_x / abs(next_x))

            predicted_x = next_x
            predicted_y = next_y

        # Add human-like error based on distance
        distance_factor = abs(ball_pos[1] + 5) / 10  # 0 to 1 based on distance
        error_margin = random.uniform(-1, 1) * (1 - self.skill_level) * distance_factor

        return max(-3.5, min(3.5, predicted_x + error_margin))

    def move_bot_paddle(self, game_state):
        current_time = time.time()

        # Only update AI decision every second
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time

            if random.random() < self.skill_level:
                self.predicted_ball_position = self.predict_ball_intersection(game_state)
            else:
                self.predicted_ball_position = random.uniform(-3.5, 3.5)

            diff = self.predicted_ball_position - game_state["player2"]
            self.moves = int(abs(diff) / PADDLE_STEP)
            self.current_direction = 1 if diff > 0 else -1

        if self.moves > 0:
            self.moves -= 1
        else:
            self.current_direction = 0

        return self.simulate_keyboard_input()

    def simulate_keyboard_input(self):
        return self.current_direction

    def adjust_difficulty(self, scored_against):
        if scored_against:
            self.consecutive_misses += 1
            self.skill_level = min(0.9, self.skill_level + 0.1)
        else:
            self.consecutive_misses = 0
            # Make AI slightly worse after successful defense
            self.skill_level = max(0.5, self.skill_level - 0.05)
