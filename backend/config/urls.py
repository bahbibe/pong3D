from django.contrib import admin
from django.urls import include, path

from .health import healthz

urlpatterns = [
    path("api/chat/", include("apps.chat.urls")),
    path("api/auth/notifications/", include("apps.notifications.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/friends/", include("apps.friends.urls")),
    path("admin/", admin.site.urls),
    path("api/game/", include("apps.game.urls")),
    # Container healthcheck (not proxied by nginx).
    path("healthz", healthz, name="healthz"),
    # /metrics for Prometheus (not proxied by nginx).
    path("", include("django_prometheus.urls")),
]
