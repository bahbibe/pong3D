from django.urls import path
from .views import (
    get_friends,
    get_friends_request,
    send_friend_request,
    accept_friend_request,
    update_friendship_status,
)


urlpatterns = [
    path("", get_friends, name="get-friends"),
    path("requests/", get_friends_request, name="get-friends-request"),
    path("accept/", accept_friend_request, name="accept-friend-request"),
    path("update/", update_friendship_status, name="update-friendship-status"),
    path("send/", send_friend_request, name="send-friend-request"),
]
