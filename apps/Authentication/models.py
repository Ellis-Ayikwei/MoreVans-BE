from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
import string

from apps.Basemodel.models import Basemodel

User = get_user_model()


class OTP(Basemodel):
    """Model to store OTP for user verification"""

    OTP_TYPES = (
        ("signup", "Sign Up Verification"),
        ("login", "Login Authentication"),
        ("password_reset", "Password Reset"),
        ("email_change", "Email Change"),
        ("phone_change", "Phone Change"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)

    class Meta:
        db_table = "otps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "otp_type", "is_used"]),
            models.Index(fields=["otp_code", "expires_at"]),
        ]

    def __str__(self):
        return f"{getattr(self.user, 'email', 'Unknown')} - {self.otp_type} - {self.otp_code}"

    @classmethod
    def generate_otp(cls, user, otp_type, validity_minutes=10):
        """Generate a new OTP for the user"""
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            f"[OTP_GEN_DEBUG] Starting OTP generation for user {user.id}, type: {otp_type}"
        )

        # Invalidate any existing unused OTPs of the same type
        logger.info(
            f"[OTP_GEN_DEBUG] Invalidating existing unused OTPs for user {user.id}, type: {otp_type}"
        )
        existing_otps = cls.objects.filter(user=user, otp_type=otp_type, is_used=False)
        existing_count = existing_otps.count()
        logger.info(f"[OTP_GEN_DEBUG] Found {existing_count} existing unused OTPs")

        existing_otps.update(is_used=True)
        logger.info(f"[OTP_GEN_DEBUG] Marked {existing_count} existing OTPs as used")

        # Generate 6-digit OTP
        logger.info(f"[OTP_GEN_DEBUG] Generating 6-digit OTP code")
        otp_code = "".join(random.choices(string.digits, k=6))
        logger.info(f"[OTP_GEN_DEBUG] Generated OTP code: {otp_code[:2]}**")

        # Create new OTP
        logger.info(f"[OTP_GEN_DEBUG] Creating new OTP record in database")
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)
        logger.info(f"[OTP_GEN_DEBUG] OTP will expire at: {expires_at}")

        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at,
        )

        logger.info(
            f"[OTP_GEN_DEBUG] OTP created successfully - ID: {otp.id}, Code: {otp_code[:2]}**, Expires: {otp.expires_at}"
        )

        return otp

    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and self.expires_at > timezone.now()

    def verify(self, otp_code):
        """Verify the OTP code (legacy method - now handled in utility)"""
        if not self.is_valid():
            return False

        if self.otp_code == otp_code:
            self.is_used = True
            self.save()
            return True

        return False


class UserVerification(Basemodel):
    """Track user verification status"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="verification"
    )
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_verifications"

    def __str__(self):
        return f"{getattr(self.user, 'email', 'Unknown')} - Email: {self.email_verified}, Phone: {self.phone_verified}"


class TrustedDevice(Basemodel):
    """Trusted device record to allow OTP bypass and bind refresh token to device."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="trusted_devices"
    )
    device_id = models.CharField(max_length=128)
    device_fingerprint_hash = models.CharField(max_length=256)
    device_name = models.CharField(max_length=200, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    refresh_token_hash = models.CharField(max_length=256, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "trusted_devices"
        indexes = [
            models.Index(fields=["user", "device_id"]),
            models.Index(fields=["user", "device_fingerprint_hash"]),
            models.Index(fields=["refresh_token_hash"]),
            models.Index(fields=["expires_at"]),
        ]
        unique_together = ("user", "device_id")

    def __str__(self):
        return f"TrustedDevice({self.user_id}, {self.device_name or self.device_id})"


class LoginSession(Basemodel):
    """Short-lived login session for OTP verification during device trust onboarding."""

    id = models.UUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="login_sessions"
    )
    device_fingerprint_hash = models.CharField(max_length=256)
    otp_code = models.CharField(max_length=6)
    otp_expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "login_sessions"
        indexes = [
            models.Index(fields=["user", "otp_expires_at"]),
        ]

    def __str__(self):
        return f"LoginSession({self.user_id}, verified={self.is_verified})"
