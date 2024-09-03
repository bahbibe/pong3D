from .models import User, Profile
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
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]


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
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        avatar_url = data["avatar"]
        if data["auth_method"] == Profile.EMAIL:
            data["avatar"] = f"{os.getenv('API_URL')}/{avatar_url}"
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

    class Meta:
        model = Profile
        fields = ["avatar", "username"]
