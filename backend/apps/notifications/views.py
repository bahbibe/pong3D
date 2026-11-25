from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view

from core.responses import SuccessResponse
from core.schema import responses

from . import services


@extend_schema(
    tags=["notifications"],
    summary="Mark every notification as read",
    operation_id="notifications_mark_all_read",
    request=None,
    responses=responses("MarkAllRead", errors=(401,)),
)
@api_view(["POST"])
def mark_all_notifications_as_read(request):
    services.mark_all_read(request.user)
    return SuccessResponse(message="All notifications marked as read")


@extend_schema(
    tags=["notifications"],
    summary="Mark one notification as read",
    operation_id="notifications_mark_read",
    request=None,
    responses=responses("MarkRead", errors=(401, 404)),
)
@api_view(["POST"])
def mark_notification_as_read(request, uuid):
    services.mark_read(request.user, uuid)
    return SuccessResponse(message="Notification marked as read")
