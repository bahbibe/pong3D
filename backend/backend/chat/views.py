from rest_framework.decorators import api_view
from rest_framework import status
from api.auth_utils import is_authenticated
from .models import  Message
from .serializers import MessageSerializer
from utils.responses import ErrorResponse, SuccessResponse

@api_view(["GET"])
@is_authenticated
def get_messages(request, conversation):
    try:


        messages = Message.objects.all().filter(conversation=conversation)
        if messages.exists():
            serialized_messages = MessageSerializer(messages, many=True).data
            return SuccessResponse(data={"messages": serialized_messages}, message="Messages fetched successfully.", status_code=status.HTTP_200_OK)
        else:
            print("==================")
            print(messages)
            print("==================")
            return SuccessResponse(data={"messages": []}, message="No messages found.", status_code=status.HTTP_200_OK)
    except Exception as e:
        return ErrorResponse(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
