from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RequestViewSet,
)
from apps.RequestItems.views import RequestItemViewSet

router = DefaultRouter(trailing_slash=True)
router.register(r"requests", RequestViewSet)
router.register(r"items", RequestItemViewSet)


urlpatterns = [
    path("", include(router.urls)),
    # path('requests/<uuid:request_id>/update_details/', RequestViewSet.as_view({'post': 'update_details'}), name='request-update-details'),
    # path('requests/<uuid:request_id>/update_staff_count/', RequestViewSet.as_view({'post': 'update_staff_count'}), name='request-update-staff-count'),
]
