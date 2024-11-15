from rest_framework import serializers
from .models import Game, Tournament
from api.serializers import UserSerializer


class GameStatsSerializer(serializers.ModelSerializer):
    total_games = serializers.IntegerField()
    total_wins = serializers.IntegerField()
    total_losses = serializers.IntegerField()
    ratio = serializers.IntegerField()

    class Meta:
        model = Game
        fields = ["total_games", "total_wins", "total_losses", "ratio"]


class GameHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    player = UserSerializer(read_only=True)
    player_score = serializers.IntegerField()
    user_score = serializers.IntegerField()
    is_user_winner = serializers.BooleanField()

    class Meta:
        model = Game
        fields = [
            "user",
            "player",
            "uuid",
            "player_score",
            "user_score",
            "is_user_winner",
        ]

class TournamentSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField()
    started = serializers.BooleanField()
    owner = UserSerializer(read_only=True)
    is_participant = serializers.BooleanField(default=False)

    class Meta:
        model = Tournament
        fields = [
            "uuid",
            "started",
            "owner",
            "is_participant",
        ]

class TournamentParticipantsSerializer(serializers.ModelSerializer):
    tournament = TournamentSerializer()
    player = UserSerializer(read_only=True)
    t_round = serializers.IntegerField()
    ready = serializers.BooleanField()
    
    class Meta:
        model = Tournament
        fields = [
            "tournament",
            "player",
            "t_round",
            "ready",
        ]

class GameSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField()
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    player1_score = serializers.IntegerField()
    player2_score = serializers.IntegerField()
    
    class Meta:
        model = Game
        fields = [
            "uuid",
            "player1",
            "player2",
            "player1_score",
            "player2_score",
        ]


class TournamentGameSerializer(serializers.ModelSerializer):
    tournament = TournamentSerializer()
    game = GameSerializer()

    class Meta:
        model = Game
        fields = [
            "tournament",
            "game",
        ]
