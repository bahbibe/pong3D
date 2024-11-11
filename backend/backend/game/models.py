from django.db import models
from django.contrib.auth.models import User
import uuid


class Game(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    player1 = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="player1d", blank=True, null=True)
    player2 = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="player2d", blank=True, null=True)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)

class Tournament(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    started = models.BooleanField(default=0)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)

class Tournament_Participants(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    t_round = models.IntegerField(default=3) # round decrement with each win
    class Meta:
        unique_together = ('tournament', 'player',)

class Tournament_Game(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.DO_NOTHING)
    game = models.ForeignKey(Game, on_delete=models.DO_NOTHING, blank=True, null=True)
    class Meta:
        unique_together = (('tournament', 'game'),)








