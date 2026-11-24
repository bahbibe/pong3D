from rest_framework.decorators import api_view

from core.responses import SuccessResponse

from . import selectors, services
from .serializers import (
    GameHistorySerializer,
    GameSerializer,
    GameStatsSerializer,
    LeaderboardSerializer,
    TournamentGameSerializer,
    TournamentSerializer,
)


@api_view(["GET"])
def stats(request):
    return SuccessResponse(data=GameStatsSerializer(selectors.stats(request.user)).data)


@api_view(["GET"])
def history(request):
    games = list(selectors.finished_games(request.user))
    return SuccessResponse(
        data={
            "games": GameHistorySerializer(selectors.history(request.user, games), many=True).data,
            "stats": GameStatsSerializer(selectors.stats(request.user, games)).data,
        }
    )


@api_view(["GET"])
def get_leaderboard(request):
    return SuccessResponse(
        data={"users": LeaderboardSerializer(selectors.leaderboard(), many=True).data}
    )


@api_view(["POST"])
def create_tournament(request):
    tournament = services.create_tournament(request.user)
    return SuccessResponse(
        data={
            "message": "tournament created successfuly",
            "data": TournamentSerializer(tournament).data,
        }
    )


@api_view(["GET"])
def get_tournaments(request):
    return SuccessResponse(
        data={"data": TournamentSerializer(selectors.open_tournaments(), many=True).data}
    )


@api_view(["GET"])
def get_tournament_games(request, tournament_id):
    tournament = services.get_tournament(tournament_id)
    return SuccessResponse(
        data={
            "data": TournamentGameSerializer(selectors.tournament_games(tournament), many=True).data
        }
    )


@api_view(["GET"])
def get_game(request, game_id):
    return SuccessResponse(data={"game": GameSerializer(services.get_game(game_id)).data})


@api_view(["POST"])
def invite_friend(request, friend_id):
    game = services.invite_friend(request.user, friend_id)
    return SuccessResponse(data={"game": GameSerializer(game).data})


@api_view(["POST"])
def play_again(request, game_id):
    game = services.play_again(request.user, game_id)
    return SuccessResponse(data={"game": GameSerializer(game).data})
