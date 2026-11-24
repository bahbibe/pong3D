import uuid

from django.db.models import Q

from apps.friends.models import Friendship


def get_chat_friendship(user, conversation):
    """
    Return the accepted Friendship that `conversation` (a friendship uuid)
    points to, if `user` is one of its two members. Otherwise return None.

    Blocked, pending and rejected friendships return None, so a block
    also closes the chat.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        conversation_uuid = uuid.UUID(str(conversation))
    except (TypeError, ValueError):
        return None
    return (
        Friendship.objects.filter(
            Q(source_user=user) | Q(target_user=user),
            uuid=conversation_uuid,
            status=Friendship.ACCEPTED,
        )
        .only("id", "uuid")
        .first()
    )
