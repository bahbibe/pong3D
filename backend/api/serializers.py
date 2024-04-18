from .models import User, Profile
from rest_framework import serializers


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "password", "avatar"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["avatar"]


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(source="profile.avatar.url")

    class Meta:
        model = User
        fields = ["username", "email", "avatar"]
