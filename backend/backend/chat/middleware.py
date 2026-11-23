import jwt
import os
from django.contrib.auth.models import User
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user(id, is_tfa_verified):
    """
    Return the user for a decoded token, or None.

    A token issued before the 2FA step (`is_tfa_verified` False) does not
    authenticate a user who has 2FA enabled, same rule as the HTTP decorator.
    """
    user = User.objects.select_related("profile").filter(id=id).first()
    if not user:
        return None
    profile = getattr(user, "profile", None)
    if profile is not None and profile.is_tfa_enabled and not is_tfa_verified:
        return None
    return user


class WSAuthMiddleware:
    """
    Authenticate WebSocket connections with the `access_token` cookie.

    On any failure the connection goes on with the user set by the outer
    AuthMiddlewareStack (AnonymousUser), and each consumer closes it with
    4001. Returning without calling the app would leave the socket hanging.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        access_token = scope.get("cookies", {}).get("access_token")
        if access_token:
            try:
                decoded = jwt.decode(
                    access_token, os.getenv("JWT_SECRET"), algorithms=["HS256"]
                )
                user = await get_user(
                    decoded.get("id"), decoded.get("is_tfa_verified") is True
                )
                if user is not None:
                    scope = dict(scope, user=user)
            except jwt.InvalidTokenError:
                pass
        return await self.app(scope, receive, send)
