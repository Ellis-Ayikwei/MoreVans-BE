from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemSettingsViewSet, PaymentGatewayViewSet

router = DefaultRouter()
router.register(r"system-settings", SystemSettingsViewSet)
router.register(r"payment-gateways", PaymentGatewayViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
