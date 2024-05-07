from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view
from .serializers import (
    SetupProfileSerializer,
    UserSerializer,
    UpdateSettingsSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from .models import User, Profile
from django.http import JsonResponse
from django.db.models import Q


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def setup_profile(request):
    user = request.user
    serializer = SetupProfileSerializer(data=request.data)
    if serializer.is_valid():
        profile = user.profile
        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        profile.is_setup = True
        profile.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_settings(request):
    user = request.user
    serializer = UpdateSettingsSerializer(data=request.data)
    if serializer.is_valid():
        profile = user.profile
        if User.objects.filter(
            username=serializer.validated_data.get("username")
        ).exists():
            return JsonResponse(
                {
                    "success": False,
                    "message": "Username already exists",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        user.username = serializer.validated_data.get("username", user.username)
        profile.save()
        user.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request, uuid):
    try:
        profile = Profile.objects.filter(uuid=uuid).first()
        if not profile:
            return JsonResponse(
                {
                    "success": False,
                    "message": "User does not exist",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        user = profile.user
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": "User does not exist",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
