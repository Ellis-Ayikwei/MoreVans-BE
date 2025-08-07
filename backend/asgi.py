import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.Tracking.routing import websocket_urlpatterns as tracking_websocket_urlpatterns
from apps.Message.routing import websocket_urlpatterns as message_websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Combine WebSocket URL patterns from different apps
all_websocket_urlpatterns = tracking_websocket_urlpatterns + message_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            all_websocket_urlpatterns
        )
    ),
})
