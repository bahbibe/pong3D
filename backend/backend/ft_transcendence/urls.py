from django.contrib import admin
from django.urls import path, include

from .health import healthz

urlpatterns = [
    path("api/chat/", include("chat.urls")),
    path("api/auth/", include("api.urls")),
    path("api/friends/", include("friends.urls")),
    path("admin/", admin.site.urls),
    path("api/game/", include("game.urls")),
    # Container healthcheck (not proxied by nginx).
    path("healthz", healthz, name="healthz"),
    # /metrics for Prometheus (not proxied by nginx).
    path("", include("django_prometheus.urls")),
]
