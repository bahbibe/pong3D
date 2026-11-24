from .models import Notification


def unread(user):
    """Unread notifications of `user`, newest first. The sender and its
    profile come in the same query (the serializer reads both)."""
    return (
        Notification.objects.filter(user=user, is_read=False)
        .select_related("sender__profile")
        .order_by("-created_at")
    )
