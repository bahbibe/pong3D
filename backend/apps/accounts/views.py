from rest_framework.decorators import api_view
from .serializers import (
    SetupProfileSerializer,
    PublicUserSerializer,
    UserSerializer,
    UpdateSettingsSerializer,
)
from rest_framework import status
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from .models import Profile
from django.db.models import Q, F
from apps.accounts.auth_utils import revoke_tokens, set_access_token
from apps.accounts.authentication import is_tfa_verified
from apps.accounts.auth_views import email_taken
from django.db import IntegrityError, transaction
from core.responses import SuccessResponse, ErrorResponse
from core.uuids import parse_uuid
from apps.friends.selectors import blocked_user_ids, is_blocked
from apps.game.models import Game
from apps.game.serializers import GameStatsSerializer, GameHistorySerializer

User = get_user_model()


@api_view(["POST"])
def setup_profile(request):
    user = request.user
    serializer = SetupProfileSerializer(data=request.data)

    if serializer.is_valid():
        is_username_exists = (
            User.objects.exclude(id=user.id)
            .filter(username=serializer.validated_data.get("username"))
            .exists()
        )
        if is_username_exists:
            return ErrorResponse(
                message="Username already exists, Please try another one."
            )

        profile = user.profile
        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        profile.is_setup = True
        user.username = serializer.validated_data.get("username", user.username)
        profile.save(update_fields=["avatar", "is_setup"])
        user.save()
        return SuccessResponse(data=UserSerializer(user).data)

    return ErrorResponse(serializer_errors=serializer.errors)


@api_view(["PUT"])
def update_settings(request):
    user = request.user
    serializer = UpdateSettingsSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)

    data = serializer.validated_data
    profile = user.profile
    username = data.get("username")
    email = data.get("email") or None
    password = data.get("password") or None
    current_password = data.get("current_password") or ""

    is_email_change = email is not None and email.lower() != user.email.lower()
    if password or is_email_change:
        # Changing credentials needs proof that the caller is the account
        # owner, not just someone holding the session cookie.
        if profile.auth_method == Profile.INTRA or not user.has_usable_password():
            return ErrorResponse(
                message="Email and password are managed by 42 intra for this account."
            )
        if not user.check_password(current_password):
            return ErrorResponse(
                message="Current password is incorrect.",
                serializer_errors={"current_password": ["Current password is incorrect."]},
            )

    if (
        username
        and username != user.username
        and User.objects.filter(username=username).exists()
    ):
        return ErrorResponse(message="Username already exists")

    if is_email_change and email_taken(email, exclude_user=user):
        return ErrorResponse(message="Email already exists")

    if password:
        try:
            validate_password(password, user=user)
        except DjangoValidationError as error:
            return ErrorResponse(
                message="Invalid password",
                serializer_errors={"password": list(error.messages)},
            )

    profile.avatar = data.get("avatar", profile.avatar)
    if username:
        user.username = username
    if is_email_change:
        user.email = email
    if password:
        user.set_password(password)

    try:
        with transaction.atomic():
            profile.save(update_fields=["avatar"])
            user.save()
    except IntegrityError:
        # Username or email taken by another request at the same moment.
        return ErrorResponse(message="Username or email already exists")
    response = SuccessResponse(data=UserSerializer(user).data)
    if password:
        # Sign out every other session, then give this one a fresh token.
        revoke_tokens(user)
        set_access_token(response, user, is_tfa_verified=is_tfa_verified(request.auth))
    return response


def user_not_found():
    return ErrorResponse(message="User does not exist", status_code=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def get_profile(request, uuid):
    profile_uuid = parse_uuid(uuid)
    profile = (
        Profile.objects.select_related("user").filter(uuid=profile_uuid).first()
        if profile_uuid
        else None
    )
    if not profile:
        return user_not_found()

    user = profile.user
    if is_blocked(user, request.user):
        return user_not_found()

    games = (
        Game.objects.filter(Q(player1_id=user) | Q(player2_id=user), status=Game.FINISHED)
        .select_related("player1__profile", "player2__profile")
        .order_by("-id")
    )
    total_games = games.count()
    total_wins = games.filter(
        Q(player1_id=user, player1_score__gt=F("player2_score"))
        | Q(player2_id=user, player2_score__gt=F("player1_score"))
    ).count()
    total_losses = total_games - total_wins
    ratio = (total_wins / total_games) * 100 if total_games > 0 else 0

    stats = {
        "total_games": total_games,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "ratio": ratio,
    }

    for game in games:
        if game.player1_id == user.id:
            game.user = game.player1
            game.user_score = game.player1_score
            game.player = game.player2
            game.player_score = game.player2_score
            game.is_user_winner = game.player1_score > game.player2_score
        else:
            game.user = game.player2
            game.user_score = game.player2_score
            game.player = game.player1
            game.player_score = game.player1_score
            game.is_user_winner = game.player2_score > game.player1_score

    return SuccessResponse(
        data={
            "user": PublicUserSerializer(user).data,
            "stats": GameStatsSerializer(stats).data,
            "history": GameHistorySerializer(games, many=True).data,
        }
    )


@api_view(["GET"])
def get_profile_with_id(request, id):
    profile = (
        Profile.objects.select_related("user").filter(id=id).first()
        if str(id).isdigit()
        else None
    )
    if not profile or is_blocked(profile.user, request.user):
        return user_not_found()
    return SuccessResponse(data=PublicUserSerializer(profile.user).data)


MAX_SEARCH_RESULTS = 50


@api_view(["GET"])
def get_users(request):
    # Search by username only, and never return emails of other users.
    users = (
        User.objects.exclude(id__in=blocked_user_ids(request.user))
        .select_related("profile")
        .order_by("username")
    )
    query = (request.GET.get("q") or "").strip()
    if query:
        users = users.filter(username__icontains=query)
    return SuccessResponse(
        data=PublicUserSerializer(users[:MAX_SEARCH_RESULTS], many=True).data
    )
