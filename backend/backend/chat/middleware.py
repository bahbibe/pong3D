from channels.middleware import BaseMiddleware
# from api.auth_utils import is_authenticated

class ChatMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)
    async def __call__(self, scope, receive, send):
        print("Middleware called")
        return await self.inner(scope, receive, send)
