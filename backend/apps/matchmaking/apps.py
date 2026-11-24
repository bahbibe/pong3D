from django.apps import AppConfig


class MatchmakingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.matchmaking"
    # The label names the tables and the migration history: keep it.
    label = "matchmaking"
