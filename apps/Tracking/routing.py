# realtimeTracking/routing.py
from django.urls import re_path, path
from .consumers import DriverTrackingConsumer

websocket_urlpatterns = [
    re_path(
        r'^ws/tracking/driver/(?P<driver_id>\d+)/$',  # Add ^ and $
        DriverTrackingConsumer.as_asgi()
    ),
]