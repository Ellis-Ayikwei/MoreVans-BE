# Register Driver app ViewSets
from django.urls import path, include
from rest_framework import routers
from .views import (
    DriverViewSet,
    DriverLocationViewSet,
    DriverAvailabilityViewSet,
    DriverDocumentViewSet,
    DriverInfringementViewSet,
)

router = routers.DefaultRouter(trailing_slash=True)
router.register(r"drivers", DriverViewSet)
router.register(r"driver-locations", DriverLocationViewSet)
router.register(r"driver-availability", DriverAvailabilityViewSet)
router.register(r"driver-documents", DriverDocumentViewSet)
router.register(r"driver-infringements", DriverInfringementViewSet)


urlpatterns = [path("", include(router.urls))]
