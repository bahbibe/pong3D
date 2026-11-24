import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.errors import NotFound
from core.uuids import parse_uuid

from .models import Notification

logger = logging.getLogger(__name__)


def notify(user, sender, type, message, game_id=None):
    """Store a notification for `user` and push it to their open
    /ws/notifications/ sockets. `sender` may be None (system notification).

    Sync code only (views, or inside database_sync_to_async). Returns the
    Notification, or None when there is nobody to notify."""
    if user is None:
        logger.warning("notify(%r): no user to notify", type)
        return None

    notification = Notification.objects.create(
        user=user, sender=sender, type=type, message=message, game_id=game_id
    )
    event = {
        "type": "send_notification",
        "notification_uuid": str(notification.uuid),
        "message": message,
        "user_id": user.id,
        "ctx": type,
        "sender_id": None,
        "sender_uuid": None,
        "sender_username": None,
        "sender_avatar": None,
    }
    if sender is not None:
        event.update(
            sender_id=sender.id,
            sender_uuid=str(sender.profile.uuid),
            sender_username=sender.username,
            sender_avatar=str(sender.profile.avatar),
        )
    if game_id is not None:
        event["game_id"] = game_id
    async_to_sync(get_channel_layer().group_send)(f"user_{user.id}", event)
    return notification


def mark_all_read(user):
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)


def mark_read(user, uuid):
    """Mark one of `user`'s notifications as read. Someone else's
    notification, or a malformed uuid, is "does not exist"."""
    notification_uuid = parse_uuid(uuid)
    notification = (
        Notification.objects.filter(uuid=notification_uuid, user=user).first()
        if notification_uuid
        else None
    )
    if notification is None:
        raise NotFound("Notification does not exist")
    notification.is_read = True
    notification.save(update_fields=["is_read"])
