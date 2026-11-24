"""Access tokens: issue, store in the cookie, revoke. Checking them is
authentication.py (DRF) and ws_auth.py (websockets)."""

import jwt
from django.conf import settings
from django.db.models import F
from django.utils import timezone

from .models import Profile


def generate_token(payload):
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def set_access_token(response, user, is_tfa_verified):
    """Issue a new access token for `user` and store it in the auth cookie."""
    access_token_liftime = timezone.now() + settings.ACCESS_TOKEN_LIFETIME
    access_token = generate_token(
        {
            "id": user.id,
            "is_tfa_verified": is_tfa_verified,
            "ver": user.profile.token_version,
            "exp": access_token_liftime,
        }
    )
    response.set_cookie(
        "access_token",
        access_token,
        expires=access_token_liftime,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return response


def revoke_tokens(user):
    """Invalidate every access token issued to `user` so far."""
    Profile.objects.filter(user=user).update(token_version=F("token_version") + 1)
    user.profile.refresh_from_db(fields=["token_version"])


def token_is_current(decoded, user):
    """False for a token issued before the last revoke_tokens() call."""
    return decoded.get("ver", 0) == user.profile.token_version
