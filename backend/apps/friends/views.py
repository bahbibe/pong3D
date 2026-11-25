from rest_framework.decorators import api_view

from apps.game import selectors as game_selectors
from apps.game.serializers import GameStatsSerializer
from core.responses import ErrorResponse, SuccessResponse

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


@api_view(["GET"])
def get_blocked_friends(request):
    return _listing(selectors.blocked_by(request.user))


@api_view(["GET"])
def get_friends_request(request):
    return _listing(selectors.received_requests(request.user))


@api_view(["GET"])
def get_sent_friends_request(request):
    return _listing(selectors.sent_requests(request.user))


@api_view(["POST"])
def send_friend_request(request):
    serializer = SentFriendRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    friendship = services.send_request(request.user, serializer.validated_data["target_user"])
    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@api_view(["POST"])
def accept_friend_request(request):
    serializer = AcceptFriendRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    friendship = services.accept_request(request.user, serializer.validated_data["source_user"])
    return SuccessResponse(data=FriendshipSerializer(friendship).data)


@api_view(["POST"])
def block_user(request):
    serializer = BlockUserSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    services.block(request.user, serializer.validated_data["user_id"])
    return SuccessResponse(message="User blocked successfully")


@api_view(["POST"])
def unblock_user(request):
    serializer = BlockUserSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    services.unblock(request.user, serializer.validated_data["user_id"])
    return SuccessResponse(message="User unblocked successfully")
