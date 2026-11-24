from django.apps import AppConfig


class FriendsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.friends"
    # The label names the tables and the migration history: keep it.
    label = "friends"
