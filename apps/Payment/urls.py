from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentMethodViewSet,
    PaymentViewSet,
    StripeWebhookView,
    StripeConfigView,
    stripe_webhook,
)

router = DefaultRouter()
router.register(r"payment-methods", PaymentMethodViewSet)
router.register(r"payments", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "payments-webhook/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"
    ),
    path("config/", StripeConfigView.as_view(), name="stripe-config"),
    path(
        "stripe-webhook/", stripe_webhook, name="legacy-stripe-webhook"
    ),  # Legacy support
]
