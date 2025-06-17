from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceProviderViewSet,
    ServiceAreaViewSet,
    InsurancePolicyViewSet,
    SavedJobViewSet,
    WatchedJobViewSet,
    ProviderDocumentViewSet,
)

router = DefaultRouter()
router.register(r"providers", ServiceProviderViewSet, basename="provider")
router.register(r"service-areas", ServiceAreaViewSet, basename="service-area")
router.register(
    r"insurance-policies", InsurancePolicyViewSet, basename="insurance-policy"
)
router.register(r"saved-jobs", SavedJobViewSet, basename="saved-job")
router.register(r"watched-jobs", WatchedJobViewSet, basename="watched-job")
router.register(
    r"provider-documents", ProviderDocumentViewSet, basename="provider-documents"
)

app_name = "provider"

urlpatterns = [
    path("", include(router.urls)),
]
