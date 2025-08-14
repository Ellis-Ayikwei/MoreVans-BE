# urls.py
from django.urls import path, include
from django.contrib import admin

import apps.ApiConnectionStatus.views
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from apps.Job.views import JobViewSet
from django.conf import settings
from django.conf.urls.static import static

# Import the ViewSets from Vehicle and Driver apps
from apps.Vehicle.views import VehicleViewSet, VehicleDocumentViewSet
from apps.Driver.views import (
    DriverViewSet,
    DriverLocationViewSet,
    DriverAvailabilityViewSet,
    DriverDocumentViewSet,
    DriverInfringementViewSet,
)

# Import Location views for testing
from apps.Location.views import (
    google_address_autocomplete_simple,
    postcode_suggestions_simple,
    google_place_details,
    geocode_address,
    postcode_address_lookup_enhanced,
    postcode_address_lookup,
    simple_postcode_addresses,
)

router = routers.DefaultRouter(trailing_slash=True)

# Register Vehicle app ViewSets
router.register(r"vehicles", VehicleViewSet)
router.register(r"vehicle-documents", VehicleDocumentViewSet)


router.register(r"jobs", JobViewSet)

urlpatterns = [
    # Geocoding endpoints outside API path to bypass authentication issues
    # API routes with prefix
    path(
        "morevans/api/v1/",
        include(
            [
                path(
                    "geocoding/google-autocomplete/",
                    google_address_autocomplete_simple,
                    name="geocoding_google_autocomplete",
                ),
                path(
                    "geocoding/postcode-suggestions/",
                    postcode_suggestions_simple,
                    name="geocoding_postcode_suggestions",
                ),
                path(
                    "geocoding/google-place-details/",
                    google_place_details,
                    name="geocoding_google_place_details",
                ),
                path(
                    "geocoding/geocode-address/",
                    geocode_address,
                    name="geocoding_geocode_address",
                ),
                path(
                    "geocoding/postcode-addresses-simple/",
                    postcode_address_lookup,
                    name="geocoding_postcode_addresses_simple",
                ),
                path(
                    "geocoding/postcode-addresses/",
                    postcode_address_lookup_enhanced,
                    name="geocoding_postcode_addresses",
                ),
                path(
                    "geocoding/postcode-addresses-demo/",
                    simple_postcode_addresses,
                    name="geocoding_postcode_addresses_demo",
                ),
                # Test endpoint outside API path
                path(
                    "test/google-autocomplete/",
                    google_address_autocomplete_simple,
                    name="test_google_autocomplete",
                ),
                path("admin/", admin.site.urls),
                # Include router URLs
                path("", include(router.urls)),
                # Status endpoint
                path(
                    "status/",
                    apps.ApiConnectionStatus.views.ApiConnectionStatusView.as_view(),
                    name="status",
                ),
                # Authentication endpoints
                path("auth/", include("apps.Authentication.urls")),
                # Request app URLs
                path("", include("apps.Request.urls")),
                # User app URLs
                path("", include("apps.User.urls")),
                # pricing app URLs
                path("", include("apps.pricing.urls")),
                # location app URLs
                path("", include("apps.Location.urls")),
                # payment app URLs
                path("", include("apps.Payment.urls")),
                # provider app URLs
                path("", include("apps.Provider.urls")),
                path("", include("apps.Driver.urls")),
                path("", include("apps.Bidding.urls")),
                path("", include("apps.CommonItems.urls")),
                path("", include("apps.Message.urls")),
                path("chat/", include("apps.Chat.urls")),
                path("", include("apps.Services.urls")),
                path("", include("apps.Vehicle.urls")),
                path("", include("apps.Notification.urls")),
                # Media files under API prefix
                *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
            ]
        ),
    ),
    # Add non-API routes here if needed
]
