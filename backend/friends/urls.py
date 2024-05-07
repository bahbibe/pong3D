from django.urls import path
from .views import (
    get_friends,
    get_friends_request,
    send_friend_request,
    accept_friend_request,
    update_friendship_status,
)


urlpatterns = [
    path("friends/", get_friends, name="get-friends"),
    path("friends/requests/", get_friends_request, name="get-friends-request"),
    path("friends/accept/", accept_friend_request, name="accept-friend-request"),
    path("friends/update/", update_friendship_status, name="update-friendship-status"),
    path("send-friend-request/", send_friend_request, name="send-friend-request"),
]
