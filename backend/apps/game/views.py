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


LEADERBOARD_PAGE_SIZE = 20
LEADERBOARD_MAX_PAGE_SIZE = 100


def _positive_int(value, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


@api_view(["GET"])
def get_leaderboard(request):
    """?page= (from 1) and ?size= (default 20, at most 100). Every row has
    its rank; "me" is the caller's rank and stats."""
    size = min(
        _positive_int(request.GET.get("size"), LEADERBOARD_PAGE_SIZE), LEADERBOARD_MAX_PAGE_SIZE
    )
    board = selectors.leaderboard_page(
        _positive_int(request.GET.get("page"), 1), size, viewer=request.user
    )
    return SuccessResponse(
        data={
            "users": LeaderboardSerializer(board["rows"], many=True).data,
            "page": board["page"],
            "pages": board["pages"],
            "size": board["size"],
            "total": board["total"],
            "me": board["me"] and {**board["me"], "ratio": int(board["me"]["ratio"])},
        }
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
