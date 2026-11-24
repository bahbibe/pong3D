from django.urls import path

from .views import (
    accept_friend_request,
    block_user,
    get_blocked_friends,
    get_friends,
    get_friends_request,
    get_sent_friends_request,
    send_friend_request,
    unblock_user,
)

urlpatterns = [
    path("", get_friends, name="get-friends"),
    path("blocked/", get_blocked_friends, name="get-blocked-friends"),
    path("send/", send_friend_request, name="send-friend-request"),
    path("requests/", get_friends_request, name="get-friends-request"),
    path("sent-requests/", get_sent_friends_request, name="get-sent-friends-request"),
    path("accept/", accept_friend_request, name="accept-friend-request"),
    path("block/", block_user, name="block-user"),
    path("unblock/", unblock_user, name="unblock-user"),
]
