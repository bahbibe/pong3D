from django.urls import path
from . import consumer

websocket_urlpatterns = [
    path('ws/friends-status/', consumer.FriendsStatusConsumer.as_asgi()),
]
