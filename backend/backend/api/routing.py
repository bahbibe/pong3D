from django.urls import re_path, path
from chat.consumers import ChatConsumer
from game.consumers import GameConsumer
from .consumer import FriendsStatusConsumer, NotificationConusmer

websocket_urlpatterns = [
    re_path(r"^ws/status/$", FriendsStatusConsumer.as_asgi()),
    re_path(r"^ws/notifications/$", NotificationConusmer.as_asgi()),
]
