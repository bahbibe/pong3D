from django.shortcuts import render
from rest_framework.decorators import api_view
from api.auth_utils import is_authenticated
from utils.responses import SuccessResponse, ErrorResponse
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
from friends.models import Friendship
from django.db.models import Q
from django.db.models import F
from api.models import User
from api.serializers import UserSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import Notification
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@is_authenticated
def stats(request):
    user = request.user
    games = Game.objects.filter((Q(player1_id=user) | Q(player2_id=user))).order_by(
        "-id"
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

    return SuccessResponse(data=GameStatsSerializer(stats).data)


@api_view(["GET"])
@is_authenticated
def history(request):
    user = request.user
    games = Game.objects.filter((Q(player1_id=user) | Q(player2_id=user))).order_by(
        "-id"
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
            "games": GameHistorySerializer(games, many=True).data,
            "stats": GameStatsSerializer(stats).data,
        }
    )


@api_view(["GET"])
@is_authenticated
def get_leaderboard(request):
    users = User.objects.all()
    for user in users:
        games = Game.objects.filter(Q(player1_id=user) | Q(player2_id=user))
        total_games = games.count()
        total_wins = games.filter(
            Q(player1_id=user, player1_score__gt=F("player2_score"))
            | Q(player2_id=user, player2_score__gt=F("player1_score"))
        ).count()
        total_losses = total_games - total_wins
        ratio = (total_wins / total_games) * 100 if total_games > 0 else 0
        user.total_games = total_games
        user.total_wins = total_wins
        user.total_losses = total_losses
        user.ratio = ratio
    users = sorted(users, key=lambda x: x.ratio, reverse=True)

    return SuccessResponse(
        data={
            "users": LeaderboardSerializer(users, many=True).data,
        }
    )


@api_view(["POST"])
@is_authenticated
def create_tournament(request):
    tournament = Tournament.objects.create(
        owner=request.user,
    )
    print(tournament.owner.id)
    # start the tournament
    # only if the request user is the tournament owner
    return SuccessResponse(
        data={
            "message": "tournament created successfuly",
            "data": TournamentSerializer(tournament).data,
        }
    )


@api_view(["GET"])
@is_authenticated
def get_tournaments(request):
    tournaments = Tournament.objects.all()
    for tournament in tournaments:
        player1_spots = Tournament_Game.objects.filter(
            tournament=tournament, game__player1=None, t_round=2
        ).count()
        player2_spots = Tournament_Game.objects.filter(
            tournament=tournament, game__player2=None, t_round=2
        ).count()
        spots = player1_spots + player2_spots
        tournament.spots = spots
    return SuccessResponse(
        data={
            "data": TournamentSerializer(tournaments, many=True).data,
        }
    )


@api_view(["GET"])
@is_authenticated
def get_tournament_games(request, tournament_id):
    tournament = Tournament.objects.get(uuid=tournament_id)
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
        print(error)
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
        Notification.objects.create(
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
        source_user = request.user
        game = Game.objects.create(
            player1 = source_user,
            player2 = target_user
        )
        Notification.objects.create(
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