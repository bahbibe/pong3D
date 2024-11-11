from django.urls import path

from . import views

urlpatterns = [
    path("history/", views.history, name="history"),
    path("stats/", views.stats, name="stats"),
    path("create_tournament/", views.create_tournament, name="create_tournament"),
    path("get_tournaments/", views.get_tournaments, name="get_tournaments"),
    path("join_tournament/<tournament_id>", views.join_tournament, name="join_tournament"),
    path("get_participants/<tournament_id>", views.get_participants, name="get_participants"),
]