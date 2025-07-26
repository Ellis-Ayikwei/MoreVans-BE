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
    SendOTPView,
    VerifyOTPView,
    ResendOTPView,
    LoginWithOTPView,
)

# Create a router for the UserViewSet
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path(
        "forget_password/", PasswordRecoveryAPIView.as_view(), name="token_obtain_pair"
    ),
    path(
        "reset_password/<uidb64>/<token>/",
        PasswordResetConfirmAPIView.as_view(),
        name="password_reset_confirm",
    ),
    path("change_password/", PasswordChangeAPIView.as_view(), name="change_password"),
    path("refresh_token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify_token/", TokenVerifyView.as_view(), name="token_verify"),
    
    # OTP endpoints
    path("otp/send/", SendOTPView.as_view(), name="send_otp"),
    path("otp/verify/", VerifyOTPView.as_view(), name="verify_otp"),
    path("otp/resend/", ResendOTPView.as_view(), name="resend_otp"),
    path("login/otp/", LoginWithOTPView.as_view(), name="login_with_otp"),
]
