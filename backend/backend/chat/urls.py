from django.urls import path
from .views import get_messages

urlpatterns = [
    path('<str:conversation>/', get_messages, name='get_messages'),
]