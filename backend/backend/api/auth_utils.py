import functools
import jwt
import os
from datetime import datetime
from django.conf import settings
from django.http.request import HttpRequest
from rest_framework import status
from .models import User
from utils.responses import ErrorResponse, SuccessResponse
from .serializers import UserSerializer


def generate_token(payload):
    encoded_jwt = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    return encoded_jwt


def set_access_token(response, user, is_tfa_verified):
    """Issue a new access token for `user` and store it in the auth cookie."""
    access_token_liftime = datetime.now() + settings.ACCESS_TOKEN_LIFETIME
    access_token = generate_token(
        {
            "id": user.id,
            "is_tfa_verified": is_tfa_verified,
            "exp": access_token_liftime,
        }
    )
    response.set_cookie(
        "access_token", access_token, httponly=True, expires=access_token_liftime
    )
    return response


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

            user = User.objects.filter(id=decoded.get("id")).first()
            if not user:
                return ErrorResponse(
                    message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
                )

            request.user = user
            is_tfa_verified = decoded.get("is_tfa_verified") is True
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

        except Exception as e:
            return ErrorResponse(
                message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return _decorator
