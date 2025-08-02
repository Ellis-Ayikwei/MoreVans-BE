"""
URL configuration for Waste Wise project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# API Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Waste Wise API",
        default_version='v1',
        description="Smart Waste Management System API Documentation",
        terms_of_service="https://www.wastewise.com/terms/",
        contact=openapi.Contact(email="contact@wastewise.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API v1
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/bins/', include('apps.bins.urls')),
    path('api/v1/sensors/', include('apps.sensors.urls')),
    path('api/v1/routes/', include('apps.routes.urls')),
    path('api/v1/alerts/', include('apps.alerts.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    
    # Prometheus metrics
    path('', include('django_prometheus.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Custom admin site configuration
admin.site.site_header = "Waste Wise Admin"
admin.site.site_title = "Waste Wise Admin Portal"
admin.site.index_title = "Welcome to Waste Wise Management System"