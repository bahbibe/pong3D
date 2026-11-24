"""Read queries about users and profiles."""

from django.contrib.auth import get_user_model

from apps.friends.selectors import blocked_user_ids, is_blocked
from core.errors import NotFound
from core.uuids import parse_uuid

from .models import Profile

MAX_SEARCH_RESULTS = 50


def email_taken(email, exclude_user=None):
    """Emails are unique case-insensitively (index auth_user_email_ci_unique)."""
    users = get_user_model().objects.filter(email__iexact=email)
    if exclude_user is not None:
        users = users.exclude(id=exclude_user.id)
    return users.exists()


def username_taken(username, exclude_user=None):
    users = get_user_model().objects.filter(username=username)
    if exclude_user is not None:
        users = users.exclude(id=exclude_user.id)
    return users.exists()


def _visible(profile, viewer):
    """The profile's user, unless missing or on the other side of a block."""
    if profile is None or is_blocked(profile.user, viewer):
        raise NotFound("User does not exist")
    return profile.user


def user_by_profile_uuid(value, viewer):
    profile_uuid = parse_uuid(value)
    profile = (
        Profile.objects.select_related("user").filter(uuid=profile_uuid).first()
        if profile_uuid
        else None
    )
    return _visible(profile, viewer)


def user_by_profile_id(value, viewer):
    profile = (
        Profile.objects.select_related("user").filter(id=value).first()
        if str(value).isdigit()
        else None
    )
    return _visible(profile, viewer)


def search_users(viewer, query=""):
    """By username only, without users on the other side of a block."""
    users = (
        get_user_model()
        .objects.exclude(id__in=blocked_user_ids(viewer))
        .select_related("profile")
        .order_by("username")
    )
    query = (query or "").strip()
    if query:
        users = users.filter(username__icontains=query)
    return users[:MAX_SEARCH_RESULTS]
