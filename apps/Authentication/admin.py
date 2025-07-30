from django.contrib import admin
from .models import OTP, UserVerification

# Register your models here.


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "otp_type",
        "otp_code",
        "is_used",
        "created_at",
        "expires_at",
        "attempts",
    ]
    list_filter = ["otp_type", "is_used", "created_at"]
    search_fields = ["user__email", "otp_code"]
    readonly_fields = ["created_at", "otp_code"]
    ordering = ["-created_at"]


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "email_verified",
        "phone_verified",
        "email_verified_at",
        "phone_verified_at",
    ]
    list_filter = ["email_verified", "phone_verified"]
    search_fields = ["user__email", "user__phone_number"]
    readonly_fields = ["email_verified_at", "phone_verified_at"]
