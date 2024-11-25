import jwt
import os
from django.contrib.auth.models import User
from channels.db import database_sync_to_async

@database_sync_to_async
def get_user(id):
    user = User.objects.filter(id=id).first()
    if not user:
        return None
    return user

class WSAuthMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        access_token = scope.get("cookies", {}).get("access_token")
        if not access_token:
            print("No access token found")
            return await self.app(scope, receive, send)
        try:
            decoded = jwt.decode(
                access_token, os.getenv("JWT_SECRET"), algorithms=["HS256"]
            )
            user = await get_user(decoded["id"])
            if not user:
                print("User does not exist")
                # !scope['user'] = AnonymousUser()
                return None
            scope['user'] = user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            print("Invalid access token")
            return None
        except Exception as e:
            print(str(e))
            return None
        return await self.app(scope, receive, send)

