from django.shortcuts import render
from rest_framework.decorators import api_view
from api.auth_utils import is_authenticated
from utils.responses import SuccessResponse, ErrorResponse
from .serializers import GameHistorySerializer, GameStatsSerializer
from .models import Game
from .models import Tournament
from django.db.models import Q
from django.db.models import F

import redis
import uuid
import json

r = redis.Redis(host="redis", charset="utf-8", decode_responses=True)


# Create your views here.

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
def create_tournament(request):
    tournament = Tournament.objects.create(
        owner = request.user,
    )
    print(tournament.owner.id)
    # start the tournament
    # only if the request user is the tournament owner
    return SuccessResponse(
        data={
            "message": "tournament created successfuly",
            "tournament": "tournament"
        }
    )

@api_view(["GET"])
@is_authenticated
def start_tournament(request):
    pass
    # create a tournament in the database
    # set this request user as the tournament owner
    return SuccessResponse(
        data={
            "message": "tournament created successfuly",
            "tournament_id": tournament_id,
            "owner": request.user.id,
        }
    )

@api_view(["GET"])
@is_authenticated
def get_tournaments(request):
    pass
    # add this user to the tournament
    return SuccessResponse(
        data={
        }
    )

@api_view(["GET"])
@is_authenticated
def leave_tournament(request):
    pass
    # leave tournament if it didn't start yet
    # if the tournament already stated count as eleminated
    return SuccessResponse(
        data={
        }
    )

@api_view(["GET"])
@is_authenticated
def get_my_tournaments(request):
    pass
    # return only the tournaments that the request user has joined
    return SuccessResponse(
        data={
        }
    )