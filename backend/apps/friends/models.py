import uuid

from django.conf import settings
from django.db import models
from django.db.models.functions import Greatest, Least


class Friendship(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"

    STATUSES = [
        (PENDING, "pending"),
        (ACCEPTED, "accepted"),
        (REJECTED, "rejected"),
        (BLOCKED, "blocked"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    source_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="source_user"
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="target_user"
    )
    status = models.CharField(max_length=50, choices=STATUSES, default=PENDING)
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="blocked_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # One row per pair of users, whatever the direction. Without it,
            # A->B and B->A requests sent at the same time make two rows.
            models.UniqueConstraint(
                Least("source_user", "target_user"),
                Greatest("source_user", "target_user"),
                name="friendship_unique_pair",
            ),
        ]

    def __str__(self):
        return f"{self.source_user_id} -> {self.target_user_id} ({self.status})"
