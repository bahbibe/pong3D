from django.urls import path
from .views import (
    get_tournaments,
    create_tournament,
    join_tournament,
    kick_player,
)


urlpatterns = [
    path("", get_tournaments, name="get-tournaments"),
    path("create/", create_tournament, name="create-tournament"),
    path("join/<str:tournament_uuid>/", join_tournament, name="join-tournament"),
    path("kick/<str:tournament_uuid>/", kick_player, name="kick-tournament"),
]
