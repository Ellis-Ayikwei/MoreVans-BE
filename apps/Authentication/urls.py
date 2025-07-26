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
    UserViewSet,
    OTPRequestAPIView,
    OTPVerificationAPIView,
    EnhancedRegisterAPIView,
    EnhancedLoginAPIView,
)

# Create a router for the UserViewSet
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    
    # Traditional authentication endpoints
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    
    # Enhanced OTP-enabled authentication endpoints
    path("register-otp/", EnhancedRegisterAPIView.as_view(), name="register_otp"),
    path("login-otp/", EnhancedLoginAPIView.as_view(), name="login_otp"),
    
    # OTP management endpoints
    path("otp/request/", OTPRequestAPIView.as_view(), name="otp_request"),
    path("otp/verify/", OTPVerificationAPIView.as_view(), name="otp_verify"),
    
    # Password management
    path(
        "forget_password/", PasswordRecoveryAPIView.as_view(), name="password_recovery"
    ),
    path(
        "reset_password/<uidb64>/<token>/",
        PasswordResetConfirmAPIView.as_view(),
        name="password_reset_confirm",
    ),
    path("change_password/", PasswordChangeAPIView.as_view(), name="change_password"),
    
    # Token management
    path("refresh_token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify_token/", TokenVerifyView.as_view(), name="token_verify"),
]
