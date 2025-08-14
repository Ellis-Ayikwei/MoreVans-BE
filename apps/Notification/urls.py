from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
]

# Individual endpoints for easier access
app_name = "notifications"

# The router creates these endpoints:
# GET /api/notifications/ - List notifications
# POST /api/notifications/ - Create notification (staff only)
# GET /api/notifications/{id}/ - Get specific notification
# PUT/PATCH /api/notifications/{id}/ - Update notification
# DELETE /api/notifications/{id}/ - Delete notification
#
# Custom endpoints:
# POST /api/notifications/{id}/mark_as_read/ - Mark notification as read
# POST /api/notifications/mark_all_as_read/ - Mark all as read
# GET /api/notifications/unread_count/ - Get unread count
# GET /api/notifications/summary/ - Get notification summary
# DELETE /api/notifications/clear_read/ - Delete all read notifications
# GET/POST /api/notifications/preferences/ - Get/update preferences
# POST /api/notifications/test_notification/ - Send test notification (staff only)
