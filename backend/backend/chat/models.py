from django.db import models
from api.models import User
from uuid import uuid4
from django.utils import timezone

    
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    conversation = models.CharField(max_length=128, blank=False , null=True)
    class Meta:
        ordering = ["timestamp"]
    def __str__(self):
        return self.content
