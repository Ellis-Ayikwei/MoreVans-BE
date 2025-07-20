from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemCategoryViewSet,
    ItemTypeViewSet,
    ItemBrandViewSet,
    ItemModelViewSet,
    CommonItemViewSet,
    VehicleTypeViewSet,
    VehicleCategoryViewSet,
    VehicleSizeViewSet,
)

router = DefaultRouter()
router.register(r"item-categories", ItemCategoryViewSet)
router.register(r"item-types", ItemTypeViewSet)
router.register(r"item-brands", ItemBrandViewSet)
router.register(r"item-models", ItemModelViewSet)
router.register(r"common-items", CommonItemViewSet)
router.register(r"vehicle-types", VehicleTypeViewSet)
router.register(r"vehicle-categories", VehicleCategoryViewSet)
router.register(r"vehicle-sizes", VehicleSizeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
