from .models import User, Profile, Freindship
from rest_framework import serializers


class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]


class SetupProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ["avatar"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["avatar", "is_setup", "total_wins", "total_losses"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        depth = 1
        fields = ["id", "username", "email", "profile"]


class SentFriendRequestSerializer(serializers.ModelSerializer):
    target_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )

    class Meta:
        model = Freindship
        fields = ["target_user"]


class AcceptFriendRequestSerializer(serializers.ModelSerializer):
    source_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )

    class Meta:
        model = Freindship
        fields = ["source_user"]


class FriendshipSerializer(serializers.ModelSerializer):
    source_user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)

    class Meta:
        model = Freindship
        fields = ["source_user", "target_user", "status"]


class ViewFriendshipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    friend = UserSerializer(read_only=True)

    class Meta:
        model = Freindship
        fields = ["user", "friend", "status"]
