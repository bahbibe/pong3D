from .models import User, Profile
from rest_framework import serializers


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
        fields = ["avatar", "is_setup", "total_wins", "total_losses", "uuid"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        depth = 1
        fields = ["id", "username", "email", "profile"]


class UpdateSettingsSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = Profile
        fields = ["avatar", "username"]
