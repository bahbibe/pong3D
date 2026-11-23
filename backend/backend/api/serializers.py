from .models import User, Profile, Notification
from rest_framework import serializers
import os


class LoginUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["email", "password", "username"]

        def validate(self, data):
            email = data.get("email")
            username = data.get("username")
            password = data.get("password")
            if email is None and username is None:
                raise serializers.ValidationError(
                    "An email or username is required to log in."
                )
            if email is not None and username is not None:
                raise serializers.ValidationError(
                    "You can only use either email or username to log in."
                )
            if password is None:
                raise serializers.ValidationError("A password is required to log in.")
            return data


class RegisterUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "confirm_password",
        ]


class SetupProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = ["avatar", "username"]


class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField()

    class Meta:
        model = Profile
        fields = [
            "avatar",
            "is_setup",
            "total_wins",
            "total_losses",
            "uuid",
            "auth_method",
            "is_tfa_enabled",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["avatar"] = (
            "cdn.intra.42.fr" in data["avatar"]
            and data["avatar"]
            or f"{os.getenv('API_URL')}/{data['avatar']}"
        )
        return data


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        depth = 1
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]


class UpdateSettingsSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = ["avatar", "username", "email", "password"]


class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    def get_sender(self, obj):
        avatar = str(obj.sender.profile.avatar)
        avatar_url = (
            "cdn.intra.42.fr" in avatar
            and avatar
            or f"{os.getenv('API_URL')}/{avatar}"
        )
        return {
            "id": obj.sender.id,
            "username": obj.sender.username,
            "avatar": avatar_url,
            "uuid": str(obj.sender.profile.uuid),
        }

    class Meta:
        model = Notification
        fields = ["uuid", "type", "message", "is_read", "created_at", "sender", "game_id"]
