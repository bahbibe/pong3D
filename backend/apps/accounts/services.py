"""Account writes: register, password login, profile setup, settings.
Errors are core.errors.ServiceError with the message for the user."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import status

from core.errors import ServiceError

from . import rate_limit
from .models import Profile
from .selectors import email_taken, username_taken

User = get_user_model()


def register(username, email, password, first_name, last_name):
    if username_taken(username):
        raise ServiceError("A user with this username already exists")
    if email_taken(email):
        raise ServiceError("A user with this email already exists")
    try:
        # User and profile (post_save signal) are created together or not at all.
        with transaction.atomic():
            return User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
    except IntegrityError:
        # Same username or email registered at the same moment.
        raise ServiceError("A user with this username or email already exists")


def login(password, ip, email=None, username=None):
    """The user for these credentials. Failures are counted per account and
    per IP (rate_limit); intra accounts have no password here."""
    if email is None and username is None:
        raise ServiceError("An email or username is required to log in.")
    field, value = ("email", str(email)) if email is not None else ("username", str(username))
    account_key = f"{field}:{value.lower()}"
    rate_limit.check("login-account", account_key)
    rate_limit.check("login-ip", ip)

    lookup = "email__iexact" if field == "email" else "username"
    user = User.objects.filter(**{lookup: value}).first()
    if (
        user is None
        or user.profile.auth_method == Profile.INTRA
        or not check_password(password, user.password)
    ):
        rate_limit.record_failure("login-account", account_key)
        rate_limit.record_failure("login-ip", ip)
        raise ServiceError(
            "These credentials does not match any records.", status.HTTP_404_NOT_FOUND
        )
    rate_limit.reset("login-account", account_key)
    return user


def setup_profile(user, data):
    """`data`: SetupProfileSerializer.validated_data (username, avatar)."""
    if username_taken(data.get("username"), exclude_user=user):
        raise ServiceError("Username already exists, Please try another one.")
    profile = user.profile
    profile.avatar = data.get("avatar", profile.avatar)
    profile.is_setup = True
    user.username = data.get("username", user.username)
    profile.save(update_fields=["avatar", "is_setup"])
    user.save()
    return user


def update_settings(user, data):
    """`data`: UpdateSettingsSerializer.validated_data. Returns True when
    the password changed: the caller then revokes the other sessions and
    issues a new token."""
    profile = user.profile
    username = data.get("username")
    email = data.get("email") or None
    password = data.get("password") or None
    current_password = data.get("current_password") or ""
    is_email_change = email is not None and email.lower() != user.email.lower()

    if password or is_email_change:
        # Changing credentials needs proof that the caller is the account
        # owner, not just someone holding the session cookie.
        if profile.auth_method == Profile.INTRA or not user.has_usable_password():
            raise ServiceError("Email and password are managed by 42 intra for this account.")
        if not user.check_password(current_password):
            raise ServiceError(
                "Current password is incorrect.",
                errors={"current_password": ["Current password is incorrect."]},
            )

    if username and username != user.username and username_taken(username):
        raise ServiceError("Username already exists")
    if is_email_change and email_taken(email, exclude_user=user):
        raise ServiceError("Email already exists")
    if password:
        try:
            validate_password(password, user=user)
        except DjangoValidationError as error:
            raise ServiceError("Invalid password", errors={"password": list(error.messages)})

    profile.avatar = data.get("avatar", profile.avatar)
    if username:
        user.username = username
    if is_email_change:
        user.email = email
    if password:
        user.set_password(password)
    try:
        with transaction.atomic():
            profile.save(update_fields=["avatar"])
            user.save()
    except IntegrityError:
        # Username or email taken by another request at the same moment.
        raise ServiceError("Username or email already exists")
    return bool(password)
