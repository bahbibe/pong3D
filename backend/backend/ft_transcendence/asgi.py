import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from chat.middleware import WSAuthMiddleware
from chat.routing import websocket_urlpatterns as chat_patterns
from game.routing import websocket_urlpatterns as game_patterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ft_transcendence.settings")

django_asgi_application = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket":AllowedHostsOriginValidator(AuthMiddlewareStack(WSAuthMiddleware(URLRouter(chat_patterns + game_patterns)))),
    }
)

