from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VehicleViewSet, VehicleImageViewSet, VehicleDocumentViewSet

router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet)
router.register(r"vehicle-photos", VehicleImageViewSet)
router.register(r"vehicle-documents", VehicleDocumentViewSet)

urlpatterns = [path("", include(router.urls))]
