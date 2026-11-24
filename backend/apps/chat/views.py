from rest_framework import status
from rest_framework.decorators import api_view

from core.responses import ErrorResponse, SuccessResponse

from .models import Message
from .serializers import MessageSerializer
from .utils import get_chat_friendship


@api_view(["GET"])
def get_messages(request, conversation):
    friendship = get_chat_friendship(request.user, conversation)
    if friendship is None:
        # Same answer for "does not exist" and "not yours", so conversation
        # ids cannot be probed.
        return ErrorResponse(
            message="Conversation not found", status_code=status.HTTP_404_NOT_FOUND
        )

    messages = Message.objects.filter(conversation=str(friendship.uuid)).select_related("author")
    serialized_messages = MessageSerializer(messages, many=True).data
    return SuccessResponse(
        data={"messages": serialized_messages},
        message="Messages fetched successfully.",
        status_code=status.HTTP_200_OK,
    )
