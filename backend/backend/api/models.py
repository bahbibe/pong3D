from django.db import models
from django.contrib.auth.models import User
import uuid


class Profile(models.Model):
    EMAIL = "email"
    INTRA = "intra"

    AUTH_CHOICES = [
        (EMAIL, "email"),
        (INTRA, "intra"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        default="avatars/profile_default.jpg",
    )
    auth_method = models.CharField(max_length=50, default=EMAIL, choices=AUTH_CHOICES)
    intra_id = models.IntegerField(null=True, blank=True)
    is_setup = models.BooleanField(default=False)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_tfa_enabled = models.BooleanField(default=False)
    tfa_secret = models.CharField(max_length=255, null=True, blank=True)


class Notification(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    type = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    game_id = models.IntegerField(null=True)