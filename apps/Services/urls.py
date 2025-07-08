from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServicesViewSet

router = DefaultRouter()
router.register(
    r"service-categories", ServiceCategoryViewSet, basename="servicecategory"
)
router.register(r"services", ServicesViewSet, basename="services")

urlpatterns = [
    path("", include(router.urls)),
]
