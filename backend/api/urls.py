from django.urls import path
from django.http import JsonResponse
from .auth_views import register_user, get_user
from .views import (
    setup_profile,
    send_friend_request,
    accept_friend_request,
    get_friends,
    get_friends_request,
    update_settings,
    get_profile,
    block_user,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView, TokenRefreshView


def hello():
    return JsonResponse({"status": "success", "message": "Hello World!"})


urlpatterns = [
    path("", hello),
    path("register/", register_user, name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("me/", get_user, name="user"),
    path("setup/", setup_profile, name="setup-profile"),
    path("settings/update/", update_settings, name="update-settings"),
    path("profile/<str:uuid>/", get_profile, name="get-profile"),
    # friends api ulrpatterns
    path("friends/", get_friends, name="get-friends"),
    path("friends-requests/", get_friends_request, name="get-friends-request"),
    path("send-friend-request/", send_friend_request, name="send-friend-request"),
    path("accept-friend-request/", accept_friend_request, name="accept-friend-request"),
    path("block-user/", block_user, name="block-user"),
]
