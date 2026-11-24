"""Read queries about friendships and blocks."""

from django.db.models import Q

from .models import Friendship


def _involving(user):
    return Q(source_user=user) | Q(target_user=user)


def _pair(a, b):
    return Q(source_user=a, target_user=b) | Q(source_user=b, target_user=a)


def _seen_by(user, friendships):
    """Set .user (this user) and .friend (the other side) on each row, as
    ViewFriendshipSerializer expects."""
    rows = list(friendships.select_related("source_user__profile", "target_user__profile"))
    for friendship in rows:
        if friendship.source_user_id == user.id:
            friendship.user, friendship.friend = friendship.source_user, friendship.target_user
        else:
            friendship.user, friendship.friend = friendship.target_user, friendship.source_user
    return rows


def friends(user):
    return _seen_by(user, Friendship.objects.filter(_involving(user), status=Friendship.ACCEPTED))


def blocked_by(user):
    """Users that `user` blocked (not the ones who blocked `user`)."""
    return _seen_by(
        user,
        Friendship.objects.filter(_involving(user), status=Friendship.BLOCKED, blocked_by=user),
    )


def received_requests(user):
    return _seen_by(user, Friendship.objects.filter(target_user=user, status=Friendship.PENDING))


def sent_requests(user):
    return _seen_by(user, Friendship.objects.filter(source_user=user, status=Friendship.PENDING))


def friendship_between(a, b):
    """The row for this pair (there is at most one, either direction)."""
    return Friendship.objects.filter(_pair(a, b)).first()


def are_friends(a, b):
    return Friendship.objects.filter(_pair(a, b), status=Friendship.ACCEPTED).exists()


def is_blocked(a, b):
    """True when one of the two blocked the other. Never for a == b."""
    if a is None or b is None or a == b:
        return False
    return Friendship.objects.filter(_pair(a, b), status=Friendship.BLOCKED).exists()


def blocked_user_ids(user):
    """Ids of users on the other side of a block with `user` (either way)."""
    pairs = Friendship.objects.filter(_involving(user), status=Friendship.BLOCKED).values_list(
        "source_user_id", "target_user_id"
    )
    return {uid for pair in pairs for uid in pair if uid != user.id}
