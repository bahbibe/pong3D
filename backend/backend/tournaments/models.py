from django.db import models
from api.models import User
import uuid


class Tournament(models.Model):
    WAITING = "waiting"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"
    CANCELED = "cancled"

    TOURNAMENT_STATUS = (
        (WAITING, "waiting"),
        (IN_PROGRESS, "in-progress"),
        (FINISHED, "finished"),
        (CANCELED , "canceled"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    max_participants = models.IntegerField(default=4)
    current_participants = models.IntegerField(default=1)
    winner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name="winner",
    )
    players = models.ManyToManyField(
        User, through="tournaments.TournamentPlayer", related_name="players"
    )
    status = models.CharField(
        max_length=255, default=WAITING, choices=TOURNAMENT_STATUS
    )

    def __str__(self):
        return self.name


class TournamentPlayer(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="tournament"
    )
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name="player")

    def __str__(self):
        return self.player.username


class Match(models.Model):
    SINGLE = "single"
    SEMI_FINAL = "semi-final"
    FINAL = "final"

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"

    MATCHE_TYPE = (
        (SINGLE, "single"),
        (SEMI_FINAL, "semi-final"),
        (FINAL, "final"),
    )

    MATCHE_STATUS = (
        (PENDING, "pending"),
        (IN_PROGRESS, "in-progress"),
        (FINISHED, "finished"),
    )

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # created_by = models.ForeignKey(
    #     User,
    #     on_delete=models.CASCADE,
    #     related_name="created_by",
    #     null=True,
    #     blank=True,
    #     default=None,
    # )
    created_at = models.DateTimeField(auto_now_add=True)
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="player1")
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="player2")
    winner = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, default=None
    )
    type = models.CharField(max_length=255, default=SINGLE, choices=MATCHE_TYPE)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    status = models.CharField(max_length=255, default=PENDING, choices=MATCHE_STATUS)

    def __str__(self):
        return self.name
