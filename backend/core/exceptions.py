"""DRF exception handler (REST_FRAMEWORK["EXCEPTION_HANDLER"]).

Every error leaves the API in the same JSON shape as core.responses:
{"success": false, "message": ..., ["errors": {...}]}. Exceptions that
are not API errors are logged and answered with a JSON 500 that says
nothing about the cause.
"""

import logging

from rest_framework.views import exception_handler as drf_exception_handler

from .errors import ServiceError
from .responses import ErrorResponse, SuccessResponse

logger = logging.getLogger(__name__)

# Headers DRF sets on error responses that clients rely on.
KEPT_HEADERS = ("WWW-Authenticate", "Allow", "Retry-After")


def handler(exc, context):
    # An "error" that is not one (accounts.permissions.TfaRequired).
    status_code = getattr(exc, "status_code", 500)
    if status_code < 400 and hasattr(exc, "data"):
        return SuccessResponse(data=exc.data, message=str(exc.detail), status_code=status_code)

    if isinstance(exc, ServiceError):
        return ErrorResponse(
            message=str(exc.detail), status_code=exc.status_code, serializer_errors=exc.errors
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        request = context.get("request")
        logger.error(
            "unhandled error in %s",
            getattr(request, "path", "?"),
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return ErrorResponse(status_code=500)

    data = response.data
    if isinstance(data, dict) and set(data) == {"detail"}:
        out = ErrorResponse(message=str(data["detail"]), status_code=response.status_code)
    else:
        # Validation errors: {"field": ["message", ...]} (or a list).
        errors = data if isinstance(data, dict) else {"non_field_errors": data}
        errors = {k: v if isinstance(v, list) else [v] for k, v in errors.items()}
        out = ErrorResponse(
            message="Invalid data", serializer_errors=errors, status_code=response.status_code
        )
    for name in KEPT_HEADERS:
        if name in response:
            out[name] = response[name]
    return out
