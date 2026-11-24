from django.apps import AppConfig


class PresenceConfig(AppConfig):
    # No models: online status lives in Redis (see consumers.py).
    name = "apps.presence"
    label = "presence"
