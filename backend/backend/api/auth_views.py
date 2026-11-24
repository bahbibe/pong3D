from rest_framework.decorators import api_view
from .serializers import (
    RegisterUserSerializer,
    UserSerializer,
    LoginUserSerializer,
    NotificationSerializer,
)
from rest_framework import status
from django.contrib.auth.models import User
from .models import Profile, Notification
from django.shortcuts import redirect
from django.contrib.auth.hashers import check_password
from .auth_utils import is_authenticated, revoke_tokens, set_access_token
from django.db.models import Q
from django.utils import timezone
from . import rate_limit
from django.conf import settings
from utils.responses import ErrorResponse, SuccessResponse
import secrets
import urllib.parse
from django.db import IntegrityError, transaction
import requests
import os
import random
import string
import pyotp.totp
import qrcode
import base64
import io


INTRA_TIMEOUT_SECONDS = 10


def check_totp(user, code):
    """
    Check a TOTP code and count failures per user (rate_limit "tfa-user").
    Returns False while the user is blocked, without checking the code, and
    for a code that was already accepted once.
    """
    if rate_limit.is_blocked("tfa-user", user.id):
        return False
    profile = user.profile
    totp = pyotp.TOTP(profile.tfa_secret)
    now = timezone.now()
    counter = totp.timecode(now)
    # Each code works once: claim its time step atomically, so a code seen
    # by someone else (shoulder surfing, a proxy log) cannot be replayed.
    if totp.verify(str(code), for_time=now) and (
        Profile.objects.filter(pk=profile.pk)
        .filter(Q(tfa_last_counter__isnull=True) | Q(tfa_last_counter__lt=counter))
        .update(tfa_last_counter=counter)
    ):
        profile.tfa_last_counter = counter
        rate_limit.reset("tfa-user", user.id)
        return True
    rate_limit.record_failure("tfa-user", user.id)
    return False


def parse_intra_user(payload):
    """Pick the fields we need from /v2/me. None if the payload is unusable."""
    if not isinstance(payload, dict):
        return None
    intra_id = payload.get("id")
    login = payload.get("login")
    if not isinstance(intra_id, int) or not login:
        return None
    image = payload.get("image") or {}
    return {
        "id": intra_id,
        "username": login,
        "email": payload.get("email") or "",
        "first_name": (payload.get("first_name") or "")[:150],
        "last_name": (payload.get("last_name") or "")[:150],
        # Some intra accounts have no picture: keep the model default then.
        "avatar": image.get("link") if isinstance(image, dict) else None,
    }


def find_or_create_intra_user(user_data):
    """
    Return the account for an intra user, creating it on first login.

    Accounts are matched by intra id only. Matching by username let an
    intra user rename their account to someone's 42 login and receive that
    person's first login.
    """
    profile = (
        Profile.objects.select_related("user").filter(intra_id=user_data["id"]).first()
    )
    if profile:
        return profile.user

    # Accounts created before intra_id was stored: claim them once and
    # save the id. Only intra accounts that have no id yet can match.
    legacy = (
        Profile.objects.select_related("user")
        .filter(
            user__username=user_data["username"],
            auth_method=Profile.INTRA,
            intra_id__isnull=True,
        )
        .first()
    )
    if legacy:
        legacy.intra_id = user_data["id"]
        legacy.save(update_fields=["intra_id"])
        return legacy.user

    username = user_data["username"]
    while User.objects.filter(username=username).exists():
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{user_data['username']}_{suffix}"

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
        )
        user.set_unusable_password()
        user.save()
        profile_fields = {"auth_method": Profile.INTRA, "intra_id": user_data["id"]}
        if user_data["avatar"]:
            profile_fields["avatar"] = user_data["avatar"]
        # The post_save signal created the profile; fill in the intra fields.
        Profile.objects.filter(user=user).update(**profile_fields)
        user.refresh_from_db()
    return user



@api_view(["POST"])
def login_user(request):
    serailizer = LoginUserSerializer(data=request.data)

    if serailizer.is_valid():
        custom_validataion = (
            serailizer.validated_data.get("email") is not None
            or serailizer.validated_data.get("username") is not None
        )
        if not custom_validataion:
            return ErrorResponse(
                message="An email or username is required to log in.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        auth_field = (
            "email"
            if serailizer.validated_data.get("email") is not None
            else "username"
        )
        login_value = str(serailizer.validated_data.get(auth_field))
        account_key = f"{auth_field}:{login_value.lower()}"
        ip_key = rate_limit.client_ip(request)
        if rate_limit.is_blocked("login-account", account_key) or rate_limit.is_blocked(
            "login-ip", ip_key
        ):
            return rate_limit.too_many_attempts()

        user = User.objects.filter(**{auth_field: login_value}).first()
        is_password_valid = (
            user is not None
            and user.profile.auth_method != Profile.INTRA
            and check_password(serailizer.validated_data.get("password"), user.password)
        )
        if not is_password_valid:
            rate_limit.record_failure("login-account", account_key)
            rate_limit.record_failure("login-ip", ip_key)
            return ErrorResponse(
                message="These credentials does not match any records.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        rate_limit.reset("login-account", account_key)
        response = SuccessResponse({"user": UserSerializer(user).data})
        return set_access_token(response, user, is_tfa_verified=False)

    return ErrorResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        serializer_errors=serailizer.errors,
    )


@api_view(["POST"])
def register_user(request):
    serializer = RegisterUserSerializer(data=request.data)

    if serializer.is_valid():
        is_user_exists = User.objects.filter(
            username=serializer.validated_data["username"]
        ).exists()
        if is_user_exists:
            return ErrorResponse(message="A user with this username already exists")

        is_user_exists = User.objects.filter(
            email=serializer.validated_data["email"]
        ).exists()

        if is_user_exists:
            return ErrorResponse(message="A user with this email already exists")

        try:
            # User and profile (post_save signal) are created together or not at all.
            with transaction.atomic():
                user = User.objects.create_user(
                    username=serializer.validated_data["username"],
                    email=serializer.validated_data["email"],
                    password=serializer.validated_data["password"],
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                )
        except IntegrityError:
            # Same username registered at the same moment.
            return ErrorResponse(message="A user with this username already exists")
        return SuccessResponse(
            data=UserSerializer(user).data,
            message="You have been registered successfully. Please login to continue.",
        )

    return ErrorResponse(
        status_code=status.HTTP_400_BAD_REQUEST, serializer_errors=serializer.errors
    )


@api_view(["POST"])
@is_authenticated(allow_unverified_tfa=True)
def logout_user(request):
    # Deleting the cookie is not enough: a copy of the token would stay valid
    # until it expires. Revoking ends every session of this user.
    revoke_tokens(request.user)
    response = SuccessResponse(message="User logged out")
    response.delete_cookie("access_token", samesite=settings.AUTH_COOKIE_SAMESITE)
    return response


@api_view(["GET"])
@is_authenticated
def get_user(request):
    user = request.user
    serializer = UserSerializer(user)
    notifications = NotificationSerializer(
        Notification.objects.filter(user=user, is_read=False).order_by("-created_at"), many=True
    )
    return SuccessResponse(
        data={"user": serializer.data, "notifications": notifications.data}
    )


INTRA_STATE_COOKIE = "intra_oauth_state"
INTRA_STATE_MAX_AGE = 10 * 60


@api_view(["GET"])
def login_intra(request):
    client_id = os.getenv("INTRA_CLIENT_ID")
    callback_uri = urllib.parse.quote(
        f'{os.getenv("API_URL")}/api/auth/intra/callback/', safe=""
    )
    # OAuth state: the callback only accepts a code if the browser also
    # holds this value, so an attacker cannot log a victim into the
    # attacker's account with their own code (login CSRF).
    state = secrets.token_urlsafe(32)
    auth_url = (
        f"https://api.intra.42.fr/oauth/authorize?client_id={client_id}"
        f"&redirect_uri={callback_uri}&response_type=code&state={state}"
    )
    response = SuccessResponse(data={"url": auth_url})
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


@api_view(["GET"])
def login_intra_callback(request):
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        return ErrorResponse(message=error)
    if not code:
        return ErrorResponse(message="No code found")

    expected_state = request.get_signed_cookie(
        INTRA_STATE_COOKIE,
        default=None,
        salt=INTRA_STATE_COOKIE,
        max_age=INTRA_STATE_MAX_AGE,
    )
    received_state = request.GET.get("state") or ""
    if not expected_state or not secrets.compare_digest(expected_state, received_state):
        return ErrorResponse(
            message="Login request expired or invalid, please try again.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        intra_response = requests.post(
            "https://api.intra.42.fr/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": os.getenv("INTRA_CLIENT_ID"),
                "client_secret": os.getenv("INTRA_CLIENT_SECRET"),
                "code": code,
                "redirect_uri": f"{os.getenv('API_URL')}/api/auth/intra/callback/",
            },
            timeout=INTRA_TIMEOUT_SECONDS,
        )
        access_token = (
            intra_response.json().get("access_token")
            if intra_response.status_code == 200
            else None
        )
        if not access_token:
            return ErrorResponse(
                message="Failed to get access token",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        intra_response = requests.get(
            "https://api.intra.42.fr/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=INTRA_TIMEOUT_SECONDS,
        )
        if intra_response.status_code != 200:
            return ErrorResponse(
                message="Failed to get user data",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        user_data = parse_intra_user(intra_response.json())
    except (requests.RequestException, ValueError):
        return ErrorResponse(
            message="42 intra is not reachable, please try again later.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    if user_data is None:
        return ErrorResponse(
            message="Failed to get user data", status_code=status.HTTP_401_UNAUTHORIZED
        )

    user = find_or_create_intra_user(user_data)

    response = redirect(settings.FRONTEND_URL)
    response.delete_cookie(INTRA_STATE_COOKIE, samesite="Lax")
    return set_access_token(response, user, is_tfa_verified=False)


@api_view(["POST"])
@is_authenticated
def enable_twofa(request):
    user = request.user
    if user.profile.is_tfa_enabled:
        return ErrorResponse(message="2FA is already enabled")

    secret = pyotp.random_base32()
    user.profile.tfa_secret = secret
    user.profile.save(update_fields=["tfa_secret"])
    tfa_code = pyotp.totp.TOTP(secret).provisioning_uri(
        user.username, issuer_name="ft_transcendence"
    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tfa_code)
    qr.make(fit=True)
    tfa_image = qr.make_image(fill_color="black", back_color="white")
    bufferd = io.BytesIO()
    tfa_image.save(bufferd, format="PNG")
    image = base64.b64encode(bufferd.getvalue())

    return SuccessResponse(
        message="2FA enables",
        data={"image": f'data:image/png;base64,{image.decode("utf-8")}'},
    )


@api_view(["POST"])
@is_authenticated
def confirm_twofa(request):
    user = request.user
    code = request.data.get("code")
    if not code:
        return ErrorResponse(message="No code found")

    if not user.profile.tfa_secret:
        return ErrorResponse(message="2FA is not enabled")

    if rate_limit.is_blocked("tfa-user", user.id):
        return rate_limit.too_many_attempts()
    if not check_totp(user, code):
        return ErrorResponse(message="Invalid code")

    user.profile.is_tfa_enabled = True
    user.profile.save(update_fields=["is_tfa_enabled"])
    # The user just proved they hold the secret, so the current session counts
    # as verified. Without this the next request would be sent back to 2FA.
    response = SuccessResponse(message="2FA confirmed")
    return set_access_token(response, user, is_tfa_verified=True)


@api_view(["POST"])
@is_authenticated(allow_unverified_tfa=True)
def verify_twofa(request):
    user = request.user
    if not user.profile.is_tfa_enabled or not user.profile.tfa_secret:
        return ErrorResponse(message="2FA is not enabled")

    code = request.data.get("code")
    if not code:
        return ErrorResponse(message="No code found")

    if rate_limit.is_blocked("tfa-user", user.id):
        return rate_limit.too_many_attempts()
    if not check_totp(user, code):
        return ErrorResponse(message="Invalid code")

    response = SuccessResponse(message="Code is valid")
    return set_access_token(response, user, is_tfa_verified=True)


@api_view(["POST"])
@is_authenticated
def disable_twofa(request):
    user = request.user
    if not user.profile.is_tfa_enabled or not user.profile.tfa_secret:
        return ErrorResponse(message="2FA is not enabled")

    code = request.data.get("code")
    if not code:
        return ErrorResponse(message="No code found")

    if rate_limit.is_blocked("tfa-user", user.id):
        return rate_limit.too_many_attempts()
    if not check_totp(user, code):
        return ErrorResponse(message="Invalid code")

    user.profile.is_tfa_enabled = False
    user.profile.tfa_secret = None
    user.profile.save(update_fields=["is_tfa_enabled", "tfa_secret"])
    return SuccessResponse(message="2FA disabled successfully")
