import jwt
import os
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from api.auth_utils import token_is_current


@database_sync_to_async
def get_user(decoded):
    """
    Return the user for a decoded token, or None.

    A revoked token (old `ver`, see api.auth_utils.revoke_tokens) is refused.

    A token issued before the 2FA step (`is_tfa_verified` False) does not
    authenticate a user who has 2FA enabled, same rule as the HTTP decorator.
    """
    user = User.objects.select_related("profile").filter(id=decoded.get("id")).first()
    if not user:
        return None
    profile = getattr(user, "profile", None)
    if profile is None or not token_is_current(decoded, user):
        return None
    if profile.is_tfa_enabled and decoded.get("is_tfa_verified") is not True:
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
                user = await get_user(decoded)
                if user is not None:
                    scope = dict(scope, user=user)
            except jwt.InvalidTokenError:
                pass
        return await self.app(scope, receive, send)
