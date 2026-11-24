from django.urls import path

from .auth_views import (
    confirm_twofa,
    disable_twofa,
    enable_twofa,
    get_user,
    login_intra,
    login_intra_callback,
    login_user,
    logout_user,
    register_user,
    verify_twofa,
)
from .views import (
    get_profile,
    get_profile_with_id,
    get_users,
    setup_profile,
    update_settings,
)

urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("intra/", login_intra, name="intra-login"),
    path("intra/callback/", login_intra_callback, name="intra-callback"),
    path("logout/", logout_user, name="logout"),
    path("twofa/enable/", enable_twofa, name="enable-towfa"),
    path("twofa/confirm/", confirm_twofa, name="confirm-towfa"),
    path("twofa/verify/", verify_twofa, name="verify-towfa"),
    path("twofa/disable/", disable_twofa, name="disable-towfa"),
    path("me/", get_user, name="user"),
    path("setup/", setup_profile, name="setup-profile"),
    path("settings/update/", update_settings, name="update-settings"),
    path("profile/<str:uuid>/", get_profile, name="get-profile"),
    path("user/<str:id>/", get_profile_with_id, name="get-profile-with-id"),
    path("users/", get_users, name="get-users"),
]
