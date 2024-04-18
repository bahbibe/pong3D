from django.urls import path
from django.http import JsonResponse
from .auth_views import register_user, get_user

def hello(request):
  return JsonResponse({'status': "success", "message": "Hello World!" })
  
urlpatterns = [
  path('', hello),
  path('register/', register_user, name='register'),
  path('me/', get_user, name='current_user')
]
