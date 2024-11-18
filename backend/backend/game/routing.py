from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # re_path("ws/game/random", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/game/(?P<game_id>\w+)$", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/game/(?P<tournament_id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})/(?P<game_id>\w+)$", consumers.GameConsumer.as_asgi()),
    re_path(r"ws/tournament/(?P<tournament_id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})$", consumers.TournamentConsumer.as_asgi()),
]