from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("history/", views.history, name="history"),
    path("stats/", views.stats, name="stats"),
    path("<str:game_id>/", views.game, name="game"),
]