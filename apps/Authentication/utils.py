from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def mask_email(email):
    """Mask email address for security (e.g., j***@example.com)"""
    if "@" not in email:
        return email

    local, domain = email.split("@")
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def mask_phone(phone):
    """Mask phone number for security (e.g., +1 ***-***-1234)"""
    if not phone or len(phone) < 4:
        return phone

    # Keep last 4 digits visible
    return "*" * (len(phone) - 4) + phone[-4:]


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def increment_failed_logins(email, ip):
    """Increment failed login attempts counter"""
    cache_key = f"login_attempts:{email}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=3600)  # 1 hour

    # Also track by IP to prevent attacks across multiple accounts
    ip_key = f"login_attempts_ip:{ip}"
    ip_attempts = cache.get(ip_key, 0) + 1
    cache.set(ip_key, ip_attempts, timeout=3600)


def is_account_locked(email):
    """Check if account is locked due to too many failed attempts"""
    cache_key = f"login_attempts:{email}"
    attempts = cache.get(cache_key, 0)
    return attempts >= 5  # Lock after 5 failed attempts


def reset_failed_logins(email):
    """Reset failed login attempts counter"""
    cache_key = f"login_attempts:{email}"
    cache.delete(cache_key)


def send_email_template(user, subject, template_name, context=None):
    """
    Send email using template

    Args:
        user: User instance
        subject: Email subject
        template_name: Template name (without .html/.txt extension)
        context: Additional context for template
    """
    try:
        if context is None:
            context = {}

        # Add default context
        context.update(
            {
                "user_name": user.first_name or user.email.split("@")[0],
                "app_name": "MoreVans",
                "current_year": datetime.now().year,
            }
        )

        # Render email templates
        html_content = render_to_string(f"emails/{template_name}.html", context)
        text_content = render_to_string(f"emails/{template_name}.txt", context)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        # Attach HTML version
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)

        logger.info(f"Email sent successfully to {user.email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return False


class OTPEmailService:
    """Service class for sending OTP emails using templates"""

    @staticmethod
    def send_otp_email(user, otp, otp_type, **kwargs):
        """
        Send OTP email to user

        Args:
            user: User instance
            otp: OTP instance
            otp_type: Type of OTP (signup, login, password_reset, etc.)
            **kwargs: Additional context for email template
        """
        try:
            # Prepare context based on OTP type
            context = {
                "user_name": user.first_name or user.email.split("@")[0],
                "otp_code": otp.otp_code,
                "validity_minutes": int(
                    (otp.expires_at - timezone.now()).total_seconds() / 60
                ),
                "app_name": kwargs.get("app_name", "MoreVans"),
                "current_year": datetime.now().year,
            }

            # Set specific messages and subjects based on OTP type
            if otp_type == "signup":
                context["subject"] = "Verify Your Email Address"
                context["message"] = (
                    "Thank you for signing up! Please use the code below to verify your email address and complete your registration."
                )
                context["action_text"] = "Complete Registration"
            elif otp_type == "login":
                context["subject"] = "Your Login Verification Code"
                context["message"] = (
                    "You requested a login verification code. Please use the code below to complete your login."
                )
                context["action_text"] = "Complete Login"
            elif otp_type == "password_reset":
                context["subject"] = "Reset Your Password"
                context["message"] = (
                    "You requested to reset your password. Please use the code below to verify your identity."
                )
                context["action_text"] = "Reset Password"
            elif otp_type == "email_change":
                context["subject"] = "Verify Your New Email Address"
                context["message"] = (
                    "You requested to change your email address. Please use the code below to verify your new email."
                )
                context["action_text"] = "Verify Email"
            else:
                context["subject"] = "Your Verification Code"
                context["message"] = (
                    "Please use the code below to complete your verification."
                )
                context["action_text"] = "Verify"

            # Add any additional context passed in kwargs
            context.update(kwargs)

            # Render email templates
            html_content = render_to_string("emails/otp_verification.html", context)
            text_content = render_to_string("emails/otp_verification.txt", context)

            # Create email message
            email = EmailMultiAlternatives(
                subject=context["subject"],
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )

            # Attach HTML version
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send(fail_silently=False)

            logger.info(f"OTP email sent successfully to {user.email} for {otp_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
            return False


class OTPValidator:
    """Utility class for OTP validation logic"""

    @staticmethod
    def validate_otp_format(otp_code):
        """Validate OTP format (6 digits)"""
        if not otp_code:
            return False, "OTP code is required"

        if not otp_code.isdigit():
            return False, "OTP must contain only digits"

        if len(otp_code) != 6:
            return False, "OTP must be 6 digits long"

        return True, None

    @staticmethod
    def get_rate_limit_key(user, otp_type):
        """Generate cache key for rate limiting"""
        return f"otp_rate_limit:{user.id}:{otp_type}"

    @staticmethod
    def get_resend_cooldown_key(user, otp_type):
        """Generate cache key for resend cooldown"""
        return f"otp_resend_cooldown:{user.id}:{otp_type}"


def send_otp_utility(user, otp_type, email=None, phone_number=None):
    """
    Comprehensive utility function to send OTP with all necessary checks and validations.

    Args:
        user: User instance (required)
        otp_type: Type of OTP (signup, login, password_reset, etc.)
        email: Email address (optional, uses user.email if not provided)
        phone_number: Phone number (optional, uses user.phone_number if not provided)

    Returns:
        dict: Response data with success status and appropriate messages
    """
    try:
        # Determine recipient
        recipient_email = email or user.email
        recipient_phone = phone_number or getattr(user, "phone_number", None)

        if not recipient_email and not recipient_phone:
            return {
                "success": False,
                "message": "No email or phone number available for OTP delivery",
                "error_code": "NO_RECIPIENT",
            }

        # Check rate limiting using cache
        rate_limit_key = OTPValidator.get_rate_limit_key(user, otp_type)
        attempts = cache.get(rate_limit_key, 0)

        if attempts >= 5:  # Max 5 OTP requests per hour
            return {
                "success": False,
                "message": "Too many OTP requests. Please try again later.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "status_code": 429,
            }

        # Check resend cooldown
        cooldown_key = OTPValidator.get_resend_cooldown_key(user, otp_type)
        if cache.get(cooldown_key):
            return {
                "success": False,
                "message": "Please wait before requesting another OTP.",
                "error_code": "COOLDOWN_ACTIVE",
                "status_code": 429,
            }

        # Import OTP model here to avoid circular imports
        from .models import OTP

        # Generate OTP
        otp = OTP.generate_otp(user, otp_type)

        # Send OTP based on recipient type
        if recipient_email:
            # Send OTP email
            email_sent = OTPEmailService.send_otp_email(user, otp, otp_type)
            if not email_sent:
                return {
                    "success": False,
                    "message": "Failed to send OTP email. Please try again later.",
                    "error_code": "EMAIL_SEND_FAILED",
                }

            # Update rate limiting
            cache.set(rate_limit_key, attempts + 1, 3600)  # 1 hour expiry
            cache.set(cooldown_key, True, 60)  # 1 minute cooldown

            return {
                "success": True,
                "message": f"OTP sent successfully to {mask_email(recipient_email)}",
                "masked_recipient": mask_email(recipient_email),
                "validity_minutes": 10,
                "otp_type": otp_type,
                "user_id": str(user.id),
            }

        elif recipient_phone:
            # TODO: Implement SMS sending logic here
            # For now, return error indicating SMS not implemented
            return {
                "success": False,
                "message": "SMS OTP delivery not implemented yet.",
                "error_code": "SMS_NOT_IMPLEMENTED",
            }

        else:
            return {
                "success": False,
                "message": "No valid delivery method available.",
                "error_code": "NO_DELIVERY_METHOD",
            }

    except Exception as e:
        logger.exception(f"Error in send_otp_utility: {str(e)}")
        return {
            "success": False,
            "message": "Failed to send OTP. Please try again later.",
            "error_code": "INTERNAL_ERROR",
        }


def verify_otp_utility(user, otp_code, otp_type):
    """
    Comprehensive utility function to verify OTP with all necessary checks.

    Args:
        user: User instance
        otp_code: OTP code to verify
        otp_type: Type of OTP (signup, login, password_reset, etc.)

    Returns:
        dict: Response data with verification status and appropriate messages
    """
    try:
        # Import models here to avoid circular imports
        from .models import OTP, UserVerification

        # Validate OTP format
        is_valid_format, format_error = OTPValidator.validate_otp_format(otp_code)
        if not is_valid_format:
            return {
                "success": False,
                "message": format_error,
                "error_code": "INVALID_FORMAT",
            }

        # Find valid OTP
        otp = (
            OTP.objects.filter(user=user, otp_type=otp_type, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            return {
                "success": False,
                "message": "No OTP found for this user and type.",
                "error_code": "OTP_NOT_FOUND",
            }

        if not otp.is_valid():
            return {
                "success": False,
                "message": "OTP has expired.",
                "error_code": "OTP_EXPIRED",
            }

        # Verify OTP
        if not otp.verify(otp_code):
            remaining_attempts = otp.max_attempts - otp.attempts
            return {
                "success": False,
                "message": f"Invalid OTP. {remaining_attempts} attempts remaining.",
                "error_code": "INVALID_OTP",
                "remaining_attempts": remaining_attempts,
            }

        # OTP is valid - perform action based on type
        if otp_type == "signup":
            # Activate user account
            user.is_active = True
            user.save()

            # Mark email as verified
            verification, _ = UserVerification.objects.get_or_create(user=user)
            verification.email_verified = True
            verification.email_verified_at = timezone.now()
            verification.save()

            return {
                "success": True,
                "message": "Email verified successfully. Your account is now active.",
                "action": "account_activated",
                "user_id": str(user.id),
            }

        elif otp_type == "login":
            return {
                "success": True,
                "message": "OTP verified successfully for login.",
                "action": "login_verified",
                "user_id": str(user.id),
            }

        elif otp_type == "password_reset":
            return {
                "success": True,
                "message": "OTP verified successfully for password reset.",
                "action": "password_reset_verified",
                "user_id": str(user.id),
            }

        else:
            return {
                "success": True,
                "message": f"OTP verified successfully for {otp_type}.",
                "action": f"{otp_type}_verified",
                "user_id": str(user.id),
            }

    except Exception as e:
        logger.exception(f"Error in verify_otp_utility: {str(e)}")
        return {
            "success": False,
            "message": "Failed to verify OTP. Please try again.",
            "error_code": "INTERNAL_ERROR",
        }
