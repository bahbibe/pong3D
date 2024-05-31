from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path('', views.chat, name='chat'),
    path('chat/login/', LoginView.as_view(template_name='chat/login.html', form_class=views.ChatLoginForm), name='chat_login'),
    # path('chat/logout/', views.chat_logout, name='chat_logout'),
    # path('chat/messages/', views.chat_messages, name='chat_messages'),
]
