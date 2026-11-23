from .models import Friendship
from api.models import User
from api.serializers import PublicUserSerializer
from rest_framework import serializers


class SentFriendRequestSerializer(serializers.ModelSerializer):
    target_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )

    class Meta:
        model = Friendship
        fields = ["target_user"]


class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    source_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )

    class Meta:
        model = Friendship
        fields = ["source_user"]


class FriendshipSerializer(serializers.ModelSerializer):
    source_user = PublicUserSerializer(read_only=True)
    target_user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ["source_user", "target_user", "status"]


class ViewFriendshipSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    friend = PublicUserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ["user", "friend", "status", "uuid"]


class BlockUserSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )

    class Meta:
        model = Friendship
        fields = ["user_id"]