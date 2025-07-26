from django.contrib import admin
from .models import OTP, LoginAttempt


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'email', 'otp_type', 'is_used', 'is_verified', 'created_at', 'expires_at')
    list_filter = ('otp_type', 'is_used', 'is_verified', 'created_at')
    search_fields = ('code', 'user__email', 'email')
    readonly_fields = ('code', 'created_at', 'verified_at')
    ordering = ('-created_at',)
    
    def has_change_permission(self, request, obj=None):
        # Allow admin to view but restrict modification
        return True
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of expired OTPs
        if obj and obj.is_expired():
            return True
        return request.user.is_superuser


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'attempt_time', 'is_successful')
    list_filter = ('is_successful', 'attempt_time')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('email', 'ip_address', 'attempt_time', 'is_successful')
    ordering = ('-attempt_time',)
    
    def has_add_permission(self, request):
        # Prevent manual addition
        return False
    
    def has_change_permission(self, request, obj=None):
        # Read-only
        return False
