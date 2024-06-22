from django.urls import path, re_path
from .consumers import ChatConsumer , NotificationConsumer


websocket_urlpatterns = [
   re_path(r"^ws/notify/$", NotificationConsumer.as_asgi()),
   re_path(r"^ws/chat/(?P<conversation>[\w-]+)/$", ChatConsumer.as_asgi()),
]
