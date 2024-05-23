from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings


def redirect_to_api(request):
    return redirect("api/")


urlpatterns = [
    path("", redirect_to_api),
    path("api/auth/", include("api.urls")),
    path("api/friends/", include("friends.urls")),
    path("api/tournaments/", include("tournaments.urls")),
    path("api/chat/", include("chat.urls")),
    path("admin/", admin.site.urls),
]

urlpatterns += static("/avatars/", document_root=settings.BASE_DIR / "avatars/")

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
