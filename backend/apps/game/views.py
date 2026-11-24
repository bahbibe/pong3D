from django.shortcuts import render
from rest_framework.decorators import api_view
from apps.accounts.auth_utils import is_authenticated
from core.responses import SuccessResponse, ErrorResponse
from .serializers import (
    GameHistorySerializer,
    GameStatsSerializer,
    TournamentSerializer,
    TournamentParticipantsSerializer,
    GameSerializer,
    TournamentGameSerializer,
    LeaderboardSerializer,
)
from .models import Game
from .models import Tournament, Tournament_Participants, Tournament_Game
from apps.friends.models import Friendship
from django.db.models import Count, Q
from django.db import transaction
from .tournament import ensure_bracket
from django.core.exceptions import ValidationError
from django.db.models import F
from django.contrib.auth import get_user_model
from apps.accounts.serializers import UserSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.accounts.models import Notification
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


@api_view(["GET"])
@is_authenticated
def stats(request):
    user = request.user
    games = Game.objects.filter(
        Q(player1_id=user) | Q(player2_id=user), status=Game.FINISHED
    ).order_by("-id")
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

    return SuccessResponse(data=GameStatsSerializer(stats).data)


@api_view(["GET"])
@is_authenticated
def history(request):
    user = request.user
    games = Game.objects.filter(
        Q(player1_id=user) | Q(player2_id=user), status=Game.FINISHED
    ).order_by("-id")

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
            "games": GameHistorySerializer(games, many=True).data,
            "stats": GameStatsSerializer(stats).data,
        }
    )


@api_view(["GET"])
@is_authenticated
def get_leaderboard(request):
    # Two queries in total (was two per user): count finished games and
    # wins per user in Python.
    totals = {}
    wins = {}
    finished = Game.objects.filter(status=Game.FINISHED).values_list(
        "player1_id", "player2_id", "winner_id"
    )
    for player1_id, player2_id, winner_id in finished:
        for player_id in (player1_id, player2_id):
            if player_id is not None:
                totals[player_id] = totals.get(player_id, 0) + 1
        if winner_id is not None:
            wins[winner_id] = wins.get(winner_id, 0) + 1

    users = list(User.objects.select_related("profile"))
    for user in users:
        user.total_games = totals.get(user.id, 0)
        user.total_wins = wins.get(user.id, 0)
        user.total_losses = user.total_games - user.total_wins
        user.ratio = (
            (user.total_wins / user.total_games) * 100 if user.total_games else 0
        )
    users.sort(key=lambda user: user.ratio, reverse=True)

    return SuccessResponse(
        data={
            "users": LeaderboardSerializer(users, many=True).data,
        }
    )


@api_view(["POST"])
@is_authenticated
def create_tournament(request):
    with transaction.atomic():
        tournament = Tournament.objects.create(owner=request.user)
        ensure_bracket(tournament)
    return SuccessResponse(
        data={
            "message": "tournament created successfuly",
            "data": TournamentSerializer(tournament).data,
        }
    )


@api_view(["GET"])
@is_authenticated
def get_tournaments(request):
    # Free seats = empty player slots in the first round (t_round=2),
    # counted in the same query as the list.
    first_round = Q(tournament_game__t_round=2)
    tournaments = (
        Tournament.objects.filter(finished=False)
        .select_related("owner__profile")
        .annotate(
            spots=Count(
                "tournament_game",
                filter=first_round & Q(tournament_game__game__player1=None),
            )
            + Count(
                "tournament_game",
                filter=first_round & Q(tournament_game__game__player2=None),
            )
        )
        .order_by("id")
    )
    return SuccessResponse(
        data={
            "data": TournamentSerializer(tournaments, many=True).data,
        }
    )


@api_view(["GET"])
@is_authenticated
def get_tournament_games(request, tournament_id):
    try:
        tournament = Tournament.objects.get(uuid=tournament_id)
    except (Tournament.DoesNotExist, ValidationError):
        return ErrorResponse(message="Tournament not found", status_code=404)
    games = Tournament_Game.objects.select_related("game").filter(tournament=tournament)
    return SuccessResponse(
        data={"data": TournamentGameSerializer(games, many=True).data}
    )


@api_view(["GET"])
@is_authenticated
def get_game(request, game_id):
    try:
        game = Game.objects.get(id=game_id)
        return SuccessResponse(data={"game": GameSerializer(game).data})
    except Exception as error:
        logger.info("get_game %s: %s", game_id, error)
        return ErrorResponse(
            message="Game not found",
        )

@api_view(["POST"])
@is_authenticated
def invite_friend(request, friend_id):
    source_user = request.user
    target_user = User.objects.filter(id=friend_id).first() if str(friend_id).isdigit() else None
    is_friend = target_user is not None and Friendship.objects.filter(
        Q(source_user=target_user, target_user=source_user)
        | Q(source_user=source_user, target_user=target_user),
        status=Friendship.ACCEPTED,
    ).exists()
    if not is_friend:
        return ErrorResponse(message="You can only invite your friends.")
    try:
        game = Game.objects.create(
            player1 = source_user,
            player2 = target_user
        )
        notification = Notification.objects.create(
            user_id=target_user.id,
            message="invated you to a game",
            type="game_invite",
            sender_id=source_user.id,
            game_id = game.id
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{target_user.id}",
            {
                "type": "send_notification",
                "notification_uuid": str(notification.uuid),
                "message": "invated you to a game",
                "user_id": target_user.id,
                "sender_id": source_user.id,
                "sender_uuid": str(source_user.profile.uuid),
                "sender_username": source_user.username,
                "sender_avatar": str(source_user.profile.avatar),
                "ctx": "game_invite",
                "game_id": game.id
            },
        )
        return SuccessResponse(data={"game": GameSerializer(game).data})
    except Exception:
        logger.exception("could not create game invite")
        return ErrorResponse(message="Could not create the game, please try again.")

@api_view(["POST"])
@is_authenticated
def play_again(request, game_id):
    try:
        prev_game = Game.objects.get((Q(player1=request.user) 
                    | Q(player2=request.user)), id=game_id)
        target_user = prev_game.player1 if prev_game.player2 == request.user else prev_game.player2
        if target_user is None:
            return ErrorResponse(message="This game has no opponent to invite.")
        source_user = request.user
        game = Game.objects.create(
            player1 = source_user,
            player2 = target_user
        )
        notification = Notification.objects.create(
            user_id=target_user.id,
            message="invated you to a game",
            type="game_invite",
            sender_id=source_user.id,
            game_id = game.id
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{target_user.id}",
            {
                "type": "send_notification",
                "notification_uuid": str(notification.uuid),
                "message": "invated you to a game",
                "user_id": target_user.id,
                "sender_id": source_user.id,
                "sender_uuid": str(source_user.profile.uuid),
                "sender_username": source_user.username,
                "sender_avatar": str(source_user.profile.avatar),
                "ctx": "game_invite",
                "game_id": game.id
            },
        )
        return SuccessResponse(data={"game": GameSerializer(game).data})
    except Exception:
        logger.exception("could not create game invite")
        return ErrorResponse(message="Could not create the game, please try again.")