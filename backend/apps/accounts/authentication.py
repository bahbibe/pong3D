"""Access token in the `access_token` cookie (JWT, HS256, see auth_utils).

Used by DRF for every API view (REST_FRAMEWORK in settings) and by the
websocket middleware (ws_auth.py), so both accept and refuse the same
tokens.

No CSRF token is checked. The cookie is SameSite=Lax, so browsers do not
send it on cross-site POST/PUT requests; that is the CSRF protection.
"""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotFound

from .auth_utils import token_is_current

COOKIE = "access_token"


class InvalidToken(Exception):
    """Bad signature, expired, or revoked (see auth_utils.revoke_tokens)."""


class UnknownUser(Exception):
    """The token is valid but its user was deleted."""


def user_for_token(token):
    """Return (user, claims) for a valid token, else raise InvalidToken or
    UnknownUser. Does not check 2FA: see permissions.IsTfaVerified."""
    try:
        claims = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError as error:
        raise InvalidToken(str(error)) from error

    user = get_user_model().objects.select_related("profile").filter(id=claims.get("id")).first()
    if user is None:
        raise UnknownUser()
    if getattr(user, "profile", None) is None or not token_is_current(claims, user):
        raise InvalidToken("revoked")
    return user, claims


def is_tfa_verified(claims):
    return claims.get("is_tfa_verified") is True


class JWTCookieAuthentication(BaseAuthentication):
    """request.user is the token's user, request.auth its claims."""

    def authenticate(self, request):
        token = request.COOKIES.get(COOKIE)
        if not token:
            return None  # anonymous; the permission answers "No access token found"
        try:
            return user_for_token(token)
        except InvalidToken:
            raise AuthenticationFailed("Invalid access token")
        except UnknownUser:
            raise NotFound("User does not exist")

    def authenticate_header(self, request):
        # Any value makes DRF answer 401 (not 403) when authentication fails.
        return 'Cookie realm="api"'
