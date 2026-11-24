from django.urls import re_path

from .views import get_messages

urlpatterns = [
    re_path(r"^messages/(?P<conversation>[^/]+)/$", get_messages, name="get_messages"),
]
