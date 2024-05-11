import jwt
import os
from django.http.request import HttpRequest
from rest_framework.response import Response
from rest_framework import status
from .models import User


def generate_token(payload):
    encoded_jwt = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    return encoded_jwt


def is_authenticated(view):
    def _decorator(request: HttpRequest, *args, **kwargs):
        if "access_token" not in request.COOKIES:
            return Response(
                {"error": "No access token found"}, status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = request.COOKIES["access_token"]
        try:
            decoded = jwt.decode(
                access_token, os.getenv("JWT_SECRET"), algorithms=["HS256"]
            )
            # user = User.objects.get(id=decoded["id"])
            user = User.objects.filter(id=decoded["id"]).first()
            if not user:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )
            request.user = user
            return view(request, *args, **kwargs)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return _decorator
