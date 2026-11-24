"""WebSocket routes of every app (mounted in config/asgi.py)."""

from apps.chat.routing import websocket_urlpatterns as chat_patterns
from apps.game.routing import websocket_urlpatterns as game_patterns
from apps.matchmaking.routing import websocket_urlpatterns as matchmaking_patterns
from apps.notifications.routing import websocket_urlpatterns as notifications_patterns
from apps.presence.routing import websocket_urlpatterns as presence_patterns

websocket_urlpatterns = (
    chat_patterns
    + game_patterns
    + presence_patterns
    + notifications_patterns
    + matchmaking_patterns
)
