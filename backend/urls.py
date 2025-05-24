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
from apps.Job.views import JobViewSet, JobBidViewSet

# Import the ViewSets from Vehicle and Driver apps
from apps.Vehicle.views import (
    VehicleViewSet,
    VehicleDocumentViewSet,
    VehicleInspectionViewSet,
    MaintenanceRecordViewSet,
)
from apps.Driver.views import (
    DriverViewSet,
    DriverLocationViewSet,
    DriverAvailabilityViewSet,
    DriverDocumentViewSet,
    DriverInfringementViewSet,
)

router = routers.DefaultRouter(trailing_slash=True)

# Register Vehicle app ViewSets
router.register(r"vehicles", VehicleViewSet)
router.register(r"vehicle-documents", VehicleDocumentViewSet)
router.register(r"vehicle-inspections", VehicleInspectionViewSet)
router.register(r"maintenance-records", MaintenanceRecordViewSet)

# Register Driver app ViewSets
router.register(r"drivers", DriverViewSet)
router.register(r"driver-locations", DriverLocationViewSet)
router.register(r"driver-availability", DriverAvailabilityViewSet)
router.register(r"driver-documents", DriverDocumentViewSet)
router.register(r"driver-infringements", DriverInfringementViewSet)

router.register(r"jobs", JobViewSet)
router.register(r"bids", JobBidViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    # API routes with prefix
    path(
        "morevans/api/v1/",
        include(
            [
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
                path("user/", include("apps.User.urls")),
                # pricing app URLs
                path("", include("apps.pricing.urls")),
            ]
        ),
    ),
    # Add non-API routes here if needed
]
