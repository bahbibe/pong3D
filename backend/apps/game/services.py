"""Game invites and tournaments. Errors are core.errors.ServiceError."""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

from apps.friends.selectors import are_friends
from apps.notifications.services import notify
from core.errors import NotFound, ServiceError
from core.uuids import parse_uuid

from .models import Game, Tournament
from .tournament import ensure_bracket

logger = logging.getLogger(__name__)

COULD_NOT_CREATE = "Could not create the game, please try again."


def _id(value):
    """int from a URL part, or None."""
    return int(value) if str(value).isdigit() else None


def get_game(game_id):
    game = Game.objects.filter(id=_id(game_id)).first() if _id(game_id) is not None else None
    if game is None:
        # 400, not 404: what the frontend has always received here.
        raise ServiceError("Game not found")
    return game


def _invite(source_user, target_user):
    """New game between the two, and a notification for the target."""
    try:
        game = Game.objects.create(player1=source_user, player2=target_user)
        notify(target_user, source_user, "game_invite", "invated you to a game", game_id=game.id)
    except Exception as error:
        logger.exception("could not create game invite")
        raise ServiceError(COULD_NOT_CREATE) from error
    return game


def invite_friend(source_user, friend_id):
    friend_id = _id(friend_id)
    target_user = (
        get_user_model().objects.filter(id=friend_id).first() if friend_id is not None else None
    )
    if target_user is None or not are_friends(source_user, target_user):
        raise ServiceError("You can only invite your friends.")
    return _invite(source_user, target_user)


def play_again(user, game_id):
    """Invite the opponent of one of `user`'s games to a new game."""
    game_id = _id(game_id)
    previous = (
        Game.objects.filter(Q(player1=user) | Q(player2=user), id=game_id).first()
        if game_id is not None
        else None
    )
    if previous is None:
        raise ServiceError(COULD_NOT_CREATE)
    opponent = previous.player1 if previous.player2 == user else previous.player2
    if opponent is None:
        raise ServiceError("This game has no opponent to invite.")
    return _invite(user, opponent)


def create_tournament(owner):
    with transaction.atomic():
        tournament = Tournament.objects.create(owner=owner)
        ensure_bracket(tournament)
    return tournament


def get_tournament(tournament_uuid):
    tournament_uuid = parse_uuid(tournament_uuid)
    tournament = (
        Tournament.objects.filter(uuid=tournament_uuid).first() if tournament_uuid else None
    )
    if tournament is None:
        raise NotFound("Tournament not found")
    return tournament
