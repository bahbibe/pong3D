from django.urls import path
from django.http import JsonResponse
from .auth_views import (
    login_user,
    register_user,
    get_user,
    login_intra,
    login_intra_callback,
    logout_user,
    enable_twofa,
    confirm_twofa,
    verify_twofa,
    disable_twofa,
)
from .views import (
    setup_profile,
    update_settings,
    get_profile,
    get_users,
    get_profile_with_id,
    mark_all_notifications_as_read,
    mark_notification_as_read
)


# def hello():
#     return JsonResponse({"status": "success", "message": "Hello World!"})


urlpatterns = [
    # path("", hello),
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
    path("notifications/mark_as_read/", mark_all_notifications_as_read, name="mark-notifications-as-read"),
    path("notifications/mark_as_read/<str:uuid>/", mark_notification_as_read, name="mark-notification-as-read"),
]
