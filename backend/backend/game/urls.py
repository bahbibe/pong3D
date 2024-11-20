from django.urls import path

from . import views

urlpatterns = [
    path("history/", views.history, name="history"),
    path("stats/", views.stats, name="stats"),
    path("leaderboard/", views.get_leaderboard, name="leaderboard"),
    path("create_tournament/", views.create_tournament, name="create_tournament"),
    path("get_tournaments/", views.get_tournaments, name="get_tournaments"),
    path(
        "get_tournament_games/<tournament_id>",
        views.get_tournament_games,
        name="get_tournament_games",
    ),
    path("get_game/<game_id>", views.get_game, name="get_game"),
]
