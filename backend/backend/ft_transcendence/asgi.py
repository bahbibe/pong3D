import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ft_transcendence.settings")

# Set up Django before importing anything that touches models (consumers,
# middleware). Under plain daphne nothing else has called django.setup().
django_asgi_application = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from chat.middleware import WSAuthMiddleware  # noqa: E402
from chat.routing import websocket_urlpatterns as chat_patterns  # noqa: E402
from game.routing import websocket_urlpatterns as game_patterns  # noqa: E402
from matchmaking.routing import websocket_urlpatterns as matchmaking_patterns  # noqa: E402
from api.routing import websocket_urlpatterns as api_patterns  # noqa: E402


application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                WSAuthMiddleware(
                    URLRouter(
                        chat_patterns
                        + game_patterns
                        + api_patterns
                        + matchmaking_patterns
                    )
                )
            )
        ),
    }
)
