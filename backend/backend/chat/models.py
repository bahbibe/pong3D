from django.db import models
from api.models import User

class Message(models.Model):
    body = models.TextField()
    sender = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['timestamp']
    def __str__(self):
        return f'{self.sender} - {self.body}'
    


class Conversation(models.Model):
    ConversationID = models.AutoField(primary_key=True)
    participants = models.ManyToManyField(User, related_name='participants' ,blank=True)
    messages = models.ManyToManyField(Message, blank=True)
    # url = models.URLField(blank=True, null=True)
    def __str__(self):
        return f'{self.ConversationID} - {self.participants}'