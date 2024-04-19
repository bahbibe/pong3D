from django.urls import path
from django.http import JsonResponse
from .auth_views import register_user, get_user
from rest_framework_simplejwt.views import TokenObtainPairView

def hello(request):
  return JsonResponse({'status': "success", "message": "Hello World!" })
  
urlpatterns = [
  path('', hello),
  path('register/', register_user, name='register'),
  path('login/', TokenObtainPairView.as_view(), name='login'),
  path('me/', get_user, name='user'),
]
