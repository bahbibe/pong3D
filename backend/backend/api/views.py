from rest_framework.decorators import api_view
from .serializers import (
    SetupProfileSerializer,
    UserSerializer,
    UpdateSettingsSerializer,
)
from rest_framework import status
from .models import User, Profile, Notification
from django.db.models import Q
from api.auth_utils import is_authenticated
from utils.responses import SuccessResponse, ErrorResponse
from friends.models import Friendship


@api_view(["POST"])
@is_authenticated
def setup_profile(request):
    user = request.user
    serializer = SetupProfileSerializer(data=request.data)

    if serializer.is_valid():
        is_username_exists = (
            User.objects.exclude(id=user.id)
            .filter(username=serializer.validated_data.get("username"))
            .exists()
        )
        if is_username_exists:
            return ErrorResponse(
                message="Username already exists, Please try another one."
            )

        profile = user.profile
        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        profile.is_setup = True
        user.username = serializer.validated_data.get("username", user.username)
        profile.save()
        user.save()
        return SuccessResponse(data=UserSerializer(user).data)

    return ErrorResponse(serializer_errors=serializer.errors)


@api_view(["PUT"])
@is_authenticated
def update_settings(request):
    user = request.user
    serializer = UpdateSettingsSerializer(data=request.data)
    if serializer.is_valid():
        profile = user.profile
        if User.objects.filter(
            username=serializer.validated_data.get("username")
        ).exists():
            return ErrorResponse(message="Username already exists")

        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        user.username = serializer.validated_data.get("username", user.username)
        profile.save()
        user.save()
        return SuccessResponse(data=UserSerializer(user).data)

    return ErrorResponse(serializer_errors=serializer.errors)


@api_view(["GET"])
@is_authenticated
def get_profile(request, uuid):
    try:
        profile = Profile.objects.filter(uuid=uuid).first()
        if not profile:
            return ErrorResponse(
                message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
            )

        user = profile.user
        if is_blocked(user, request.user):
            return ErrorResponse(
                message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
            )
        return SuccessResponse(data=UserSerializer(user).data)

    except Exception as e:
        return ErrorResponse(
            message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@is_authenticated
def get_profile_with_id(request, id):
    try:
        profile = Profile.objects.filter(id=id).first()
        if not profile:
            return ErrorResponse(
                message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
            )

        user = profile.user
        if is_blocked(user, request.user):
            return ErrorResponse(
                message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
            )
        return SuccessResponse(data=UserSerializer(user).data)

    except Exception as e:
        return ErrorResponse(
            message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
        )


def is_blocked(user, target_user):
    return Friendship.objects.filter(
        (Q(source_user=user) | Q(target_user=user))
        & (Q(source_user=target_user) | Q(target_user=target_user))
        & Q(status="blocked")
    ).exists()


@api_view(["GET"])
@is_authenticated
def get_users(request):
    current_user = request.user
    query = request.GET.get("q")
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )

        for user in users:
            if is_blocked(current_user, user):
                users = users.exclude(id=user.id)
        return SuccessResponse(data=UserSerializer(users, many=True).data)

    users = User.objects.all()
    for user in users:
        if is_blocked(current_user, user):
            users = users.exclude(id=user.id)
    return SuccessResponse(data=UserSerializer(users, many=True).data)

@api_view(["POST"])
@is_authenticated
def mark_all_notifications_as_read(request):
    user = request.user
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return SuccessResponse(message="All notifications marked as read")