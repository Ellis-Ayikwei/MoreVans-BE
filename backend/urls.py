"""
WasteWise Backend URL Configuration

The main URL configuration for the WasteWise Smart Waste Management System.
Includes API endpoints, admin interface, and documentation.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# API URL patterns
api_v1_patterns = [
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/', include('apps.Authentication.urls')),  # Legacy auth endpoints
    
    # WasteWise Core API endpoints
    path('bins/', include('apps.wastewise.bins.urls')),
    path('sensors/', include('apps.wastewise.sensors.urls')),
    path('routes/', include('apps.wastewise.routes.urls')),
    path('vehicles/', include('apps.wastewise.vehicles.urls')),
    path('users/', include('apps.wastewise.users.urls')),
    path('alerts/', include('apps.wastewise.alerts.urls')),
    path('analytics/', include('apps.wastewise.analytics.urls')),
    path('notifications/', include('apps.wastewise.notifications.urls')),
    path('reports/', include('apps.wastewise.reports.urls')),
    
    # Legacy endpoints (for backward compatibility)
    path('legacy/', include([
        path('notifications/', include('apps.Notification.urls')),
        path('messages/', include('apps.Message.urls')),
        path('users/', include('apps.User.urls')),
    ])),
]

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/v1/', include(api_v1_patterns)),
    
    # Health check endpoints
    path('health/', include('health_check.urls')),
    
    # WebSocket endpoints (for real-time features)
    # Note: These are handled by ASGI routing in production
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "WasteWise Administration"
admin.site.site_title = "WasteWise Admin"
admin.site.index_title = "Smart Waste Management System"
