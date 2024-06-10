from django.urls import path
from .views import get_messages

urlpatterns = [
    path('<str:conversation_name>/', get_messages, name='get_messages'),
]