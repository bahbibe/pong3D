"""Errors raised by services (apps/*/services.py).

A service raises ServiceError with the message the user should see; the
DRF exception handler (core/exceptions.py) answers it with the usual
{"success": false, "message": ..., ["errors": {...}]} body. Views do not
need to catch it.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class ServiceError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Something went wrong!, Please try again later."

    def __init__(self, message=None, status_code=None, errors=None):
        super().__init__(detail=message)
        if status_code is not None:
            self.status_code = status_code
        # {"field": ["message", ...]}, shown under "errors".
        self.errors = errors


class NotFound(ServiceError):
    status_code = status.HTTP_404_NOT_FOUND


class TooManyAttempts(ServiceError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many failed attempts. Please wait a few minutes and try again."
