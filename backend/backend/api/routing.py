from django.urls import re_path
from chat.consumers import ChatConsumer
from game.consumers import GameConsumer
from .consumer import FriendsStatusConsumer

websocket_urlpatterns = [
    re_path('ws/chat/$', ChatConsumer.as_asgi()),
    re_path('ws/game/$', GameConsumer.as_asgi()),
    re_path('ws/friend-status/$', FriendsStatusConsumer.as_asgi()),
]
