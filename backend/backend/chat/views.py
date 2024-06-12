from rest_framework.decorators import api_view
from rest_framework import status
from api.auth_utils import is_authenticated
from .models import  Message
from .serializers import MessageSerializer
from django.http import JsonResponse


@api_view(["GET"])
@is_authenticated
def get_messages(request, conversation):
    try:
        messages = Message.objects.all().filter(conversation=conversation)
        if messages.exists():
            serialized_messages = MessageSerializer(messages, many=True).data
            return JsonResponse({"messages": serialized_messages}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"messages": []}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        return JsonResponse({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

