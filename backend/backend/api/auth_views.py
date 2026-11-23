from rest_framework.decorators import api_view
from .serializers import (
    RegisterUserSerializer,
    UserSerializer,
    SetupProfileSerializer,
    LoginUserSerializer,
    NotificationSerializer,
)
from rest_framework import status, viewsets
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Profile, Notification
from django.shortcuts import redirect
from django.contrib.auth.hashers import check_password
from .auth_utils import is_authenticated, set_access_token
from django.conf import settings
from utils.responses import ErrorResponse, SuccessResponse
import urllib.parse
import requests
import os
import random
import string
import pyotp.totp
import qrcode
import base64
import io


class RegisterUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SetupProfileSerializer
    parser_classes = [MultiPartParser, FormParser]


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
        user = User.objects.filter(
            **{auth_field: serailizer.validated_data.get(auth_field)}
        ).first()
        if user is None or user.profile.auth_method == Profile.INTRA:
            return ErrorResponse(
                message="These credentials does not match any records.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        is_password_valid = check_password(
            serailizer.validated_data.get("password"), user.password
        )
        if not is_password_valid:
            return ErrorResponse(
                message="These credentials does not match any records.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

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

        user = User.objects.create_user(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data["first_name"],
            last_name=serializer.validated_data["last_name"],
        )
        Profile.objects.create(user=user)
        user.save()
        return SuccessResponse(
            data=UserSerializer(user).data,
            message="You have been registered successfully. Please login to continue.",
        )

    return ErrorResponse(
        status_code=status.HTTP_400_BAD_REQUEST, serializer_errors=serializer.errors
    )


@api_view(["POST"])
@is_authenticated(allow_unverified_tfa=True)
def logout_user(_):
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


@api_view(["GET"])
def login_intra(request):
    client_id = os.getenv("INTRA_CLIENT_ID")
    callback_uri = urllib.parse.quote(
        f'{os.getenv("API_URL")}/api/auth/intra/callback/', safe=""
    )
    auth_url = f"https://api.intra.42.fr/oauth/authorize?client_id={client_id}&redirect_uri={callback_uri}&response_type=code"
    return SuccessResponse(data={"url": auth_url})


@api_view(["GET"])
def login_intra_callback(request):
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        return ErrorResponse(message=error)
    if not code:
        return ErrorResponse(message="No code found")

    intra_response = requests.post(
        "https://api.intra.42.fr/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": os.getenv("INTRA_CLIENT_ID"),
            "client_secret": os.getenv("INTRA_CLIENT_SECRET"),
            "code": code,
            "redirect_uri": f"{os.getenv('API_URL')}/api/auth/intra/callback/",
        },
    )

    if intra_response.status_code != 200:
        return ErrorResponse(
            message="Failed to get access token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    json_response = intra_response.json()
    access_token = json_response["access_token"]
    if not access_token:
        return ErrorResponse(
            message="Failed to get access token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    intra_response = requests.get(
        "https://api.intra.42.fr/v2/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if intra_response.status_code != 200:
        return ErrorResponse(
            message="Failed to get user data", status_code=status.HTTP_401_UNAUTHORIZED
        )

    json_response = intra_response.json()
    user_data = {
        "id": json_response["id"],
        "username": json_response["login"],
        "email": json_response["email"],
        "first_name": json_response["first_name"],
        "last_name": json_response["last_name"],
        "avatar": json_response["image"]["link"],
    }
    
    user = None
    profile = Profile.objects.filter(intra_id=user_data["id"]).first()
    if profile:
        user = profile.user
    else:
        user = User.objects.filter(username=user_data["username"]).first()
        if user and user.profile.auth_method != Profile.INTRA:
            user_data["username"] = (
                f"{user_data['username']}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
            )
            user = None

    if user is None:
        user = User.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
        )
        Profile.objects.create(
            user=user,
            avatar=user_data["avatar"],
            auth_method=Profile.INTRA,
            intra_id=user_data["id"],
        )
        user.set_unusable_password()
        user.save()

    response = redirect(settings.FRONTEND_URL)
    return set_access_token(response, user, is_tfa_verified=False)


@api_view(["POST"])
@is_authenticated
def enable_twofa(request):
    user = request.user
    if user.profile.is_tfa_enabled:
        return ErrorResponse(message="2FA is already enabled")

    secret = pyotp.random_base32()
    user.profile.tfa_secret = secret
    user.profile.save()
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

    secret = user.profile.tfa_secret
    is_code_valid = pyotp.TOTP(secret).verify(code)
    if not is_code_valid:
        return ErrorResponse(message="Invalid code")

    user.profile.is_tfa_enabled = True
    user.profile.save()
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

    is_code_valid = pyotp.TOTP(user.profile.tfa_secret).verify(code)
    if not is_code_valid:
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

    if not pyotp.TOTP(user.profile.tfa_secret).verify(str(code)):
        return ErrorResponse(message="Invalid code")

    user.profile.is_tfa_enabled = False
    user.profile.tfa_secret = None
    user.profile.save()
    return SuccessResponse(message="2FA disabled successfully")
