from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view

from core.responses import ErrorResponse, SuccessResponse
from core.schema import data_object, responses

from .models import Message
from .serializers import MessageSerializer
from .utils import get_chat_friendship


@extend_schema(
    tags=["chat"],
    summary="Message history of a conversation (a friendship uuid)",
    description="Messages are sent over the /ws/chat/<conversation>/ websocket.",
    parameters=[
        OpenApiParameter("conversation", str, OpenApiParameter.PATH, description="Friendship uuid")
    ],
    responses=responses(
        "Messages",
        data_object("MessageList", messages=MessageSerializer(many=True)),
        errors=(401, 404),
    ),
)
@api_view(["GET"])
def get_messages(request, conversation):
    friendship = get_chat_friendship(request.user, conversation)
    if friendship is None:
        # Same answer for "does not exist" and "not yours", so conversation
        # ids cannot be probed.
        return ErrorResponse(
            message="Conversation not found", status_code=status.HTTP_404_NOT_FOUND
        )

    # Rows written by the previous release only have the uuid as text.
    messages = Message.objects.filter(
        Q(friendship=friendship) | Q(friendship__isnull=True, conversation=str(friendship.uuid))
    ).select_related("author")
    serialized_messages = MessageSerializer(messages, many=True).data
    return SuccessResponse(
        data={"messages": serialized_messages},
        message="Messages fetched successfully.",
        status_code=status.HTTP_200_OK,
    )
