"""
ASGI config for Waste Wise project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import routing after Django setup
django_asgi_app = get_asgi_application()

from apps.sensors import routing as sensors_routing
from apps.alerts import routing as alerts_routing

# Combine all WebSocket URL patterns
websocket_urlpatterns = []
websocket_urlpatterns.extend(sensors_routing.websocket_urlpatterns)
websocket_urlpatterns.extend(alerts_routing.websocket_urlpatterns)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})