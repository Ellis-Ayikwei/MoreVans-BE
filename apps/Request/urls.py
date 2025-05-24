from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RequestViewSet,
)
from apps.RequestItems.views import RequestItemViewSet

from apps.CommonItems.views import ItemCategoryViewSet, CommonItemViewset

router = DefaultRouter(trailing_slash=True)
router.register(r"requests", RequestViewSet)
router.register(r"items", RequestItemViewSet)

router.register(r"item-categories", ItemCategoryViewSet)
router.register(r"common-items", CommonItemViewset)

urlpatterns = [
    path("", include(router.urls)),
]
