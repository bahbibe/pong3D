from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    # Was the "api" app. The label names the tables (api_profile, ...) and
    # the migration history: keep it.
    label = "api"

    def ready(self):
        from . import schema, signals  # noqa: F401  (OpenAPI auth scheme, post_save handler)
