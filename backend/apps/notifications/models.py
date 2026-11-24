import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # friend_request, friend_request_accepted, game_invite
    type = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    # None for a system notification.
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Game id, or "<tournament uuid>/<game id>" for a tournament game.
    game_id = models.CharField(null=True)

    class Meta:
        # Moved from the "api" app: the table keeps its name, so an older
        # image still works against the same database (rollback).
        db_table = "api_notification"

    def __str__(self):
        return f"{self.type} for user {self.user_id}"
