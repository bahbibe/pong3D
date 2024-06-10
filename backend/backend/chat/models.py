from django.db import models
from api.models import User
from uuid import uuid4


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=128)
    paties = models.ManyToManyField(to=User, related_name="conversations")
    def __str__(self):
        return self.name
    
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(to=Conversation, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    class Meta:
        ordering = ["timestamp"]
    def __str__(self):
        return f"{self.author}: {self.content}"
