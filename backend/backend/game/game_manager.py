# game_manager.py
import asyncio
import random
import time
import math

from channels.layers import get_channel_layer
from .models import Game
from channels.db import database_sync_to_async

BALL_SPEED = 0.07
BALL_SPEED_ACCELERATION = 0.00001

class GameInstance:
    def __init__(self, game, channel_layer):
        self.game_id = str(game.id)
        self.game_state = {
            'ball_position': [0, 0],
            'player1': 0,
            'player2': 0,
            'score': [0,0],
        }
        self.vel = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.speed = BALL_SPEED
        self.limit = [3.5, 5]
        self.channel_layer = channel_layer
        self.running = True
        self.game_loop_task = asyncio.create_task(self.game_loop())
        self.game = game
        self.paused = False
        self.ready = {
            'player1': False,
            'player2': False,
        }
        self.reset_pause = True

    async def game_loop(self):
        while self.running:
            if self.reset_pause:
                self.reset_pause = False
                await self.channel_layer.group_send(f"{self.player.username}_bot", {
                    "type": "game_update_message",
                    "game_state": self.game_state,
                    })
                await asyncio.sleep(1)  # Wait 1 second
            if self.game.player1_score >= 11 or self.game.player2_score >= 11:
                self.game_state['score'] = [self.game.player1_score, self.game.player2_score]
                await self.channel_layer.group_send(self.game_id, {
                    "type": "game_update_message",
                    "game_state": self.game_state,
                })
                await asyncio.sleep(1)  # Wait 1 second
                break
            if not self.paused and self.ready['player1'] and self.ready['player2']:
                # print(f"ready['player1']: {self.ready['player1']}\nready['player2']: {self.ready['player2']}")
                self.update_ball_position()
                await self.save_game()
                self.game_state['score'] = [self.game.player1_score, self.game.player2_score]
                await self.channel_layer.group_send(self.game_id, {
                    "type": "game_update_message",
                    "game_state": self.game_state,
                    })
            else:
                await self.channel_layer.group_send(self.game_id, {
                    "type": "send_game_id",
                    "game_id": self.game_id,
                })
                await asyncio.sleep(1)  # Wait 1 second
            await asyncio.sleep(1/60)  # Run at 60 FPS
        await self.send_game_end_notification()

    def set_player_ready(self, player):
        self.ready[player] = True

    @database_sync_to_async
    def save_game(self):
        self.game.save()

    async def send_game_end_notification(self):
        # Use Django Channels to send a game end notification to all the clients
        # in the game instance
        await self.channel_layer.group_send(self.game_id, {
            "type": "send_game_end",
            "game_id": self.game_id,
            })
    
    def update_ball_position(self):
        self.speed += BALL_SPEED_ACCELERATION
        self.player_padding = [0.5, 0.1]
        self.ball_padding = 0.125
        self.game_state['ball_position'][0] += self.vel[0] * self.speed
        self.game_state['ball_position'][1] += self.vel[1] * self.speed

        if self.game_state['ball_position'][0] > self.limit[0]  - self.ball_padding:
            self.vel[0] *= -1
        if self.game_state['ball_position'][0] < -self.limit[0]  + self.ball_padding:
            self.vel[0] *= -1
            

        if self.game_state['ball_position'][1] > self.limit[1] - self.ball_padding: # player 1 lost
            self.game.player2_score += 1 # add point to player 2
            self.reset_game()
            print(self.game.player2_score)
            
        if self.game_state['ball_position'][1] < -self.limit[1] + self.ball_padding: # player 2 lost
            self.game.player1_score += 1 # add point to player 1
            self.reset_game()
            print(self.game.player1_score)
        
        if self.game_state['ball_position'][1] > 4.5 - self.player_padding[1] - self.ball_padding \
        and self.game_state['ball_position'][1] < 4.5 + self.player_padding[1] + self.ball_padding:
            if self.game_state['ball_position'][0] - self.ball_padding < self.game_state['player1'] + self.player_padding[0] \
            and self.game_state['ball_position'][0] + self.ball_padding > self.game_state['player1'] - self.player_padding[0]:
                self.vel[1] = -1
        
        if self.game_state['ball_position'][1] < -4.5 + self.player_padding[1] + self.ball_padding \
        and self.game_state['ball_position'][1] > -4.5 - self.player_padding[1] - self.ball_padding:
            if self.game_state['ball_position'][0] - self.ball_padding < self.game_state['player2'] + self.player_padding[0] \
            and self.game_state['ball_position'][0] + self.ball_padding > self.game_state['player2'] - self.player_padding[0]:
                self.vel[1] = 1
    
    def reset_game(self):
        self.game_state['ball_position'][0] = 0
        self.game_state['ball_position'][1] = 0
        self.vel = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.speed = BALL_SPEED
        self.reset_pause = True

    def set_paused(self, state):
        self.paused = state

        
class GameManager:
    def __init__(self):
        self.game_instances = {}
        self.channel_layer = get_channel_layer()

    async def create_game_instance(self, game):
        self.game_instances[str(game.id)] = GameInstance(game, self.channel_layer)

    async def get_game_instance(self, game_id):
        return self.game_instances.get(game_id)

    async def remove_game_instance(self, game_id):
        if game_id in self.game_instances:
            del self.game_instances[game_id]

class BotInstance:
    def __init__(self, player, channel_layer):
        self.ai = PongAI()
        self.ai_action = 0
        self.player = player
        self.game = Game(
            player1 = player,
            player2 = None,
        )
        self.game_state = {
            'ball_position': [0, 0],
            'player1': 0,
            'player2': 0,
            'ball_velocity': [random.choice([-1, 1]), random.choice([-1, 1])],
            'speed': BALL_SPEED, # initial ball speed
            'score': [0,0]
        }
        self.limit = [3.5, 5] # board limit -3.5, 3.5 width -5, 5 lenght
        self.channel_layer = channel_layer
        self.running = True
        self.game_loop_task = asyncio.create_task(self.game_loop())    
        self.paused = False
        self.ready = {
            'player1': False,
            'player2': True,
        }
        self.reset_pause = True

    async def game_loop(self):
        while self.running:
            if self.reset_pause:
                self.reset_pause = False
                await self.channel_layer.group_send(f"{self.player.username}_bot", {
                    "type": "game_update_message",
                    "game_state": self.game_state,
                    })
                await asyncio.sleep(1)  # Wait 1 second
            if self.game.player1_score >= 11 or self.game.player2_score >= 11:
                await self.channel_layer.group_send(f"{self.player.username}_bot", {
                    "type": "game_update_message",
                    "game_state": self.game_state,
                })
                await asyncio.sleep(1)  # Wait 1 second
                break
            if not self.paused:
                self.update_ball_position()
                self.move_bot_paddle()
                self.game_state['score'] = [self.game.player1_score, self.game.player2_score]
                await self.channel_layer.group_send(f"{self.player.username}_bot", {
                    "type": "game_update_message",
                    "game_state": self.game_state,
                    })
            else:
                await self.channel_layer.group_send(f"{self.player.username}_bot", {
                    "type": "send_game_id",
                    "game_id": f"{self.player.username}_bot",
                })
                await asyncio.sleep(1)  # Wait 1 second
            await asyncio.sleep(1/60)  # Run at 60 FPS
        await self.send_game_end_notification()

    def set_player_ready(self, player):
        self.ready[player] = True

    async def send_game_end_notification(self):
        # Use Django Channels to send a game end notification to all the clients
        # in the game instance
        await self.channel_layer.group_send(f"{self.player.username}_bot", {
            "type": "send_game_end",
            "game_id": f"{self.player.username}_bot",
            })
    
    def update_ball_position(self):
        self.game_state['speed'] += BALL_SPEED_ACCELERATION
        self.player_padding = [0.5, 0.1]
        self.ball_padding = 0.125
        self.game_state['ball_position'][0] += self.game_state['ball_velocity'][0] * self.game_state['speed']
        self.game_state['ball_position'][1] += self.game_state['ball_velocity'][1] * self.game_state['speed']

        if self.game_state['ball_position'][0] > self.limit[0]  - self.ball_padding:
            self.game_state['ball_velocity'][0] *= -1
        if self.game_state['ball_position'][0] < -self.limit[0]  + self.ball_padding:
            self.game_state['ball_velocity'][0] *= -1
            

        if self.game_state['ball_position'][1] > self.limit[1] - self.ball_padding: # player 1 lost
            self.game.player2_score += 1 # add point to player 2
            self.ai.adjust_difficulty(False)
            self.reset_game()
            print(self.game.player2_score)
            
        if self.game_state['ball_position'][1] < -self.limit[1] + self.ball_padding: # player 2 lost
            self.game.player1_score += 1 # add point to player 1
            self.ai.adjust_difficulty(True)
            self.reset_game()
            print(self.game.player1_score)
        
        if self.game_state['ball_position'][1] > 4.5 - self.player_padding[1] - self.ball_padding \
        and self.game_state['ball_position'][1] < 4.5 + self.player_padding[1] + self.ball_padding:
            if self.game_state['ball_position'][0] - self.ball_padding < self.game_state['player1'] + self.player_padding[0] \
            and self.game_state['ball_position'][0] + self.ball_padding > self.game_state['player1'] - self.player_padding[0]:
                self.game_state['ball_velocity'][1] = -1
        
        if self.game_state['ball_position'][1] < -4.5 + self.player_padding[1] + self.ball_padding \
        and self.game_state['ball_position'][1] > -4.5 - self.player_padding[1] - self.ball_padding:
            if self.game_state['ball_position'][0] - self.ball_padding < self.game_state['player2'] + self.player_padding[0] \
            and self.game_state['ball_position'][0] + self.ball_padding > self.game_state['player2'] - self.player_padding[0]:
                self.game_state['ball_velocity'][1] = 1

        
    def move_bot_paddle(self):
        self.ai_action = self.ai.move_bot_paddle(self.game_state)
        BOT_SPEED = 5 * 0.015  # Same speed as player
        
        self.game_state['player2'] += BOT_SPEED * self.ai_action
        
        # Keep paddle within bounds
        self.game_state['player2'] = max(-3, min(3, self.game_state['player2']))

    
    def reset_game(self):
        self.game_state['ball_position'][0] = 0
        self.game_state['ball_position'][1] = 0
        self.game_state['ball_velocity'] = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.game_state['speed'] = BALL_SPEED
        self.reset_pause = True

    def set_paused(self, state):
        self.paused = state

class BotManager:
    def __init__(self):
        self.bot_instances = {}
        self.channel_layer = get_channel_layer()

    async def create_bot_instance(self, player):
        print(f"create player_id: {player.id}")
        self.bot_instances[str(player.id)] = BotInstance(player, self.channel_layer)

    async def get_bot_instance(self, player_id):
        print(f"get player_id: {player_id}")
        return self.bot_instances.get(player_id)

    async def remove_bot_instance(self, player_id):
        print(f"remove player_id: {player_id}")
        if player_id in self.bot_instances:
            del self.bot_instances[player_id]


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
        ball_pos = game_state['ball_position'].copy()
        ball_vel = game_state['ball_velocity'].copy()
        speed = game_state.get('speed', 1)  # Get current ball speed
        
        # If ball is moving towards player's side (positive y), return center
        if ball_vel[1] > 0:
            return 0
            
        # Calculate time to reach AI's side
        time_to_reach = (-5 - ball_pos[1]) / (ball_vel[1] * speed)
        
        # Calculate number of bounces
        predicted_x = ball_pos[0]
        predicted_y = ball_pos[1]
        
        # Simulate ball movement until it reaches AI's side
        while predicted_y > -5:
            # Update position
            next_x = predicted_x + ball_vel[0] * speed
            next_y = predicted_y + ball_vel[1] * speed
            
            # Check for wall bounces
            if abs(next_x) > 3.5:
                # Ball will bounce off wall
                ball_vel[0] *= -1
                # Adjust for overflow past wall
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
        BOT_SPEED = 5 * 0.015

        # Only update AI decision every second
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            
            # Predict where ball will intersect with AI's side
            if random.random() < self.skill_level:
                self.predicted_ball_position = self.predict_ball_intersection(game_state)
            else:
                self.predicted_ball_position = random.uniform(-3.5, 3.5)
            
            # Determine movement direction
            diff = self.predicted_ball_position - game_state['player2']
            self.moves = int(abs(diff) / BOT_SPEED)


            # Set direction for keyboard simulation
            self.current_direction = 1 if diff > 0 else -1
            print(f"moves: {self.moves}, direction: {self.current_direction}, diff: {diff}, skill_level: {self.skill_level}")

            # # Add occasional random movement when ball is far
            # if game_state['ball_position'][1] > 0 and random.random() < 0.2:
            #     self.current_direction = random.choice([-1, 0, 1])
        
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