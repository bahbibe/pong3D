from django.db import models
from django.contrib.auth.models import User
import uuid

class Profile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
