from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create two separate routers - one for regular factor endpoints, one for admin
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

# Register admin viewset
admin_router = DefaultRouter(trailing_slash=True)
admin_router.register(
    r"pricing-factors",
    views.AdminPricingFactorsViewSet,
    basename="admin-pricing-factors",
)

urlpatterns = [
    # Include standard factor routes directly
    path("", include(factor_router.urls)),
    # Admin routes
    path("admin/", include(admin_router.urls)),
    path(
        "admin/pricing/factors/",
        views.AdminPricingFactorsViewSet.as_view({"get": "list"}),
        name="admin-pricing-factors",
    ),
    path(
        "admin/price-configurations/",
        views.PricingConfigurationViewSet.as_view({"get": "list", "post": "create"}),
        name="admin-price-configuration",
    ),
    path(
        "admin/price-configuration/<str:pk>/",
        views.PricingConfigurationViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="admin-price-configuration-detail",
    ),
]
