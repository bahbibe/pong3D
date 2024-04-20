from django.urls import path
from django.http import JsonResponse
from .auth_views import register_user, get_user
from .views import setup_profile, send_friend_request
from rest_framework_simplejwt.views import TokenObtainPairView

def hello(request):
  return JsonResponse({'status': "success", "message": "Hello World!" })
  
urlpatterns = [
  path('', hello),
  path('register/', register_user, name='register'),
  path('login/', TokenObtainPairView.as_view(), name='login'),
  path('me/', get_user, name='user'),
  path('setup/', setup_profile, name='setup-profile'),
  path('send-friend-request/', send_friend_request, name='send-friend-request'),
]
