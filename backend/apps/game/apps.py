from django.apps import AppConfig


class GameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.game"
    # The label names the tables and the migration history: keep it.
    label = "game"
