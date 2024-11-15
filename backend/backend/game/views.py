from django.shortcuts import render
from rest_framework.decorators import api_view
from api.auth_utils import is_authenticated
from utils.responses import SuccessResponse, ErrorResponse
from .serializers import GameHistorySerializer, GameStatsSerializer, TournamentSerializer, TournamentParticipantsSerializer
from .models import Game
from .models import Tournament, Tournament_Participants, Tournament_Game
from django.db.models import Q
from django.db.models import F

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
    Tournament_Participants.objects.create(
        tournament = tournament,
        player = request.user,
    )
    print(tournament.owner.id)
    # start the tournament
    # only if the request user is the tournament owner
    return SuccessResponse(
        data={
            "message": "tournament created successfuly",
            "data": TournamentSerializer(tournament).data , 
        }
    )

@api_view(["GET"])
@is_authenticated
def get_tournaments(request):
    tournaments = Tournament.objects.all()
    for tournament in tournaments:
        tournament.is_participant = Tournament_Participants.objects.filter(player=request.user, tournament=tournament).exists()
    return SuccessResponse(
        data={
            "data": TournamentSerializer(tournaments, many=True).data,
        }
    )

@api_view(["GET"])
@is_authenticated
def join_tournament(request, tournament_id):
    tournament = Tournament.objects.get(uuid=tournament_id)
    if not tournament:
        return ErrorResponse(
            message= "Tournament doesn't exist!",
        )
    participant_count = Tournament_Participants.objects.filter(tournament=tournament).count()
    if participant_count >= 4:
        return ErrorResponse(
            message="tournament is full",
        )
    participant = Tournament_Participants.objects.filter(player=request.user).filter(tournament=tournament).first()
    if not participant:
        print(tournament_id)
        participant = Tournament_Participants.objects.create(
            tournament = tournament,
            player = request.user,
        )
    return SuccessResponse(
        data={
            "message": "tournament joined successfuly",
            "data": TournamentParticipantsSerializer(participant).data
        }
    )

@api_view(["GET"])
@is_authenticated
def get_participants(request, tournament_id):
    tournament = Tournament.objects.get(uuid=tournament_id)
    participant = Tournament_Participants.objects.filter(tournament=tournament)
    return SuccessResponse(
        data={ 
            "data": TournamentParticipantsSerializer(participant, many=True).data
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
