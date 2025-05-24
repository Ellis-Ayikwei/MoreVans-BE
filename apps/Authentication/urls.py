from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LoginAPIView,
    LogoutAPIView,
    PasswordChangeAPIView,
    PasswordRecoveryAPIView,
    PasswordResetConfirmAPIView,
    RegisterAPIView,
    TokenRefreshView,
    TokenVerifyView,
    UserViewSet
)

# Create a router for the UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('recover_password/', PasswordRecoveryAPIView.as_view(), name='token_obtain_pair'),
    path('reset_password/<uidb64>/<token>/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('change_password/', PasswordChangeAPIView.as_view(), name='change_password'),
    path('refresh_token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify_token/', TokenVerifyView.as_view(), name='token_verify'),
]


