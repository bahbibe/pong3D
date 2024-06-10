from rest_framework.decorators import api_view
from .models import Conversation, Message
from api.auth_utils import is_authenticated
from utils.responses import  SuccessResponse
from .serializers import MessageSerializer
from api.models import User

# create dummy conversations
def create_dummy_conversations():
    Conversation.objects.create(name="messages")
    Conversation.objects.create(name="general")
    Conversation.objects.create(name="random")

# create dummy messages

def create_dummy_messages():
    create_dummy_conversations()
    conversation = Conversation.objects.filter(name="messages").first()
    Message.objects.create(conversation=conversation, author=User.objects.first(), content="Hello")
    Message.objects.create(conversation=conversation, author=User.objects.first(), content="World")
    conversation = Conversation.objects.filter(name="general").first()
    Message.objects.create(conversation=conversation, author=User.objects.first(), content="Hello")
    Message.objects.create(conversation=conversation, author=User.objects.first(), content="World")
    conversation = Conversation.objects.filter(name="random").first()

@api_view(["GET"])
@is_authenticated
def get_messages(request, conversation_name):
    create_dummy_messages()
    conversation = Conversation.objects.get(name=conversation_name)
    messages = Message.objects.filter(conversation=conversation)
    messages = [MessageSerializer(message).data for message in messages]
    return SuccessResponse(data=messages)

