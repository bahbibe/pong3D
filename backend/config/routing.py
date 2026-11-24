"""WebSocket routes of every app (mounted in config/asgi.py)."""

from apps.accounts.routing import websocket_urlpatterns as accounts_patterns
from apps.chat.routing import websocket_urlpatterns as chat_patterns
from apps.game.routing import websocket_urlpatterns as game_patterns
from apps.matchmaking.routing import websocket_urlpatterns as matchmaking_patterns

websocket_urlpatterns = (
    chat_patterns + game_patterns + accounts_patterns + matchmaking_patterns
)
