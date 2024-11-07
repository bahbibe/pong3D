from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # re_path("ws/game/random", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/game/(?P<game_id>\w+)$", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/game/tournament/(?P<tournament_id>\w+)/$", consumers.GameConsumer.as_asgi()),
]