from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LoginAPIView,
    LogoutAPIView,
    PasswordChangeAPIView,
    PasswordRecoveryAPIView,
    PasswordResetConfirmAPIView,
    RegisterAPIView,
    RegisterProviderAPIView,
    TokenRefreshView,
    TokenVerifyView,
    DebugTokenView,
    UserViewSet,
    SendOTPView,
    VerifyOTPView,
    ResendOTPView,
    LoginWithOTPView,
    MFALoginView,
    VerifyMFALoginView,
    AdminSendOTPView,
    AdminVerifyOTPView,
    AdminResetOTPLimitsView,
    AdminEmailStatsView,
    AdminResetGlobalEmailLimitView,
    AdminOTPDebugLogsView,
    ListTrustedDevicesView,
    RevokeTrustedDeviceView,
    RevokeAllTrustedDevicesView,
)


# Create a router for the UserViewSet
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    # Authentication endpoints
    path("register/", RegisterAPIView.as_view(), name="register"),
    path(
        "register/provider/",
        RegisterProviderAPIView.as_view(),
        name="register_provider",
    ),
    path("login/", LoginAPIView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("forget_password/", PasswordRecoveryAPIView.as_view(), name="forget_password"),
    path(
        "reset_password/<uidb64>/<token>/",
        PasswordResetConfirmAPIView.as_view(),
        name="password_reset_confirm",
    ),
    path("change_password/", PasswordChangeAPIView.as_view(), name="change_password"),
    path("refresh_token/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "device-trust/devices/<uuid:user_id>/",
        ListTrustedDevicesView.as_view(),
        name="list_trusted_devices",
    ),
    path(
        "device-trust/devices/revoke/<uuid:device_id>/",
        RevokeTrustedDeviceView.as_view(),
        name="revoke_trusted_device",
    ),
    path(
        "device-trust/devices/revoke-all/<uuid:user_id>/",
        RevokeAllTrustedDevicesView.as_view(),
        name="revoke_all_trusted_devices",
    ),
    path("verify_token/", TokenVerifyView.as_view(), name="token_verify"),
    path("debug_token/", DebugTokenView.as_view(), name="debug_token"),
    # OTP endpoints
    path("otp/send/", SendOTPView.as_view(), name="send_otp"),
    path("otp/verify/", VerifyOTPView.as_view(), name="verify_otp"),
    path("otp/resend/", ResendOTPView.as_view(), name="resend_otp"),
    path("login/otp/", LoginWithOTPView.as_view(), name="login_with_otp"),
    # MFA Login endpoints
    path("mfa/login/", MFALoginView.as_view(), name="mfa_login"),
    path("mfa/verify/", VerifyMFALoginView.as_view(), name="verify_mfa_login"),
    # Admin OTP endpoints
    path("admin/otp/send/", AdminSendOTPView.as_view(), name="admin_send_otp"),
    path("admin/otp/verify/", AdminVerifyOTPView.as_view(), name="admin_verify_otp"),
    path(
        "admin/otp/reset-limits/",
        AdminResetOTPLimitsView.as_view(),
        name="admin_reset_otp_limits",
    ),
    # Admin Email Management endpoints
    path("admin/email/stats/", AdminEmailStatsView.as_view(), name="admin_email_stats"),
    path(
        "admin/email/reset-limit/",
        AdminResetGlobalEmailLimitView.as_view(),
        name="admin_reset_email_limit",
    ),
    # Admin Debug endpoints
    path("admin/debug/logs/", AdminOTPDebugLogsView.as_view(), name="admin_debug_logs"),
]
