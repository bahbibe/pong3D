from rest_framework import serializers
from .models import Tournament
from api.serializers import UserSerializer


class TournamentSerializer(serializers.ModelSerializer):
    # players = UserSerializer(many=True)
    created_by = UserSerializer()

    class Meta:
        model = Tournament
        depth = 1
        fields = [
            "uuid",
            "created_by",
            "created_at",
            # "players",
            "status",
            "current_participants",
            "winner",
            "max_participants",
        ]
