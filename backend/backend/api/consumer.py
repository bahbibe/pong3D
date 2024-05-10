import json
from channels.generic.websocket import AsyncWebsocketConsumer

connected_users = []


class FriendsStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # TODO: send the status to all the connected users
        # for user in connected_users:
        #     data = {
        #         "type": "friends_status",
        #         "status": "online",
        #         "user": self.scope["user"].id,
        #     }
        #     await self.send(text_data=json.dumps(data))
        connected_users.append(self)

    async def disconnect(self, close_code):
        connected_users.remove(self)
        # TODO: send the status to all the connected users
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        data["type"] = "friends_status"
        # TODO: send the status to all the connected users
        for user in connected_users:
            if user == self:
                continue
            await user.send(text_data=json.dumps(data))
