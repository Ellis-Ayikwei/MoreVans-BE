from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
import string

User = get_user_model()


class OTP(models.Model):
    """Model to store One-Time Passwords for user verification"""
    
    OTP_TYPES = (
        ('signup_verification', 'Signup Verification'),
        ('login_verification', 'Login Verification'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    email = models.EmailField()  # Store the email for which OTP was generated
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'otp_type']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_otp_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # 10 minutes expiry
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_otp_code():
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used and verified"""
        self.is_used = True
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"OTP {self.code} for {self.email} ({self.otp_type})"


class LoginAttempt(models.Model):
    """Model to track login attempts for rate limiting"""
    
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    attempt_time = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-attempt_time']
        indexes = [
            models.Index(fields=['email', 'attempt_time']),
            models.Index(fields=['ip_address', 'attempt_time']),
        ]
    
    def __str__(self):
        return f"Login attempt for {self.email} from {self.ip_address}"
