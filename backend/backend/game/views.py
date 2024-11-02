from django.shortcuts import render
from rest_framework.decorators import api_view
from api.auth_utils import is_authenticated
from utils.responses import SuccessResponse, ErrorResponse
from .serializers import GameHistorySerializer, GameStatsSerializer
from .models import Game
from django.db.models import Q
from django.db.models import F


# Create your views here.
def index(request):
    return render(request, "game/index.html")


def game(request, game_id):
    return render(request, "game/game.html", {"game_id": game_id})


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
