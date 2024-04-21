from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view
from .serializers import (
    SetupProfileSerializer,
    UserSerializer,
    SentFriendRequestSerializer,
    AcceptFriendRequestSerializer,
    FriendshipSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from .models import Freindship
from django.http import JsonResponse


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_friend_request(request):
    source_user = request.user
    serializer = SentFriendRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    target_user = serializer.validated_data["target_user"]
    is_freindship_exists = (
        Freindship.objects.filter(
            source_user=source_user, target_user=target_user
        ).exists()
        or Freindship.objects.filter(
            source_user=target_user, target_user=source_user
        ).exists()
    )
    if source_user == target_user:
        return JsonResponse(
            {
                "success": False,
                "message": "You cannot send a friend request to yourself",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if is_freindship_exists:
        return JsonResponse(
            {
                "success": False,
                "message": "Friendship already exists",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    friendship = Freindship.objects.create(
        source_user=source_user, target_user=target_user
    )
    return Response(
        FriendshipSerializer(friendship).data, status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_friend_request(request):
    user = request.user
    serializer = AcceptFriendRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    source_user = serializer.validated_data["source_user"]
    friendship = Freindship.objects.filter(
        source_user=source_user, target_user=user
    ).first()
    if not friendship:
        return JsonResponse(
            {
                "success": False,
                "message": "Friend request does not exist",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    friendship.status = "accepted"
    friendship.save()
    return Response(FriendshipSerializer(friendship).data, status=status.HTTP_200_OK)
