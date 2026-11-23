from .models import User, Profile, Notification
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
import os


def username_field(required):
    # Same rules as Django's User.username (letters, digits and @.+-_ only).
    # The serializer fields below replace the model field, so the model
    # validators are not applied unless we add them here.
    return serializers.CharField(
        required=required,
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )


def check_password_strength(password, user):
    """Run AUTH_PASSWORD_VALIDATORS and turn errors into a serializer error."""
    try:
        validate_password(password, user=user)
    except DjangoValidationError as error:
        raise serializers.ValidationError({"password": list(error.messages)})


class LoginUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["email", "password", "username"]


class RegisterUserSerializer(serializers.ModelSerializer):
    username = username_field(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
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

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        candidate = User(
            username=data["username"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        check_password_strength(data["password"], candidate)
        return data


class SetupProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)
    username = username_field(required=False)

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
    """The logged-in user's own data (includes email)."""

    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        depth = 1
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]


class PublicUserSerializer(UserSerializer):
    """Another user as seen by others: same shape, no email."""

    class Meta(UserSerializer.Meta):
        fields = ["id", "username", "first_name", "last_name", "profile"]


class UpdateSettingsSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)
    username = username_field(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    confirm_password = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    current_password = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )

    class Meta:
        model = Profile
        fields = [
            "avatar",
            "username",
            "email",
            "password",
            "confirm_password",
            "current_password",
        ]

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if password and confirm_password is not None and password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        return data


class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    def get_sender(self, obj):
        if obj.sender is None:  # system notification
            return None
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
