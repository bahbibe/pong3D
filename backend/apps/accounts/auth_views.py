"""Login, register, logout, the current user, 42 intra OAuth and 2FA.
The rules live in services.py, intra.py and twofa.py."""

import secrets

from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from apps.notifications import selectors as notification_selectors
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.serializers import NotificationSerializer as _Notification
from core.errors import ServiceError
from core.responses import ErrorResponse, SuccessResponse
from core.schema import data_object, responses

from . import intra, rate_limit, services, twofa
from .auth_utils import revoke_tokens, set_access_token
from .permissions import IsAuthenticated
from .serializers import LoginUserSerializer, RegisterUserSerializer, UserSerializer

CODE_REQUEST = inline_serializer(
    "TwoFaCode", {"code": serializers.CharField(help_text="6 digits from the authenticator app")}
)

INTRA_STATE_COOKIE = "intra_oauth_state"
INTRA_STATE_MAX_AGE = 10 * 60


@extend_schema(
    tags=["auth"],
    summary="Log in with email or username and password; sets the access_token cookie",
    request=LoginUserSerializer,
    responses=responses(
        "Login", data_object("LoginData", user=UserSerializer()), errors=(400, 404, 429)
    ),
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_user(request):
    serializer = LoginUserSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    data = serializer.validated_data
    user = services.login(
        data.get("password"),
        ip=rate_limit.client_ip(request),
        email=data.get("email"),
        username=data.get("username"),
    )
    response = SuccessResponse({"user": UserSerializer(user).data})
    return set_access_token(response, user, is_tfa_verified=False)


@extend_schema(
    tags=["auth"],
    summary="Create an account (log in afterwards)",
    request=RegisterUserSerializer,
    responses=responses("Register", UserSerializer, errors=(400,)),
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterUserSerializer(data=request.data)
    if not serializer.is_valid():
        return ErrorResponse(serializer_errors=serializer.errors)
    data = serializer.validated_data
    user = services.register(
        data["username"], data["email"], data["password"], data["first_name"], data["last_name"]
    )
    return SuccessResponse(
        data=UserSerializer(user).data,
        message="You have been registered successfully. Please login to continue.",
    )


@extend_schema(
    tags=["auth"],
    summary="Log out: ends every session of the user and deletes the cookie",
    request=None,
    responses=responses("Logout"),
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    # Deleting the cookie is not enough: a copy of the token would stay valid
    # until it expires. Revoking ends every session of this user.
    revoke_tokens(request.user)
    response = SuccessResponse(message="User logged out")
    response.delete_cookie("access_token", samesite=settings.AUTH_COOKIE_SAMESITE)
    return response


@extend_schema(
    tags=["auth"],
    summary="The current user and their unread notifications",
    description=(
        'With 2FA pending, answers 200 with message "Two factor authentication '
        'is enabled" and data {user, is_tfa_verified: false}.'
    ),
    responses=responses(
        "Me",
        data_object("MeData", user=UserSerializer(), notifications=_Notification(many=True)),
        errors=(401,),
    ),
)
@api_view(["GET"])
def get_user(request):
    unread = notification_selectors.unread(request.user)
    return SuccessResponse(
        data={
            "user": UserSerializer(request.user).data,
            "notifications": NotificationSerializer(unread, many=True).data,
        }
    )


@extend_schema(
    tags=["auth"],
    summary="Start a 42 intra login: the URL to send the browser to",
    responses=responses(
        "IntraLogin", data_object("IntraUrl", url=serializers.URLField()), errors=()
    ),
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_intra(request):
    state = intra.new_state()
    response = SuccessResponse(data={"url": intra.authorize_url(state)})
    response.set_signed_cookie(
        INTRA_STATE_COOKIE,
        state,
        salt=INTRA_STATE_COOKIE,
        max_age=INTRA_STATE_MAX_AGE,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="Lax",
    )
    return response


@extend_schema(
    tags=["auth"],
    summary="42 intra redirects here; logs in and redirects to the frontend",
    parameters=[
        OpenApiParameter("code", str, description="Authorization code from 42"),
        OpenApiParameter("state", str, description="Must match the state cookie set by /intra/"),
        OpenApiParameter("error", str, description="Set by 42 when the user refused"),
    ],
    responses={
        302: OpenApiResponse(description="Logged in: redirect to the frontend"),
        400: responses("_", errors=(400,))[400],
        401: responses("_", errors=(401,))[401],
        502: responses("_", errors=(502,))[502],
    },
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_intra_callback(request):
    if request.GET.get("error"):
        return ErrorResponse(message=request.GET["error"])
    code = request.GET.get("code")
    if not code:
        return ErrorResponse(message="No code found")

    expected_state = request.get_signed_cookie(
        INTRA_STATE_COOKIE, default=None, salt=INTRA_STATE_COOKIE, max_age=INTRA_STATE_MAX_AGE
    )
    received_state = request.GET.get("state") or ""
    if not expected_state or not secrets.compare_digest(expected_state, received_state):
        raise ServiceError(
            "Login request expired or invalid, please try again.", status.HTTP_400_BAD_REQUEST
        )

    user = intra.find_or_create_intra_user(intra.fetch_user_data(code))
    response = redirect(settings.FRONTEND_URL)
    response.delete_cookie(INTRA_STATE_COOKIE, samesite="Lax")
    return set_access_token(response, user, is_tfa_verified=False)


@extend_schema(
    tags=["2fa"],
    summary="Start enabling 2FA: a new secret as a QR code (confirm it next)",
    request=None,
    responses=responses(
        "TwoFaEnable",
        data_object("QrCode", image=serializers.CharField(help_text="data: URL of a PNG")),
    ),
)
@api_view(["POST"])
def enable_twofa(request):
    return SuccessResponse(message="2FA enables", data={"image": twofa.start(request.user)})


@extend_schema(
    tags=["2fa"],
    summary="Turn 2FA on with a first valid code",
    request=CODE_REQUEST,
    responses=responses("TwoFaConfirm", errors=(400, 401, 429)),
)
@api_view(["POST"])
def confirm_twofa(request):
    twofa.confirm(request.user, request.data.get("code"))
    # The user just proved they hold the secret, so the current session counts
    # as verified. Without this the next request would be sent back to 2FA.
    return set_access_token(
        SuccessResponse(message="2FA confirmed"), request.user, is_tfa_verified=True
    )


@extend_schema(
    tags=["2fa"],
    summary="Enter the 2FA code after login (works with a 2FA-pending token)",
    request=CODE_REQUEST,
    responses=responses("TwoFaVerify", errors=(400, 401, 429)),
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_twofa(request):
    twofa.verify(request.user, request.data.get("code"))
    return set_access_token(
        SuccessResponse(message="Code is valid"), request.user, is_tfa_verified=True
    )


@extend_schema(
    tags=["2fa"],
    summary="Turn 2FA off (needs a current code)",
    request=CODE_REQUEST,
    responses=responses("TwoFaDisable", errors=(400, 401, 429)),
)
@api_view(["POST"])
def disable_twofa(request):
    twofa.disable(request.user, request.data.get("code"))
    return SuccessResponse(message="2FA disabled successfully")
