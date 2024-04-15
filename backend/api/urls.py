from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

def hello(request):
  return JsonResponse({'status': "success", "message": "Hello World!" })
  
urlpatterns = [
  path('', hello)
]
