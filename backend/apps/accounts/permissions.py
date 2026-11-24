from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework.permissions import BasePermission

from .authentication import is_tfa_verified


class TfaRequired(APIException):
    """The token comes from the password step and the user has 2FA on.
    core.exceptions.handler answers it with the 200 body the frontend
    expects (it then shows the 2FA form)."""

    status_code = 200
    default_detail = "Two factor authentication is enabled"

    def __init__(self, user):
        from .serializers import UserSerializer

        super().__init__()
        self.data = {"user": UserSerializer(user).data, "is_tfa_verified": False}


class IsAuthenticated(BasePermission):
    """A valid token, even one issued before the 2FA step. Only for the
    views that finish or leave that step (2FA verify, logout)."""

    def has_permission(self, request, view):
        if request.user is None or not request.user.is_authenticated:
            raise NotAuthenticated("No access token found")
        return True


class IsTfaVerified(IsAuthenticated):
    """Default for every API view: a valid token, past the 2FA step when
    the user has 2FA on."""

    def has_permission(self, request, view):
        super().has_permission(request, view)
        if request.user.profile.is_tfa_enabled and not is_tfa_verified(request.auth):
            raise TfaRequired(request.user)
        return True
