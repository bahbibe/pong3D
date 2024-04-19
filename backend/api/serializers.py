from .models import User, Profile
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
