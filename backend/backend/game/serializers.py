from rest_framework import serializers
from .models import Game, Tournament
from api.serializers import UserSerializer
import os
from api.models import Profile


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


class LeaderboardSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    total_games = serializers.IntegerField()
    total_wins = serializers.IntegerField()
    total_losses = serializers.IntegerField()
    ratio = serializers.IntegerField()

    def get_user(self, obj):
        avatar = obj.profile.avatar
        if obj.profile.auth_method == Profile.EMAIL:
            avatar = f"{os.getenv('API_URL')}/{avatar}"

        return {
            "id": obj.id,
            "username": obj.username,
            "avatar": str(avatar),
        }

    class Meta:
        model = Game
        fields = [
            "user",
            "total_games",
            "total_wins",
            "total_losses",
            "ratio",
        ]


class TournamentSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField()
    owner = UserSerializer(read_only=True)
    spots = serializers.IntegerField(default=4)
    finished = serializers.BooleanField()

    class Meta:
        model = Tournament
        fields = ["uuid", "owner", "spots", "finished"]


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
    id = serializers.IntegerField()
    uuid = serializers.CharField()
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    player1_score = serializers.IntegerField()
    player2_score = serializers.IntegerField()

    class Meta:
        model = Game
        fields = [
            "id",
            "uuid",
            "player1",
            "player2",
            "player1_score",
            "player2_score",
        ]


class TournamentGameSerializer(serializers.ModelSerializer):
    tournament = TournamentSerializer()
    game = GameSerializer()
    t_round = serializers.IntegerField()

    class Meta:
        model = Game
        fields = ["tournament", "game", "t_round"]
