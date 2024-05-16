from django.shortcuts import render
from rest_framework.decorators import api_view
from api.auth_utils import is_authenticated
from .models import Tournament, TournamentPlayer
from utils.responses import SuccessResponse, ErrorResponse
from .serializers import TournamentSerializer
from rest_framework import status


@api_view(["POST"])
@is_authenticated
def create_tournament(request):
    user = request.user
    tournament = Tournament.objects.create(created_by=user)
    tournament.save()
    TournamentPlayer.objects.create(tournament=tournament, player=user)
    return SuccessResponse(
        data={"tournament": tournament.uuid}, message="Tournament created successfully"
    )


@api_view(["GET"])
@is_authenticated
def get_tournaments(_):
    tournaments = TournamentSerializer(Tournament.objects.all(), many=True).data
    return SuccessResponse(data=tournaments, message="Tournaments fetched successfully")


@api_view(["POST"])
@is_authenticated
def join_tournament(request, tournament_uuid):
    user = request.user
    tournament = Tournament.objects.filter(uuid=tournament_uuid).first()

    if not tournament:
        return ErrorResponse(
            message="Tournament not found", status_code=status.HTTP_404_NOT_FOUND
        )

    if tournament.status != "waiting":
        return ErrorResponse(
            message="Tournament is not waiting", status_code=status.HTTP_400_BAD_REQUEST
        )

    if tournament.current_participants >= tournament.max_participants:
        return ErrorResponse(
            message="Tournament is full", status_code=status.HTTP_400_BAD_REQUEST
        )

    if TournamentPlayer.objects.filter(tournament=tournament, player=user).exists():
        return ErrorResponse(
            message="You have already joined the tournament",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    TournamentPlayer.objects.create(tournament=tournament, player=user)
    tournament.current_participants += 1
    tournament.save()

    return SuccessResponse(message="You have joined the tournament successfully")


@api_view(["POST"])
@is_authenticated
def kick_player(request, tournament_uuid):
    user = request.user
    player_id = request.data.get("player_id")
    if not player_id:
        return ErrorResponse(
            message="Player id is required", status_code=status.HTTP_400_BAD_REQUEST
        )

    tournament = Tournament.objects.filter(uuid=tournament_uuid).first()

    if not tournament:
        return ErrorResponse(
            message="Tournament not found", status_code=status.HTTP_404_NOT_FOUND
        )

    if tournament.created_by != user:
        return ErrorResponse(
            message="You cannot kick players from this tournament",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if tournament.status != "waiting":
        return ErrorResponse(
            message="Tournament is not waiting", status_code=status.HTTP_400_BAD_REQUEST
        )

    player = TournamentPlayer.objects.filter(
        tournament=tournament, player_id=player_id
    ).first()

    if not player:
        return ErrorResponse(
            message="Player not found", status_code=status.HTTP_404_NOT_FOUND
        )

    if player.player == tournament.created_by:
        return ErrorResponse(
            message="You cannot kick yourself from the tournament",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    player.delete()
    tournament.current_participants -= 1
    tournament.save()

    return SuccessResponse(message="Player has been kicked successfully")
