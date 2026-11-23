from django.db import models
from api.models import User
import uuid


# Create your models here.
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
        User, on_delete=models.CASCADE, related_name="source_user"
    )
    target_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="target_user"
    )
    status = models.CharField(max_length=50, choices=STATUSES, default=PENDING)
    blocked_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["source_user", "target_user"]
