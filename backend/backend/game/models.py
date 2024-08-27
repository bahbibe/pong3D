from django.db import models
from django.contrib.auth.models import User
import uuid


class Game(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    player1 = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="player1d")
    player2 = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="player2d")
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
