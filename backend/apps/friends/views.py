from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view

from apps.game import selectors as game_selectors
from apps.game.serializers import GameStatsSerializer
from core.responses import ErrorResponse, SuccessResponse
from core.schema import responses

from . import selectors, services
from .serializers import (
    AcceptFriendRequestSerializer,
    BlockUserSerializer,
    FriendshipSerializer,
    SentFriendRequestSerializer,
    ViewFriendshipSerializer,
)


def _listing(rows):
    return SuccessResponse(data=[ViewFriendshipSerializer(row).data for row in rows])


@extend_schema(
    tags=["friends"],
    summary="Friends, each with their game stats",
    responses=responses(
        "Friends",
        inline_serializer(
            "FriendWithStats",
            {
                "user": serializers.DictField(),
                "friend": serializers.DictField(),
                "status": serializers.CharField(),
                "uuid": serializers.UUIDField(help_text="Also the chat conversation id"),
                "stats": GameStatsSerializer(),
            },
            many=True,
        ),
        errors=(401,),
    ),
)
@api_view(["GET"])
def get_friends(request):
    """Friends, each with their game stats (one more query for all of them)."""
    rows = selectors.friends(request.user)
    stats = game_selectors.stats_for(row.friend.id for row in rows)
    return SuccessResponse(
        data=[
            {
                **ViewFriendshipSerializer(row).data,
                "stats": GameStatsSerializer(stats[row.friend.id]).data,
            }
            for row in rows
        ]
    )


@extend_schema(
    tags=["friends"],
    summary="Users you blocked",
    responses=responses("Blocked", ViewFriendshipSerializer, many=True, errors=(401,)),
)
@api_view(["GET"])
def get_blocked_friends(request):
    return _listing(selectors.blocked_by(request.user))


@extend_schema(
    tags=["friends"],
    summary="Friend requests you received",
    responses=responses("Received", ViewFriendshipSerializer, many=True, errors=(401,)),
)
@api_view(["GET"])
def get_friends_request(request):
    return _listing(selectors.received_requests(request.user))


@extend_schema(
    tags=["friends"],
    summary="Friend requests you sent",
    responses=responses("Sent", ViewFriendshipSerializer, many=True, errors=(401,)),
)
@api_view(["GET"])
def get_sent_friends_request(request):
    return _listing(selectors.sent_requests(request.user))


@extend_schema(
    tags=["friends"],
    summary="Send a friend request",
    request=SentFriendRequestSerializer,
    responses=responses("SendRequest", FriendshipSerializer, errors=(400, 401)),
)
@api_view(["POST"])
def send_friend_request(request):
    serializer = SentFriendRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    friendship = services.send_request(request.user, serializer.validated_data["target_user"])
    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@extend_schema(
    tags=["friends"],
    summary="Accept a friend request",
    request=AcceptFriendRequestSerializer,
    responses=responses("AcceptRequest", FriendshipSerializer, errors=(400, 401, 404)),
)
@api_view(["POST"])
def accept_friend_request(request):
    serializer = AcceptFriendRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    friendship = services.accept_request(request.user, serializer.validated_data["source_user"])
    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@extend_schema(
    tags=["friends"],
    summary="Block a user (also closes the chat)",
    request=BlockUserSerializer,
    responses=responses("Block", errors=(400, 401)),
)
@api_view(["POST"])
def block_user(request):
    serializer = BlockUserSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    services.block(request.user, serializer.validated_data["user_id"])
    return SuccessResponse(message="User blocked successfully")


@extend_schema(
    tags=["friends"],
    summary="Unblock a user you blocked",
    request=BlockUserSerializer,
    responses=responses("Unblock", errors=(400, 401, 404)),
)
@api_view(["POST"])
def unblock_user(request):
    serializer = BlockUserSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    services.unblock(request.user, serializer.validated_data["user_id"])
    return SuccessResponse(message="User unblocked successfully")
