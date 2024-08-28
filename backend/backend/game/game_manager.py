# game_manager.py
import asyncio
from channels.layers import get_channel_layer
from .models import Game
from channels.db import database_sync_to_async

class GameInstance:
    def __init__(self, game_id, channel_layer):
        self.game_id = game_id
        self.game_state = {
            'ball_position': [0, 0],
            'player1': 0,
            'player2': 0,
            'score': [0, 0] # [0] for player1 ; [1] for player2
        }
        self.vel = [1, 1]
        self.speed = 0.02
        self.limit = [3.5, 5]
        self.channel_layer = channel_layer
        self.running = True
        self.game_loop_task = asyncio.create_task(self.game_loop())

    def setPlayer1(self, user):
        self.player1 = user

    def setPlayer2(self, user):
        self.player2 = user

    async def game_loop(self):
        await self.channel_layer.group_send(self.game_id, {
            "type": "send_game_id",
            "game_id": self.game_id,
            })
        while self.running:
            # if self.game_state['score'][0] >= 3 or self.game_state['score'][1] >= 3:
            #     break
            self.update_ball_position()
            await self.channel_layer.group_send(self.game_id, {
                "type": "game_update_message",
                "game_state": self.game_state,
                })
            if self.check_for_game_end():
                self.running = False
                break
            await asyncio.sleep(1/60)  # Run at 60 FPS
        await self.on_game_end()

    def check_for_game_end(self):
        # Check if the game has ended (e.g., a player has reached a certain score)
        # and update the game state accordingly
        # Return True if the game has ended, False otherwise
        return False

    @database_sync_to_async
    def on_game_end(self):
        # Notify the clients that the game has ended
        # await self.send_game_end_notification()
        print("game end")
        print(self.player1)
        print(self.player2)
        print(self.game_state['score'][0])
        print(self.game_state['score'][1])
        game = Game.objects.create(
            player1 = self.player1,
            player2 = self.player2,
            player1_score = self.game_state['score'][0],
            player2_score = self.game_state['score'][1],
        )
        print(game)

    async def send_game_end_notification(self):
        # Use Django Channels to send a game end notification to all the clients
        # in the game instance
        pass
    
    async def send_game_state_update(self):
        print("inside send_game_state")
        pass
        # await self.channel_layer.group_send(self.game_id, {
        #     "type": "game_update_message",
        #     "game_state": self.game_state,
        #     })

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
            self.game_state['score'][1] += 1 # add point to player 2
            self.reset_game()
            print(self.game_state['score'])
            
        if self.game_state['ball_position'][1] < -self.limit[1] + self.ball_padding: # player 2 lost
            self.game_state['score'][0] += 1 # add point to player 1
            self.reset_game()
            print(self.game_state['score'])

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
        self.game_state['player1'] = 0
        self.game_state['player2'] = 0
        self.vel = [1, 1]
        
class GameManager:
    def __init__(self):
        self.game_instances = {}
        self.channel_layer = get_channel_layer()

    async def create_game_instance(self, game_id):
        self.game_instances[game_id] = GameInstance(game_id, self.channel_layer)

    async def get_game_instance(self, game_id):
        return self.game_instances.get(game_id)

    async def remove_game_instance(self, game_id):
        if game_id in self.game_instances:
            del self.game_instances[game_id]