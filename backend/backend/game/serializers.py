from rest_framework import serializers
from .models import Game
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
