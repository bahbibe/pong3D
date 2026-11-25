from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view

from core.responses import SuccessResponse
from core.schema import data_object, responses

from . import selectors, services
from .serializers import (
    GameHistorySerializer,
    GameSerializer,
    GameStatsSerializer,
    LeaderboardSerializer,
    TournamentGameSerializer,
    TournamentSerializer,
)


@extend_schema(
    tags=["games"],
    summary="Your game stats",
    responses=responses("Stats", GameStatsSerializer, errors=(401,)),
)
@api_view(["GET"])
def stats(request):
    return SuccessResponse(data=GameStatsSerializer(selectors.stats(request.user)).data)


@extend_schema(
    tags=["games"],
    summary="Your finished games and stats",
    responses=responses(
        "History",
        data_object(
            "HistoryData", games=GameHistorySerializer(many=True), stats=GameStatsSerializer()
        ),
        errors=(401,),
    ),
)
@api_view(["GET"])
def history(request):
    games = list(selectors.finished_games(request.user))
    return SuccessResponse(
        data={
            "games": GameHistorySerializer(selectors.history(request.user, games), many=True).data,
            "stats": GameStatsSerializer(selectors.stats(request.user, games)).data,
        }
    )


GAME_DATA = data_object("GameData", game=GameSerializer())

LEADERBOARD_PAGE_SIZE = 20
LEADERBOARD_MAX_PAGE_SIZE = 100


def _positive_int(value, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


@extend_schema(
    tags=["games"],
    summary="One page of the leaderboard, best ratio first, with your rank",
    parameters=[
        OpenApiParameter("page", int, description="From 1; past the end gives the last page"),
        OpenApiParameter("size", int, description="Default 20, at most 100"),
    ],
    responses=responses(
        "Leaderboard",
        data_object(
            "LeaderboardPage",
            users=LeaderboardSerializer(many=True),
            page=serializers.IntegerField(),
            pages=serializers.IntegerField(),
            size=serializers.IntegerField(),
            total=serializers.IntegerField(),
            me=inline_serializer(
                "LeaderboardMe",
                {
                    "rank": serializers.IntegerField(),
                    "total_games": serializers.IntegerField(),
                    "total_wins": serializers.IntegerField(),
                    "total_losses": serializers.IntegerField(),
                    "ratio": serializers.IntegerField(),
                },
                allow_null=True,
            ),
        ),
        errors=(401,),
    ),
)
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


@extend_schema(
    tags=["tournaments"],
    summary="Create a tournament (4 players, the bracket is made on first join)",
    request=None,
    responses=responses(
        "CreateTournament",
        data_object(
            "CreatedTournament", message=serializers.CharField(), data=TournamentSerializer()
        ),
        errors=(400, 401),
    ),
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


@extend_schema(
    tags=["tournaments"],
    summary="Open tournaments, with free seats",
    responses=responses(
        "Tournaments",
        data_object("TournamentList", data=TournamentSerializer(many=True)),
        errors=(401,),
    ),
)
@api_view(["GET"])
def get_tournaments(request):
    return SuccessResponse(
        data={"data": TournamentSerializer(selectors.open_tournaments(), many=True).data}
    )


@extend_schema(
    tags=["tournaments"],
    summary="The games of a tournament's bracket",
    parameters=[
        OpenApiParameter("tournament_id", str, OpenApiParameter.PATH, description="Tournament uuid")
    ],
    responses=responses(
        "TournamentGames",
        data_object("TournamentGameList", data=TournamentGameSerializer(many=True)),
        errors=(401, 404),
    ),
)
@api_view(["GET"])
def get_tournament_games(request, tournament_id):
    tournament = services.get_tournament(tournament_id)
    return SuccessResponse(
        data={
            "data": TournamentGameSerializer(selectors.tournament_games(tournament), many=True).data
        }
    )


@extend_schema(
    tags=["games"],
    summary="One game",
    parameters=[OpenApiParameter("game_id", int, OpenApiParameter.PATH)],
    responses=responses("Game", GAME_DATA, errors=(400, 401)),
)
@api_view(["GET"])
def get_game(request, game_id):
    return SuccessResponse(data={"game": GameSerializer(services.get_game(game_id)).data})


@extend_schema(
    tags=["games"],
    summary="New game against a friend; they get a notification",
    request=None,
    parameters=[OpenApiParameter("friend_id", int, OpenApiParameter.PATH, description="User id")],
    responses=responses("Invite", GAME_DATA, errors=(400, 401)),
)
@api_view(["POST"])
def invite_friend(request, friend_id):
    game = services.invite_friend(request.user, friend_id)
    return SuccessResponse(data={"game": GameSerializer(game).data})


@extend_schema(
    tags=["games"],
    summary="New game against the opponent of one of your games",
    request=None,
    parameters=[OpenApiParameter("game_id", int, OpenApiParameter.PATH)],
    responses=responses("PlayAgain", GAME_DATA, errors=(400, 401)),
)
@api_view(["POST"])
def play_again(request, game_id):
    game = services.play_again(request.user, game_id)
    return SuccessResponse(data={"game": GameSerializer(game).data})
