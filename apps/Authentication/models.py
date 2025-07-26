from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
import string

User = get_user_model()


class OTP(models.Model):
    """Model to store OTP for user verification"""
    OTP_TYPES = (
        ('signup', 'Sign Up Verification'),
        ('login', 'Login Authentication'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
        ('phone_change', 'Phone Change'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'otps'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp_type', 'is_used']),
            models.Index(fields=['otp_code', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.otp_type} - {self.otp_code}"
    
    @classmethod
    def generate_otp(cls, user, otp_type, validity_minutes=10):
        """Generate a new OTP for the user"""
        # Invalidate any existing unused OTPs of the same type
        cls.objects.filter(
            user=user, 
            otp_type=otp_type, 
            is_used=False
        ).update(is_used=True)
        
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Create new OTP
        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=timezone.now() + timedelta(minutes=validity_minutes)
        )
        
        return otp
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return (
            not self.is_used and 
            self.expires_at > timezone.now() and 
            self.attempts < self.max_attempts
        )
    
    def verify(self, otp_code):
        """Verify the OTP code"""
        self.attempts += 1
        self.save()
        
        if not self.is_valid():
            return False
        
        if self.otp_code == otp_code:
            self.is_used = True
            self.save()
            return True
        
        return False


class UserVerification(models.Model):
    """Track user verification status"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_verifications'
    
    def __str__(self):
        return f"{self.user.email} - Email: {self.email_verified}, Phone: {self.phone_verified}"
