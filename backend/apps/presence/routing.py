from django.urls import re_path

from .consumers import FriendsStatusConsumer

websocket_urlpatterns = [
    re_path(r"^ws/status/$", FriendsStatusConsumer.as_asgi()),
]
