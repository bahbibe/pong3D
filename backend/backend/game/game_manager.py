# game_manager.py
import asyncio
import random
from channels.layers import get_channel_layer
from .models import Game
from channels.db import database_sync_to_async

class GameInstance:
    def __init__(self, game, channel_layer):
        self.game_id = str(game.id)
        self.game_state = {
            'ball_position': [0, 0],
            'player1': 0,
            'player2': 0,
        }
        self.vel = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.speed = 0.04
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

    async def game_loop(self):
        while self.running:
            if self.game.player1_score >= 3 or self.game.player2_score >= 3:
                    self.game_state['score'] = [self.game.player1_score, self.game.player2_score]
                    await self.channel_layer.group_send(self.game_id, {
                        "type": "game_update_message",
                        "game_state": self.game_state,
                    })
                    await asyncio.sleep(1)  # Wait 1 second
                    break
            if not self.paused and self.ready['player1'] and self.ready['player2']:
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
        # self.game_state['player1'] = 0
        # self.game_state['player2'] = 0
        self.vel = [random.choice([-1, 1]), random.choice([-1, 1])]

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