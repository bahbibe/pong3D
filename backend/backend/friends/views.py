from rest_framework.decorators import api_view
from .models import Friendship
from rest_framework import status
from django.db.models import Q
from .serializers import (
    ViewFriendshipSerializer,
    SentFriendRequestSerializer,
    AcceptFriendRequestSerializer,
    FriendshipSerializer,
    BlockUserSerializer,
)
from api.auth_utils import is_authenticated
from utils.responses import ErrorResponse, SuccessResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import Notification


@api_view(["GET"])
@is_authenticated
def get_friends(request):
    user = request.user
    friends = Friendship.objects.filter(
        (Q(source_user=user) | Q(target_user=user)) & Q(status="accepted")
    ).select_related("source_user__profile", "target_user__profile")
    for friendship in friends:
        if friendship.source_user == user:
            friendship.user = friendship.source_user
            friendship.friend = friendship.target_user
        else:
            friendship.user = friendship.target_user
            friendship.friend = friendship.source_user
    friends = [ViewFriendshipSerializer(friendship).data for friendship in friends]

    return SuccessResponse(data=friends)


@api_view(["GET"])
@is_authenticated
def get_blocked_friends(request):
    user = request.user
    friends = Friendship.objects.filter(
        (Q(source_user=user) | Q(target_user=user))
        & Q(status="blocked")
        & Q(blocked_by=user)
    ).select_related("source_user__profile", "target_user__profile")
    for friendship in friends:
        if friendship.source_user == user:
            friendship.user = friendship.source_user
            friendship.friend = friendship.target_user
        else:
            friendship.user = friendship.target_user
            friendship.friend = friendship.source_user
    friends = [ViewFriendshipSerializer(friendship).data for friendship in friends]

    return SuccessResponse(data=friends)


@api_view(["GET"])
@is_authenticated
def get_friends_request(request):
    user = request.user
    friends_request = Friendship.objects.filter(target_user=user, status="pending").select_related(
        "source_user__profile", "target_user__profile"
    )

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
    friends_request = Friendship.objects.filter(source_user=user, status="pending").select_related(
        "source_user__profile", "target_user__profile"
    )

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

    Notification.objects.create(
        user_id=target_user.id,
        message="sent you a friend request",
        type="friend_request",
        sender_id=source_user.id,
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{target_user.id}",
        {
            "type": "send_notification",
            "message": "sent you a friend request",
            "user_id": target_user.id,
            "sender_id": source_user.id,
            "sender_uuid": str(source_user.profile.uuid),
            "sender_username": source_user.username,
            "sender_avatar": str(source_user.profile.avatar),
            "ctx": "friend_request",
        },
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
    # Only a pending request can be accepted. Without this check a blocked
    # user could "accept" an old request and undo the block.
    friendship = Friendship.objects.filter(
        source_user=source_user, target_user=user, status=Friendship.PENDING
    ).first()
    if not friendship:
        return ErrorResponse(
            message="Friend request does not exist",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    friendship.status = "accepted"
    friendship.save()

    Notification.objects.create(
        user_id=source_user.id,
        message="accepted your friend request",
        type="friend_request_accepted",
        sender_id=user.id,
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{source_user.id}",
        {
            "type": "send_notification",
            "message": "accepted your friend request",
            "user_id": source_user.id,
            "sender_id": user.id,
            "sender_uuid": str(user.profile.uuid),
            "sender_username": user.username,
            "sender_avatar": str(user.profile.avatar),
            "ctx": "friend_request_accepted",
        },
    )

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
