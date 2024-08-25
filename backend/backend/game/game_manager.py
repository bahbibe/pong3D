# game_manager.py
import asyncio
from channels.layers import get_channel_layer

class GameInstance:
    def __init__(self, game_id, channel_layer):
        self.game_id = game_id
        self.game_state = {
            'ball_position': [0, 0],
            'player1': 0,
            'player2': 0,
            'score': [0, 0]
        }
        self.vel = [1, 1]
        self.speed = 0.04
        self.limit = [1.83, 2.7]
        self.channel_layer = channel_layer
        self.running = True
        self.game_loop_task = asyncio.create_task(self.game_loop())

    async def game_loop(self):
        await self.channel_layer.group_send(self.game_id, {
            "type": "send_game_id",
            "game_id": self.game_id,
            })
        while True:
            self.update_ball_position()
            await self.channel_layer.group_send(self.game_id, {
                "type": "game_update_message",
                "game_state": self.game_state,
                })
            if self.check_for_game_end():
                print("end")
                self.running = False
                # await self.on_game_end()
                break
            await asyncio.sleep(1/60)  # Run at 60 FPS

    def check_for_game_end(self):
        # Check if the game has ended (e.g., a player has reached a certain score)
        # and update the game state accordingly
        # Return True if the game has ended, False otherwise
        return False

    async def on_game_end(self):
        # Notify the clients that the game has ended
        await self.send_game_end_notification()

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
        self.game_state['ball_position'][0] += self.vel[0] * self.speed
        self.game_state['ball_position'][1] += self.vel[1] * self.speed

        if self.game_state['ball_position'][0] > self.limit[0] or self.game_state['ball_position'][0] < -self.limit[0]:
            self.vel[0] *= -1
        if self.game_state['ball_position'][1] > self.limit[1] or self.game_state['ball_position'][1] < -self.limit[1]:
            self.vel[1] *= -1
        
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