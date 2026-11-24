"""Friend requests and blocks. Errors are core.errors.ServiceError with
the message shown to the user."""

from django.db import IntegrityError, transaction

from apps.notifications.services import notify
from core.errors import NotFound, ServiceError

from .models import Friendship
from .selectors import friendship_between


def send_request(source_user, target_user):
    if source_user == target_user:
        raise ServiceError("You cannot send a friend request to yourself")
    if friendship_between(source_user, target_user) is not None:
        raise ServiceError("Friendship already exists")
    try:
        with transaction.atomic():
            friendship = Friendship.objects.create(source_user=source_user, target_user=target_user)
    except IntegrityError:
        # The other user sent a request (or blocked) at the same moment.
        raise ServiceError("Friendship already exists")
    notify(target_user, source_user, "friend_request", "sent you a friend request")
    return friendship


def accept_request(user, source_user):
    # Only a pending request can be accepted. Without this check a blocked
    # user could "accept" an old request and undo the block.
    friendship = Friendship.objects.filter(
        source_user=source_user, target_user=user, status=Friendship.PENDING
    ).first()
    if friendship is None:
        raise ServiceError("Friend request does not exist")
    friendship.status = Friendship.ACCEPTED
    friendship.save()
    notify(source_user, user, "friend_request_accepted", "accepted your friend request")
    return friendship


def block(user, target_user):
    if user == target_user:
        raise ServiceError("You cannot block yourself")
    friendship = friendship_between(user, target_user)
    if friendship is None:
        try:
            with transaction.atomic():
                Friendship.objects.create(
                    source_user=user,
                    target_user=target_user,
                    status=Friendship.BLOCKED,
                    blocked_by=user,
                )
            return
        except IntegrityError:
            # A row for this pair was created meanwhile: block that one.
            friendship = friendship_between(user, target_user)
    friendship.status = Friendship.BLOCKED
    friendship.blocked_by = user
    friendship.save()


def unblock(user, target_user):
    friendship = friendship_between(user, target_user)
    if friendship is None:
        raise NotFound("Friendship does not exist")
    if friendship.blocked_by != user:
        raise ServiceError("User is not blocked by you")
    if friendship.status != Friendship.BLOCKED:
        raise ServiceError("User is not blocked")
    friendship.delete()
