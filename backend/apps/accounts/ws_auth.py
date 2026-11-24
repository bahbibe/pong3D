from channels.db import database_sync_to_async

from .authentication import COOKIE, InvalidToken, UnknownUser, is_tfa_verified, user_for_token


@database_sync_to_async
def user_from_cookie(token):
    """The token's user, or None. Same checks as the API
    (authentication.JWTCookieAuthentication + permissions.IsTfaVerified):
    a token issued before the 2FA step does not authenticate a user who has
    2FA on."""
    try:
        user, claims = user_for_token(token)
    except (InvalidToken, UnknownUser):
        return None
    if user.profile.is_tfa_enabled and not is_tfa_verified(claims):
        return None
    return user


class WSAuthMiddleware:
    """
    Authenticate WebSocket connections with the access token cookie.

    On any failure the connection goes on with the user set by the outer
    AuthMiddlewareStack (AnonymousUser), and each consumer closes it with
    4001. Returning without calling the app would leave the socket hanging.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        token = scope.get("cookies", {}).get(COOKIE)
        if token:
            user = await user_from_cookie(token)
            if user is not None:
                scope = dict(scope, user=user)
        return await self.app(scope, receive, send)


# Close code the frontend treats as "log in again".
CLOSE_UNAUTHORIZED = 4001


async def reject_anonymous(consumer):
    """Accept then close with CLOSE_UNAUTHORIZED when nobody is logged in.
    Returns True when the socket was rejected."""
    user = consumer.scope.get("user")
    if user is None or user.is_anonymous:
        await consumer.accept()
        await consumer.close(code=CLOSE_UNAUTHORIZED)
        return True
    return False
