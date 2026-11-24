import functools
import jwt
import logging
import os
from django.conf import settings
from django.utils import timezone
from django.http.request import HttpRequest
from rest_framework import status
from django.db.models import F
from .models import User, Profile
from utils.responses import ErrorResponse, SuccessResponse
from .serializers import UserSerializer


logger = logging.getLogger(__name__)


def generate_token(payload):
    encoded_jwt = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
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


def is_authenticated(view=None, *, allow_unverified_tfa=False):
    """
    Decorator to check if the user is authenticated.

    When the user has 2FA enabled, a token issued after the password step only
    (`is_tfa_verified` False) is rejected, unless the view is explicitly marked
    with `allow_unverified_tfa=True` (2FA verify and logout).

    Usage: `@is_authenticated` or `@is_authenticated(allow_unverified_tfa=True)`.
    """
    if view is None:
        return functools.partial(
            is_authenticated, allow_unverified_tfa=allow_unverified_tfa
        )

    @functools.wraps(view)
    def _decorator(request: HttpRequest, *args, **kwargs):
        if "access_token" not in request.COOKIES:
            return ErrorResponse(
                message="No access token found",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = request.COOKIES["access_token"]
        try:
            decoded = jwt.decode(
                access_token, os.getenv("JWT_SECRET"), algorithms=["HS256"]
            )

            user = (
                User.objects.select_related("profile")
                .filter(id=decoded.get("id"))
                .first()
            )
            if not user:
                return ErrorResponse(
                    message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
                )
            if not token_is_current(decoded, user):
                return ErrorResponse(
                    message="Invalid access token",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            request.user = user
            is_tfa_verified = decoded.get("is_tfa_verified") is True
            request.is_tfa_verified = is_tfa_verified
            if (
                user.profile.is_tfa_enabled
                and not is_tfa_verified
                and not allow_unverified_tfa
            ):
                return SuccessResponse(
                    data={"user": UserSerializer(user).data, "is_tfa_verified": False},
                    message="Two factor authentication is enabled",
                )
            return view(request, *args, **kwargs)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return ErrorResponse(
                message="Invalid access token", status_code=status.HTTP_401_UNAUTHORIZED
            )

        except Exception:
            # Keep the traceback in the logs, not in the response.
            logger.exception("unhandled error in %s", request.path)
            return ErrorResponse(
                message="Something went wrong!, Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return _decorator
