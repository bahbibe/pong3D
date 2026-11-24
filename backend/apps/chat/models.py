from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    # Friendship uuid. Indexed: chat history is loaded by conversation.
    conversation = models.CharField(max_length=128, blank=False, null=True, db_index=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return self.content
