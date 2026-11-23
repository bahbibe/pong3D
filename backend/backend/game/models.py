from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Game(models.Model):
    PENDING = "pending"
    PLAYING = "playing"
    FINISHED = "finished"
    STATUSES = [
        (PENDING, "pending"),
        (PLAYING, "playing"),
        (FINISHED, "finished"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # SET_NULL: deleting an account keeps the other player's history.
    player1 = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="player1d", blank=True, null=True)
    player2 = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="player2d", blank=True, null=True)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)

    # Only finished games count in stats, history and the leaderboard.
    # Invites that were never played stay "pending".
    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING, db_index=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="won_games", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_finished(self):
        return self.status == self.FINISHED


class Tournament(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    finished = models.BooleanField(default=False)


class Tournament_Participants(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    t_round = models.IntegerField(default=3) # round decrement with each win
    ready = models.BooleanField(default=False)
    class Meta:
        unique_together = (('tournament', 'player',))


class Tournament_Game(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, blank=True, null=True)
    t_round = models.IntegerField(default=2)
    class Meta:
        unique_together = (('tournament', 'game',),)
