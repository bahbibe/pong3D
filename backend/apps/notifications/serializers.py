import os

from rest_framework import serializers

from .models import Notification


def avatar_url(avatar):
    """intra avatars are absolute URLs; uploaded ones are relative paths."""
    if "cdn.intra.42.fr" in avatar:
        return avatar
    return f"{os.getenv('API_URL')}/{avatar}"


class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    def get_sender(self, obj):
        if obj.sender is None:  # system notification
            return None
        return {
            "id": obj.sender.id,
            "username": obj.sender.username,
            "avatar": avatar_url(str(obj.sender.profile.avatar)),
            "uuid": str(obj.sender.profile.uuid),
        }

    class Meta:
        model = Notification
        fields = ["uuid", "type", "message", "is_read", "created_at", "sender", "game_id"]
