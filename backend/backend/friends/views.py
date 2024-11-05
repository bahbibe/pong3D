from rest_framework.decorators import api_view
from .models import Friendship
from rest_framework import status
from django.db.models import Q
from .serializers import (
    ViewFriendshipSerializer,
    SentFriendRequestSerializer,
    AcceptFriendRequestSerializer,
    FriendshipSerializer,
    UpdateFriendshipSerializer,
    BlockUserSerializer,
)
from api.auth_utils import is_authenticated
from utils.responses import ErrorResponse, SuccessResponse


@api_view(["GET"])
@is_authenticated
def get_friends(request):
    user = request.user
    friends = Friendship.objects.filter(
        (Q(source_user=user) | Q(target_user=user))
        & (Q(status="accepted") | Q(status="blocked"))
    )
    for friendship in friends:
        if friendship.source_user == user:
            friendship.user = friendship.source_user
            friendship.friend = friendship.target_user
        else:
            friendship.user = friendship.target_user
            friendship.friend = friendship.source_user
    friends_filtered = []
    for friendship in friends:
        if friendship.status == "blocked" and friendship.blocked_by != user:
            continue
        friends_filtered.append(friendship)
    friends = [
        ViewFriendshipSerializer(friendship).data for friendship in friends_filtered
    ]

    return SuccessResponse(data=friends)


@api_view(["GET"])
@is_authenticated
def get_friends_request(request):
    user = request.user
    friends_request = Friendship.objects.filter(target_user=user, status="pending")

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

    return SuccessResponse(data=friends_request)

@api_view(["GET"])
@is_authenticated
def get_sent_friends_request(request):
    user = request.user
    friends_request = Friendship.objects.filter(source_user=user, status="pending")

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

    return SuccessResponse(data=friends_request)


@api_view(["POST"])
@is_authenticated
def send_friend_request(request):
    source_user = request.user
    serializer = SentFriendRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)

    target_user = serializer.validated_data["target_user"]
    is_friendship_exist = (
        Friendship.objects.filter(
            source_user=source_user, target_user=target_user
        ).exists()
        or Friendship.objects.filter(
            source_user=target_user, target_user=source_user
        ).exists()
    )
    if source_user == target_user:
        return ErrorResponse(
            message="You cannot send a friend request to yourself",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if is_friendship_exist:
        return ErrorResponse(
            message="Friendship already exists",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friendship = Friendship.objects.create(
        source_user=source_user, target_user=target_user
    )

    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@api_view(["POST"])
@is_authenticated
def accept_friend_request(request):
    user = request.user
    serializer = AcceptFriendRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)

    source_user = serializer.validated_data["source_user"]
    friendship = Friendship.objects.filter(
        source_user=source_user, target_user=user
    ).first()
    if not friendship:
        return ErrorResponse(
            message="Friend request does not exist",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friendship.status = "accepted"
    friendship.save()

    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@api_view(["PUT"])
@is_authenticated
def update_friendship_status(request):
    user = request.user
    serializer = UpdateFriendshipSerializer(data=request.data)

    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)

    friend_id = serializer.validated_data["friend_id"]
    friendship = Friendship.objects.filter(
        Q(source_user=user, target_user=friend_id)
        | Q(source_user=friend_id, target_user=user)
    ).first()

    if not friendship:
        return ErrorResponse(
            message="Friendship does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if serializer.validated_data["status"] == "blocked":
        friendship.status = "blocked"
        friendship.blocked_by = user
        friendship.save()
        return SuccessResponse(data=FriendshipSerializer(friendship).data)

    friendship.status = serializer.validated_data["status"]
    friendship.save()

    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@api_view(["POST"])
@is_authenticated
def block_user(request):
    user = request.user
    serializer = BlockUserSerializer(data=request.data)

    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)

    if user == serializer.validated_data["user_id"]:
        return ErrorResponse(
            message="You cannot block yourself",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user_id = serializer.validated_data["user_id"]
    friendship = Friendship.objects.filter(
        Q(source_user=user, target_user=user_id)
        | Q(source_user=user_id, target_user=user)
    ).first()

    if not friendship:
        Friendship.objects.create(
            source_user=user, target_user=user_id, status="blocked", blocked_by=user
        )
        return SuccessResponse(message="User blocked successfully")

    friendship.status = "blocked"
    friendship.blocked_by = user
    friendship.save()
    return SuccessResponse(message="User blocked successfully")


@api_view(["POST"])
@is_authenticated
def unblock_user(request):
    user = request.user
    serializer = BlockUserSerializer(data=request.data)

    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)

    user_id = serializer.validated_data["user_id"]
    friendship = Friendship.objects.filter(
        Q(source_user=user, target_user=user_id)
        | Q(source_user=user_id, target_user=user)
    ).first()

    if not friendship:
        return ErrorResponse(
            message="Friendship does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if friendship.blocked_by != user:
        return ErrorResponse(
            message="User is not blocked by you",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if friendship.status != "blocked":
        return ErrorResponse(
            message="User is not blocked",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friendship.delete()
    return SuccessResponse(message="User unblocked successfully")
