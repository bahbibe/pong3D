from django.urls import path
from . import consumer
from game.consumers import GameConsumer

websocket_urlpatterns = [
    path('ws/friends-status/', consumer.FriendsStatusConsumer.as_asgi()),
    path("ws/game/", GameConsumer.as_asgi()),
]
