from rest_framework import serializers
from chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(source="author.username")
    class Meta:
        model = Message
        fields = ["author", "content" ]
