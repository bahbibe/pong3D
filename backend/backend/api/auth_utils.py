import jwt
import os
from django.http.request import HttpRequest
from rest_framework import status
from .models import User
from utils.responses import ErrorResponse


def generate_token(payload):
    encoded_jwt = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    return encoded_jwt


def is_authenticated(view):
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

            user = User.objects.filter(id=decoded["id"]).first()
            if not user:
                return ErrorResponse(
                    message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
                )

            request.user = user
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
