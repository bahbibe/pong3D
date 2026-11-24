from rest_framework.decorators import api_view

from core.responses import SuccessResponse

from . import services


@api_view(["POST"])
def mark_all_notifications_as_read(request):
    services.mark_all_read(request.user)
    return SuccessResponse(message="All notifications marked as read")


@api_view(["POST"])
def mark_notification_as_read(request, uuid):
    services.mark_read(request.user, uuid)
    return SuccessResponse(message="Notification marked as read")
