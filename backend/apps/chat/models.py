from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    friendship = models.ForeignKey(
        "friends.Friendship",
        on_delete=models.CASCADE,
        null=True,
        related_name="messages",
    )
    # Friendship uuid as text: what the previous release reads and writes.
    # Still written (rollback), read only for rows it wrote. Dropped in a
    # later release, once friendship is filled everywhere.
    conversation = models.CharField(max_length=128, blank=False, null=True, db_index=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return self.content
