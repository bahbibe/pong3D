from rest_framework import status
from rest_framework.decorators import api_view

from core.responses import ErrorResponse, SuccessResponse
from core.uuids import parse_uuid

from .models import Notification


@api_view(["POST"])
def mark_all_notifications_as_read(request):
    user = request.user
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return SuccessResponse(message="All notifications marked as read")


@api_view(["POST"])
def mark_notification_as_read(request, uuid):
    notification_uuid = parse_uuid(uuid)
    notification = (
        Notification.objects.filter(uuid=notification_uuid, user=request.user).first()
        if notification_uuid
        else None
    )
    if not notification:
        return ErrorResponse(
            message="Notification does not exist", status_code=status.HTTP_404_NOT_FOUND
        )
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return SuccessResponse(message="Notification marked as read")
