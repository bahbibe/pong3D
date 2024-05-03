from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view
from .serializers import (
    SetupProfileSerializer,
    UserSerializer,
    SentFriendRequestSerializer,
    AcceptFriendRequestSerializer,
    FriendshipSerializer,
    ViewFriendshipSerializer,
    UpdateSettingsSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from .models import Freindship, User, Profile
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_friends(request):
    user = request.user
    friends = Freindship.objects.filter(
        (Q(source_user=user) | Q(target_user=user)) & Q(status="accepted")
    )
    for friendship in friends:
        if friendship.source_user == user:
            friendship.user = friendship.source_user
            friendship.friend = friendship.target_user
        else:
            friendship.user = friendship.target_user
            friendship.friend = friendship.source_user
    friends = [ViewFriendshipSerializer(friendship).data for friendship in friends]
    return Response(friends, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_friends_request(request):
    user = request.user
    friends_request = Freindship.objects.filter(target_user=user, status="pending")
    for friendship in friends_request:
        if friendship.source_user == user:
            friendship.user = friendship.source_user
            friendship.friend = friendship.target_user
        else:
            friendship.user = friendship.target_user
            friendship.friend = friendship.source_user
    friends_request = [
        ViewFriendshipSerializer(friendship).data for friendship in friends_request
    ]
    return Response(friends_request, status=status.HTTP_200_OK)


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
