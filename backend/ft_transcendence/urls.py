from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView


def redirect_to_api(request):
    return redirect('api/')

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]

urlpatterns += static("/avatars/", document_root=settings.BASE_DIR/"avatars/")

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
