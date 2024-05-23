from django.db import models
from api.models import Profile as User

class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, default='unread')
    def __str__(self):
        return self.author + '=>' + self.content
