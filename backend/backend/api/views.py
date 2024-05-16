from rest_framework.decorators import api_view
from .serializers import (
    SetupProfileSerializer,
    UserSerializer,
    UpdateSettingsSerializer,
)
from rest_framework import status
from .models import User, Profile
from django.db.models import Q
from api.auth_utils import is_authenticated
from utils.responses import SuccessResponse, ErrorResponse


@api_view(["PUT"])
@is_authenticated
def setup_profile(request):
    user = request.user
    serializer = SetupProfileSerializer(data=request.data)

    if serializer.is_valid():
        profile = user.profile
        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        profile.is_setup = True
        profile.save()
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
def get_profile(_, uuid):
    try:
        profile = Profile.objects.filter(uuid=uuid).first()
        if not profile:
            return ErrorResponse(
                message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
            )

        user = profile.user
        return SuccessResponse(data=UserSerializer(user).data)

    except Exception as e:
        return ErrorResponse(
            message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
@is_authenticated
def get_users(request):
    query = request.GET.get("q")
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )
        return SuccessResponse(data=UserSerializer(users, many=True).data)

    users = User.objects.all()
    return SuccessResponse(data=UserSerializer(users, many=True).data)
