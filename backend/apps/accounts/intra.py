"""42 intra OAuth login: authorize URL, code exchange, account lookup."""

import os
import random
import secrets
import string
import urllib.parse

import requests
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status

from core.errors import ServiceError

from .models import Profile
from .selectors import email_taken

User = get_user_model()

INTRA_TIMEOUT_SECONDS = 10


def callback_url():
    return f"{os.getenv('API_URL')}/api/auth/intra/callback/"


def new_state():
    """OAuth state: the callback only accepts a code if the browser also
    holds this value, so an attacker cannot log a victim into the
    attacker's account with their own code (login CSRF)."""
    return secrets.token_urlsafe(32)


def authorize_url(state):
    return (
        f"https://api.intra.42.fr/oauth/authorize?client_id={os.getenv('INTRA_CLIENT_ID')}"
        f"&redirect_uri={urllib.parse.quote(callback_url(), safe='')}"
        f"&response_type=code&state={state}"
    )


def fetch_user_data(code):
    """Exchange the OAuth code and read /v2/me. Returns parse_intra_user()'s
    dict, or raises ServiceError with the message shown to the user."""
    try:
        response = requests.post(
            "https://api.intra.42.fr/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": os.getenv("INTRA_CLIENT_ID"),
                "client_secret": os.getenv("INTRA_CLIENT_SECRET"),
                "code": code,
                "redirect_uri": callback_url(),
            },
            timeout=INTRA_TIMEOUT_SECONDS,
        )
        access_token = response.json().get("access_token") if response.status_code == 200 else None
        if not access_token:
            raise ServiceError("Failed to get access token", status.HTTP_401_UNAUTHORIZED)

        response = requests.get(
            "https://api.intra.42.fr/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=INTRA_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            raise ServiceError("Failed to get user data", status.HTTP_401_UNAUTHORIZED)
        user_data = parse_intra_user(response.json())
    except (requests.RequestException, ValueError):
        raise ServiceError(
            "42 intra is not reachable, please try again later.", status.HTTP_502_BAD_GATEWAY
        )
    if user_data is None:
        raise ServiceError("Failed to get user data", status.HTTP_401_UNAUTHORIZED)
    return user_data


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

    # Emails are unique but never verified at registration. When the 42
    # email is already used, create the intra account without an email
    # instead of linking: someone could have registered the victim's 42
    # email first, and linking would hand them the victim's account.
    email = user_data["email"]
    if email and email_taken(email):
        email = ""

    for _ in range(3):
        username = user_data["username"]
        while User.objects.filter(username=username).exists():
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"{user_data['username']}_{suffix}"
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
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
        except IntegrityError:
            # Username or email taken at the same moment. A second login of
            # the same intra user wins the intra_id race: return that account.
            profile = (
                Profile.objects.select_related("user")
                .filter(intra_id=user_data["id"])
                .first()
            )
            if profile:
                return profile.user
            email = ""
            continue
        user.refresh_from_db()
        return user
    raise IntegrityError("could not create the intra account")
