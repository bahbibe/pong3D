"""Profile setup, settings, profiles and user search. The rules live in
services.py and selectors.py."""

from rest_framework.decorators import api_view

from apps.game.selectors import finished_games
from apps.game.selectors import history as game_history
from apps.game.selectors import stats as game_stats
from apps.game.serializers import GameHistorySerializer, GameStatsSerializer
from core.responses import ErrorResponse, SuccessResponse

from . import selectors, services
from .auth_utils import revoke_tokens, set_access_token
from .authentication import is_tfa_verified
from .serializers import (
    PublicUserSerializer,
    SetupProfileSerializer,
    UpdateSettingsSerializer,
    UserSerializer,
)


@api_view(["POST"])
def setup_profile(request):
    serializer = SetupProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    user = services.setup_profile(request.user, serializer.validated_data)
    return SuccessResponse(data=UserSerializer(user).data)


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


@api_view(["GET"])
def get_profile_with_id(request, id):
    user = selectors.user_by_profile_id(id, viewer=request.user)
    return SuccessResponse(data=PublicUserSerializer(user).data)


@api_view(["GET"])
def get_users(request):
    # Search by username only, and never return emails of other users.
    users = selectors.search_users(request.user, request.GET.get("q"))
    return SuccessResponse(data=PublicUserSerializer(users, many=True).data)
