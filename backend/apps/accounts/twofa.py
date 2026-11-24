"""TOTP two-factor authentication. Errors are core.errors.ServiceError."""

import base64
import io

import pyotp
import qrcode
from django.db.models import Q
from django.utils import timezone

from core.errors import ServiceError

from . import rate_limit
from .models import Profile

# Shown in authenticator apps. Kept from the 42 project name: changing it
# would rename the entry of every user who already set up 2FA.
ISSUER = "ft_transcendence"


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


def _require_code(code):
    if not code:
        raise ServiceError("No code found")


def _check(user, code):
    rate_limit.check("tfa-user", user.id)
    if not check_totp(user, code):
        raise ServiceError("Invalid code")


def start(user):
    """New secret for `user` (2FA is on only after confirm()). Returns the
    QR code to scan, as a data: URL."""
    if user.profile.is_tfa_enabled:
        raise ServiceError("2FA is already enabled")
    secret = pyotp.random_base32()
    user.profile.tfa_secret = secret
    user.profile.save(update_fields=["tfa_secret"])
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.username, issuer_name=ISSUER)
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4
    )
    qr.add_data(uri)
    qr.make(fit=True)
    buffer = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def confirm(user, code):
    """Turn 2FA on with a first valid code."""
    _require_code(code)
    if not user.profile.tfa_secret:
        raise ServiceError("2FA is not enabled")
    _check(user, code)
    user.profile.is_tfa_enabled = True
    user.profile.save(update_fields=["is_tfa_enabled"])


def _require_enabled(user):
    if not user.profile.is_tfa_enabled or not user.profile.tfa_secret:
        raise ServiceError("2FA is not enabled")


def verify(user, code):
    """The login step after the password."""
    _require_enabled(user)
    _require_code(code)
    _check(user, code)


def disable(user, code):
    _require_enabled(user)
    _require_code(code)
    _check(user, code)
    user.profile.is_tfa_enabled = False
    user.profile.tfa_secret = None
    user.profile.save(update_fields=["is_tfa_enabled", "tfa_secret"])
