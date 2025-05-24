from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserManagementViewSet, AddressViewSet, UserActivityViewSet

router = DefaultRouter()
router.register(r'users', UserManagementViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'activities', UserActivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]