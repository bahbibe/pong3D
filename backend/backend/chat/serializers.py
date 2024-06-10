from rest_framework import serializers
from chat.models import Message, Conversation


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["name", "messages"]

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["author", "content", "timestamp", "conversation", "read"]
    