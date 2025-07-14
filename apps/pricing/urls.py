from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for all pricing factor viewsets
factor_router = DefaultRouter(trailing_slash=True)
factor_router.register(r"distance", views.DistancePricingViewSet)
factor_router.register(r"weight", views.WeightPricingViewSet)
factor_router.register(r"time", views.TimePricingViewSet)
factor_router.register(r"weather", views.WeatherPricingViewSet)
factor_router.register(r"vehicle-type", views.VehicleTypePricingViewSet)
factor_router.register(r"special-requirements", views.SpecialRequirementsPricingViewSet)
factor_router.register(r"location", views.LocationPricingViewSet)
factor_router.register(r"service-level", views.ServiceLevelPricingViewSet)
factor_router.register(r"staff-required", views.StaffRequiredPricingViewSet)
factor_router.register(r"property-type", views.PropertyTypePricingViewSet)
factor_router.register(r"insurance", views.InsurancePricingViewSet)
factor_router.register(r"loading-time", views.LoadingTimePricingViewSet)

# Create router for admin viewsets
factors_router = DefaultRouter(trailing_slash=True)
factors_router.register(
    r"pricing-factors",
    views.PricingFactorsViewSet,
    basename="pricing-factors",
)

# Create router for pricing configurations
config_router = DefaultRouter(trailing_slash=True)
config_router.register(
    r"price-configurations",
    views.PricingConfigurationViewSet,
    basename="price-configuration",
)

urlpatterns = [
    # Include all pricing factor routes
    path("pricing/factors/", include(factor_router.urls)),
    # Include admin routes
    path("", include(factors_router.urls)),
    # Include pricing configuration routes
    path("", include(config_router.urls)),
]
