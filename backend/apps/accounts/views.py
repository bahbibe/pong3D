"""Profile setup, settings, profiles and user search. The rules live in
services.py and selectors.py."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view

from apps.game.selectors import finished_games
from apps.game.selectors import history as game_history
from apps.game.selectors import stats as game_stats
from apps.game.serializers import GameHistorySerializer, GameStatsSerializer
from core.responses import ErrorResponse, SuccessResponse
from core.schema import data_object, responses

from . import selectors, services
from .auth_utils import revoke_tokens, set_access_token
from .authentication import is_tfa_verified
from .serializers import (
    PublicUserSerializer,
    SetupProfileSerializer,
    UpdateSettingsSerializer,
    UserSerializer,
)


@extend_schema(
    tags=["profile"],
    summary="First setup: username and avatar (multipart)",
    request={"multipart/form-data": SetupProfileSerializer},
    responses=responses("Setup", UserSerializer),
)
@api_view(["POST"])
def setup_profile(request):
    serializer = SetupProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    user = services.setup_profile(request.user, serializer.validated_data)
    return SuccessResponse(data=UserSerializer(user).data)


@extend_schema(
    tags=["profile"],
    summary="Change username, email, password or avatar (multipart)",
    description="A new password ends every other session; this one gets a new cookie.",
    request={"multipart/form-data": UpdateSettingsSerializer},
    responses=responses("Settings", UserSerializer),
)
@api_view(["PUT"])
def update_settings(request):
    serializer = UpdateSettingsSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    user = request.user
    password_changed = services.update_settings(user, serializer.validated_data)
    response = SuccessResponse(data=UserSerializer(user).data)
    if password_changed:
        # Sign out every other session, then give this one a fresh token.
        revoke_tokens(user)
        set_access_token(response, user, is_tfa_verified=is_tfa_verified(request.auth))
    return response


@extend_schema(
    tags=["profile"],
    summary="Another player's profile, stats and match history",
    responses=responses(
        "Profile",
        data_object(
            "ProfileData",
            user=PublicUserSerializer(),
            stats=GameStatsSerializer(),
            history=GameHistorySerializer(many=True),
        ),
        errors=(401, 404),
    ),
)
@api_view(["GET"])
def get_profile(request, uuid):
    user = selectors.user_by_profile_uuid(uuid, viewer=request.user)
    games = list(finished_games(user))
    return SuccessResponse(
        data={
            "user": PublicUserSerializer(user).data,
            "stats": GameStatsSerializer(game_stats(user, games)).data,
            "history": GameHistorySerializer(game_history(user, games), many=True).data,
        }
    )


@extend_schema(
    tags=["profile"],
    summary="A player by user id",
    responses=responses("ProfileById", PublicUserSerializer, errors=(401, 404)),
)
@api_view(["GET"])
def get_profile_with_id(request, id):
    user = selectors.user_by_profile_id(id, viewer=request.user)
    return SuccessResponse(data=PublicUserSerializer(user).data)


@extend_schema(
    tags=["profile"],
    summary="Search players by username (at most 50)",
    parameters=[OpenApiParameter("q", str, description="Part of a username")],
    responses=responses("Users", PublicUserSerializer, many=True, errors=(401,)),
)
@api_view(["GET"])
def get_users(request):
    # Search by username only, and never return emails of other users.
    users = selectors.search_users(request.user, request.GET.get("q"))
    return SuccessResponse(data=PublicUserSerializer(users, many=True).data)
