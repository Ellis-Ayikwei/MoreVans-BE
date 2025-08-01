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
    def generate_svg_logo(text="MV", color="#2E2787", size=80):
        """Generate a simple SVG logo for email templates"""
        svg = f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#4A3F9C;stop-opacity:1" />
                </linearGradient>
            </defs>
            <circle cx="{size//2}" cy="{size//2}" r="{size//2-2}" fill="url(#logoGradient)" stroke="{color}" stroke-width="2"/>
            <text x="{size//2}" y="{size//2+size//8}" font-family="Arial, sans-serif" font-size="{size//3}" font-weight="bold" text-anchor="middle" fill="white">{text}</text>
        </svg>"""
        return svg

    @staticmethod
    def get_logo_data_url(text="MV", color="#2E2787", size=80):
        """Get base64 encoded SVG logo for email embedding"""
        import base64

        svg = OTPEmailService.generate_svg_logo(text, color, size)
        encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{encoded}"

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
        logger.info(
            f"[EMAIL_DEBUG] Starting email send for user {user.id} ({user.email}), OTP ID: {otp.id}"
        )

        try:
            # Prepare context based on OTP type
            logger.info(
                f"[EMAIL_DEBUG] Preparing email context for OTP type: {otp_type}"
            )

            # Generate logo for email
            logo_data_url = OTPEmailService.get_logo_data_url("MV", "#2E2787", 80)

            context = {
                "user_name": user.first_name or user.email.split("@")[0],
                "otp_code": otp.otp_code,
                "validity_minutes": int(
                    (otp.expires_at - timezone.now()).total_seconds() / 60
                ),
                "app_name": kwargs.get("app_name", "MoreVans"),
                "current_year": datetime.now().year,
                "logo_svg_base64": logo_data_url.split(",")[
                    1
                ],  # Remove the data:image/svg+xml;base64, prefix
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

            logger.info(f"[EMAIL_DEBUG] Email subject: {context['subject']}")

            # Add any additional context passed in kwargs
            context.update(kwargs)

            # Render email templates
            logger.info(f"[EMAIL_DEBUG] Rendering email templates")
            try:
                html_content = render_to_string("emails/otp_verification.html", context)
                text_content = render_to_string("emails/otp_verification.txt", context)
                logger.info(
                    f"[EMAIL_DEBUG] Templates rendered successfully - HTML length: {len(html_content)}, Text length: {len(text_content)}"
                )
            except Exception as template_error:
                logger.error(
                    f"[EMAIL_DEBUG] Template rendering failed: {str(template_error)}"
                )
                raise

            # Create email message
            logger.info(f"[EMAIL_DEBUG] Creating EmailMultiAlternatives object")
            logger.info(f"[EMAIL_DEBUG] From email: {settings.DEFAULT_FROM_EMAIL}")
            logger.info(f"[EMAIL_DEBUG] To email: {user.email}")

            email = EmailMultiAlternatives(
                subject=context["subject"],
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )

            # Attach HTML version
            logger.info(f"[EMAIL_DEBUG] Attaching HTML alternative")
            email.attach_alternative(html_content, "text/html")

            # Send email
            logger.info(f"[EMAIL_DEBUG] Attempting to send email via SMTP")
            email.send(fail_silently=False)
            logger.info(f"[EMAIL_DEBUG] Email sent successfully via SMTP")

            logger.info(f"OTP email sent successfully to {user.email} for {otp_type}")
            return True

        except Exception as e:
            logger.exception(
                f"[EMAIL_DEBUG] Failed to send OTP email to {user.email}: {str(e)}"
            )
            logger.error(
                f"[EMAIL_DEBUG] Email settings - DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
            )
            logger.error(
                f"[EMAIL_DEBUG] Email settings - EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}"
            )
            logger.error(
                f"[EMAIL_DEBUG] Email settings - EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}"
            )
            logger.error(
                f"[EMAIL_DEBUG] Email settings - EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}"
            )
            logger.error(
                f"[EMAIL_DEBUG] Email settings - EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}"
            )
            logger.error(
                f"[EMAIL_DEBUG] Email settings - EMAIL_HOST_PASSWORD: {'Set' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'Not set'}"
            )
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

    @staticmethod
    def get_hourly_verification_key(user, otp_type):
        """Generate cache key for hourly verification attempts"""
        return f"otp_hourly_verification:{user.id}:{otp_type}"

    @staticmethod
    def get_otp_verification_key(user, otp_type, otp_id):
        """Generate cache key for specific OTP verification attempts"""
        return f"otp_verification_attempts:{user.id}:{otp_type}:{otp_id}"

    @staticmethod
    def get_global_email_limit_key():
        """Generate cache key for global email sending limit"""
        return "global_otp_emails_sent_hourly"

    @staticmethod
    def get_global_email_stats():
        """Get current global email sending statistics"""
        key = OTPValidator.get_global_email_limit_key()
        current_count = cache.get(key, 0)
        max_limit = 1000  # Should match the limit in send_otp_utility

        return {
            "current_count": current_count,
            "max_limit": max_limit,
            "remaining": max(0, max_limit - current_count),
            "percentage_used": (
                (current_count / max_limit) * 100 if max_limit > 0 else 0
            ),
        }

    @staticmethod
    def reset_global_email_limit():
        """Reset global email sending counter (admin function)"""
        key = OTPValidator.get_global_email_limit_key()
        cache.delete(key)
        return True


def send_otp_utility(
    user, otp_type, email=None, phone_number=None, admin_override=False, admin_user=None
):
    """
    Comprehensive utility function to send OTP with all necessary checks and validations.

    Args:
        user: User instance (required)
        otp_type: Type of OTP (signup, login, password_reset, etc.)
        email: Email address (optional, uses user.email if not provided)
        phone_number: Phone number (optional, uses user.phone_number if not provided)
        admin_override: Whether admin is bypassing rate limits (default: False)
        admin_user: Admin user performing the override (required if admin_override=True)

    Returns:
        dict: Response data with success status and appropriate messages
    """
    logger.info(
        f"[OTP_DEBUG] Starting OTP send process for user {user.id} ({user.email}), type: {otp_type}"
    )

    try:
        # Validate admin override
        if admin_override:
            logger.info(
                f"[OTP_DEBUG] Admin override requested by {admin_user.email if admin_user else 'Unknown'}"
            )
            if not admin_user:
                logger.error(
                    "[OTP_DEBUG] Admin override requested but no admin_user provided"
                )
                return {
                    "success": False,
                    "message": "Admin user must be specified for admin override.",
                    "error_code": "ADMIN_OVERRIDE_ERROR",
                }

            # Check if admin user has permission (you can customize this check)
            if not admin_user.is_staff:
                logger.error(
                    f"[OTP_DEBUG] Non-staff user {admin_user.email} attempted admin override"
                )
                return {
                    "success": False,
                    "message": "Only staff members can perform admin overrides.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                }
            logger.info(f"[OTP_DEBUG] Admin override validated for {admin_user.email}")

        # Determine recipient
        recipient_email = email or user.email
        recipient_phone = phone_number or getattr(user, "phone_number", None)

        logger.info(
            f"[OTP_DEBUG] Recipient determined - Email: {recipient_email}, Phone: {recipient_phone}"
        )

        if not recipient_email and not recipient_phone:
            logger.error(f"[OTP_DEBUG] No recipient found for user {user.id}")
            return {
                "success": False,
                "message": "No email or phone number available for OTP delivery",
                "error_code": "NO_RECIPIENT",
            }

        # GLOBAL EMAIL ABUSE PROTECTION - Check total emails sent per hour
        if recipient_email and not admin_override:
            logger.info(
                f"[OTP_DEBUG] Checking global email limit for {recipient_email}"
            )
            global_email_key = "global_otp_emails_sent_hourly"
            global_email_count = cache.get(global_email_key, 0)
            max_global_emails_per_hour = (
                1000  # Adjust based on your email service limits
            )

            logger.info(
                f"[OTP_DEBUG] Global email count: {global_email_count}/{max_global_emails_per_hour}"
            )

            if global_email_count >= max_global_emails_per_hour:
                logger.warning(
                    f"[OTP_DEBUG] Global email limit reached: {global_email_count} emails sent in the last hour"
                )
                return {
                    "success": False,
                    "message": "Email service temporarily unavailable. Please try again later.",
                    "error_code": "EMAIL_SERVICE_LIMIT",
                    "status_code": 503,
                }
            logger.info(f"[OTP_DEBUG] Global email limit check passed")

        # Skip rate limiting checks if admin override is enabled
        if not admin_override:
            logger.info(f"[OTP_DEBUG] Checking user rate limits for {user.id}")
            # Check rate limiting using cache
            rate_limit_key = OTPValidator.get_rate_limit_key(user, otp_type)
            attempts = cache.get(rate_limit_key, 0)
            logger.info(f"[OTP_DEBUG] User rate limit attempts: {attempts}/5")

            if attempts >= 5:  # Max 5 OTP requests per hour
                logger.warning(
                    f"[OTP_DEBUG] User rate limit exceeded for {user.id}: {attempts} attempts"
                )
                return {
                    "success": False,
                    "message": "Too many OTP requests. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "status_code": 429,
                }

            # Check resend cooldown
            cooldown_key = OTPValidator.get_resend_cooldown_key(user, otp_type)
            cooldown_active = cache.get(cooldown_key)
            logger.info(f"[OTP_DEBUG] Cooldown check: {cooldown_active}")

            if cooldown_active:
                logger.warning(f"[OTP_DEBUG] Cooldown active for user {user.id}")
                return {
                    "success": False,
                    "message": "Please wait before requesting another OTP.",
                    "error_code": "COOLDOWN_ACTIVE",
                    "status_code": 429,
                }
            logger.info(f"[OTP_DEBUG] All rate limit checks passed")
        else:
            logger.info(f"[OTP_DEBUG] Skipping rate limit checks due to admin override")

        # Import OTP model here to avoid circular imports
        logger.info(f"[OTP_DEBUG] Importing OTP model")
        from .models import OTP

        # Generate OTP
        logger.info(f"[OTP_DEBUG] Generating OTP for user {user.id}, type {otp_type}")
        otp = OTP.generate_otp(user, otp_type)
        logger.info(
            f"[OTP_DEBUG] OTP generated successfully - ID: {otp.id}, Code: {otp.otp_code[:2]}**, Expires: {otp.expires_at}"
        )

        # Send OTP based on recipient type
        if recipient_email:
            logger.info(
                f"[OTP_DEBUG] Attempting to send email OTP to {recipient_email}"
            )

            # Send OTP email
            logger.info(f"[OTP_DEBUG] Calling OTPEmailService.send_otp_email")
            email_sent = OTPEmailService.send_otp_email(user, otp, otp_type)
            logger.info(
                f"[OTP_DEBUG] OTPEmailService.send_otp_email returned: {email_sent}"
            )

            if not email_sent:
                logger.error(
                    f"[OTP_DEBUG] Email sending failed for user {user.id} to {recipient_email}"
                )
                return {
                    "success": False,
                    "message": "Failed to send OTP email. Please try again later.",
                    "error_code": "EMAIL_SEND_FAILED",
                }

            logger.info(f"[OTP_DEBUG] Email sent successfully, updating counters")

            # Update global email counter (only if not admin override)
            if not admin_override:
                global_email_key = "global_otp_emails_sent_hourly"
                global_email_count = cache.get(global_email_key, 0)
                new_global_count = global_email_count + 1
                cache.set(global_email_key, new_global_count, 3600)  # 1 hour expiry
                logger.info(
                    f"[OTP_DEBUG] Updated global email counter: {global_email_count} -> {new_global_count}"
                )

            # Update rate limiting (only if not admin override)
            if not admin_override:
                rate_limit_key = OTPValidator.get_rate_limit_key(user, otp_type)
                attempts = cache.get(rate_limit_key, 0)
                new_attempts = attempts + 1
                cache.set(rate_limit_key, new_attempts, 3600)  # 1 hour expiry
                logger.info(
                    f"[OTP_DEBUG] Updated user rate limit: {attempts} -> {new_attempts}"
                )

                cooldown_key = OTPValidator.get_resend_cooldown_key(user, otp_type)
                cache.set(cooldown_key, True, 60)  # 1 minute cooldown
                logger.info(f"[OTP_DEBUG] Set cooldown for user {user.id}")

            # Log admin override if applicable
            if admin_override:
                logger.info(
                    f"[OTP_DEBUG] Admin override: {admin_user.email} sent OTP to {user.email} for {otp_type}"
                )

            logger.info(
                f"[OTP_DEBUG] OTP send process completed successfully for user {user.id}"
            )
            return {
                "success": True,
                "message": f"OTP sent successfully to {mask_email(recipient_email)}"
                + (" (Admin Override)" if admin_override else ""),
                "masked_email": mask_email(recipient_email),
                "validity_minutes": 10,
                "otp_type": otp_type,
                "user_id": str(user.id),
                "admin_override": admin_override,
                "admin_user_id": str(admin_user.id) if admin_override else None,
            }

        elif recipient_phone:
            logger.info(
                f"[OTP_DEBUG] SMS OTP requested for {recipient_phone} (not implemented)"
            )
            # TODO: Implement SMS sending logic here
            # For now, return error indicating SMS not implemented
            return {
                "success": False,
                "message": "SMS OTP delivery not implemented yet.",
                "error_code": "SMS_NOT_IMPLEMENTED",
            }

        else:
            logger.error(
                f"[OTP_DEBUG] No valid delivery method found for user {user.id}"
            )
            return {
                "success": False,
                "message": "No valid delivery method available.",
                "error_code": "NO_DELIVERY_METHOD",
            }

    except Exception as e:
        logger.exception(
            f"[OTP_DEBUG] Exception in send_otp_utility for user {user.id}: {str(e)}"
        )
        return {
            "success": False,
            "message": "Failed to send OTP. Please try again later.",
            "error_code": "INTERNAL_ERROR",
        }


def verify_otp_utility(user, otp_code, otp_type, admin_override=False, admin_user=None):
    """
    Comprehensive utility function to verify OTP with all necessary checks.

    Args:
        user: User instance
        otp_code: OTP code to verify
        otp_type: Type of OTP (signup, login, password_reset, etc.)
        admin_override: Whether admin is bypassing verification limits (default: False)
        admin_user: Admin user performing the override (required if admin_override=True)

    Returns:
        dict: Response data with verification status and appropriate messages
    """
    logger.info(
        f"[VERIFY_DEBUG] Starting OTP verification for user {user.id} ({user.email}), type: {otp_type}, code: {otp_code[:2]}**"
    )

    try:
        # Validate admin override
        if admin_override:
            logger.info(
                f"[VERIFY_DEBUG] Admin override requested by {admin_user.email if admin_user else 'Unknown'}"
            )
            if not admin_user:
                logger.error(
                    "[VERIFY_DEBUG] Admin override requested but no admin_user provided"
                )
                return {
                    "success": False,
                    "message": "Admin user must be specified for admin override.",
                    "error_code": "ADMIN_OVERRIDE_ERROR",
                }

            # Check if admin user has permission
            if not admin_user.is_staff:
                logger.error(
                    f"[VERIFY_DEBUG] Non-staff user {admin_user.email} attempted admin override"
                )
                return {
                    "success": False,
                    "message": "Only staff members can perform admin overrides.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                }
            logger.info(
                f"[VERIFY_DEBUG] Admin override validated for {admin_user.email}"
            )

        # Import models here to avoid circular imports
        from .models import OTP, UserVerification

        # Validate OTP format
        logger.info(f"[VERIFY_DEBUG] Validating OTP format")
        is_valid_format, format_error = OTPValidator.validate_otp_format(otp_code)
        if not is_valid_format:
            logger.error(f"[VERIFY_DEBUG] OTP format validation failed: {format_error}")
            return {
                "success": False,
                "message": format_error,
                "error_code": "INVALID_FORMAT",
            }
        logger.info(f"[VERIFY_DEBUG] OTP format validation passed")

        # Find valid OTP
        logger.info(
            f"[VERIFY_DEBUG] Searching for valid OTP for user {user.id}, type: {otp_type}"
        )
        otp = (
            OTP.objects.filter(user=user, otp_type=otp_type, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp:
            logger.error(
                f"[VERIFY_DEBUG] No valid OTP found for user {user.id}, type: {otp_type}"
            )
            return {
                "success": False,
                "message": "No OTP found for this user and type.",
                "error_code": "OTP_NOT_FOUND",
            }

        logger.info(
            f"[VERIFY_DEBUG] Found OTP - ID: {otp.id}, Code: {otp.otp_code[:2]}**, Expires: {otp.expires_at}, Used: {otp.is_used}"
        )

        # Check if OTP is still valid (not expired)
        logger.info(f"[VERIFY_DEBUG] Checking OTP validity")
        if otp.is_used:
            logger.error(f"[VERIFY_DEBUG] OTP {otp.id} is already used")
            return {
                "success": False,
                "message": "OTP has already been used.",
                "error_code": "OTP_ALREADY_USED",
            }

        if otp.expires_at <= timezone.now():
            logger.error(f"[VERIFY_DEBUG] OTP {otp.id} has expired at {otp.expires_at}")
            return {
                "success": False,
                "message": "OTP has expired.",
                "error_code": "OTP_EXPIRED",
            }

        logger.info(f"[VERIFY_DEBUG] OTP validity check passed")

        # Skip rate limiting checks if admin override is enabled
        if not admin_override:
            logger.info(f"[VERIFY_DEBUG] Checking verification rate limits")
            # TIER 1: Check hourly verification attempts per user per OTP type
            hourly_verification_key = OTPValidator.get_hourly_verification_key(
                user, otp_type
            )
            hourly_attempts = cache.get(hourly_verification_key, 0)
            max_hourly_attempts = 5
            logger.info(
                f"[VERIFY_DEBUG] Hourly verification attempts: {hourly_attempts}/{max_hourly_attempts}"
            )

            if hourly_attempts >= max_hourly_attempts:
                logger.warning(
                    f"[VERIFY_DEBUG] Hourly verification limit exceeded for user {user.id}"
                )
                return {
                    "success": False,
                    "message": "Too many verification attempts in the last hour. Please try again later.",
                    "error_code": "HOURLY_LIMIT_EXCEEDED",
                }

            # TIER 2: Check attempts per specific OTP instance
            otp_verification_key = OTPValidator.get_otp_verification_key(
                user, otp_type, otp.id
            )
            otp_attempts = cache.get(otp_verification_key, 0)
            max_otp_attempts = 3
            logger.info(
                f"[VERIFY_DEBUG] OTP-specific attempts: {otp_attempts}/{max_otp_attempts}"
            )

            if otp_attempts >= max_otp_attempts:
                logger.warning(
                    f"[VERIFY_DEBUG] OTP-specific limit exceeded for OTP {otp.id}"
                )
                return {
                    "success": False,
                    "message": "Maximum attempts reached for this OTP. Please request a new OTP.",
                    "error_code": "OTP_MAX_ATTEMPTS_REACHED",
                }

            # Increment both counters
            hourly_attempts += 1
            otp_attempts += 1
            logger.info(
                f"[VERIFY_DEBUG] Incremented counters - Hourly: {hourly_attempts}, OTP: {otp_attempts}"
            )

            # Store with appropriate expiry times
            cache.set(hourly_verification_key, hourly_attempts, 3600)  # 1 hour expiry
            cache.set(otp_verification_key, otp_attempts, 3600)  # 1 hour expiry
            logger.info(f"[VERIFY_DEBUG] Rate limit counters updated in cache")
        else:
            logger.info(
                f"[VERIFY_DEBUG] Skipping rate limit checks due to admin override"
            )

        # Verify OTP code
        logger.info(
            f"[VERIFY_DEBUG] Comparing OTP codes - Provided: {otp_code}, Expected: {otp.otp_code}"
        )
        if otp.otp_code == otp_code:
            logger.info(f"[VERIFY_DEBUG] OTP code match successful")
            # Success - mark OTP as used
            otp.is_used = True
            otp.save()
            logger.info(f"[VERIFY_DEBUG] Marked OTP {otp.id} as used")

            # Clear verification attempts cache (only if not admin override)
            if not admin_override:
                cache.delete(otp_verification_key)
                logger.info(f"[VERIFY_DEBUG] Cleared OTP verification cache")

            # Log admin override if applicable
            if admin_override:
                logger.info(
                    f"[VERIFY_DEBUG] Admin override: {admin_user.email} verified OTP for {user.email} ({otp_type})"
                )

            # Perform action based on type
            logger.info(f"[VERIFY_DEBUG] Performing action for OTP type: {otp_type}")
            if otp_type == "signup":
                # Activate user account
                logger.info(f"[VERIFY_DEBUG] Activating user account for {user.id}")
                user.is_active = True
                user.save()

                # Mark email as verified
                logger.info(f"[VERIFY_DEBUG] Marking email as verified for {user.id}")
                verification, _ = UserVerification.objects.get_or_create(user=user)
                verification.email_verified = True
                verification.email_verified_at = timezone.now()
                verification.save()

                logger.info(
                    f"[VERIFY_DEBUG] User account activated and email verified successfully"
                )
                return {
                    "success": True,
                    "message": "Email verified successfully. Your account is now active."
                    + (" (Admin Override)" if admin_override else ""),
                    "action": "account_activated",
                    "user_id": str(user.id),
                    "admin_override": admin_override,
                    "admin_user_id": str(admin_user.id) if admin_override else None,
                }

            elif otp_type == "login":
                logger.info(f"[VERIFY_DEBUG] Login OTP verified successfully")
                return {
                    "success": True,
                    "message": "OTP verified successfully for login."
                    + (" (Admin Override)" if admin_override else ""),
                    "action": "login_verified",
                    "user_id": str(user.id),
                    "admin_override": admin_override,
                    "admin_user_id": str(admin_user.id) if admin_override else None,
                }

            elif otp_type == "password_reset":
                logger.info(f"[VERIFY_DEBUG] Password reset OTP verified successfully")
                return {
                    "success": True,
                    "message": "OTP verified successfully for password reset."
                    + (" (Admin Override)" if admin_override else ""),
                    "action": "password_reset_verified",
                    "user_id": str(user.id),
                    "admin_override": admin_override,
                    "admin_user_id": str(admin_user.id) if admin_override else None,
                }

            else:
                logger.info(f"[VERIFY_DEBUG] Generic OTP verified successfully")
                return {
                    "success": True,
                    "message": f"OTP verified successfully for {otp_type}."
                    + (" (Admin Override)" if admin_override else ""),
                    "action": f"{otp_type}_verified",
                    "user_id": str(user.id),
                    "admin_override": admin_override,
                    "admin_user_id": str(admin_user.id) if admin_override else None,
                }
        else:
            # Wrong OTP code
            logger.warning(
                f"[VERIFY_DEBUG] OTP code mismatch - Provided: {otp_code}, Expected: {otp.otp_code}"
            )
            if admin_override:
                logger.info(
                    f"[VERIFY_DEBUG] Admin override - returning error without rate limiting"
                )
                return {
                    "success": False,
                    "message": "Invalid OTP code. (Admin Override - No rate limiting applied)",
                    "error_code": "INVALID_OTP",
                    "admin_override": True,
                    "admin_user_id": str(admin_user.id),
                }
            else:
                # Calculate remaining attempts for both tiers
                remaining_otp_attempts = max_otp_attempts - otp_attempts
                remaining_hourly_attempts = max_hourly_attempts - hourly_attempts
                logger.info(
                    f"[VERIFY_DEBUG] Remaining attempts - OTP: {remaining_otp_attempts}, Hourly: {remaining_hourly_attempts}"
                )

                # Use the more restrictive limit for the message
                if remaining_otp_attempts <= remaining_hourly_attempts:
                    message = f"Invalid OTP. {remaining_otp_attempts} attempts remaining for this OTP."
                else:
                    message = f"Invalid OTP. {remaining_hourly_attempts} verification attempts remaining this hour."

                return {
                    "success": False,
                    "message": message,
                    "error_code": "INVALID_OTP",
                    "remaining_otp_attempts": remaining_otp_attempts,
                    "remaining_hourly_attempts": remaining_hourly_attempts,
                }

    except Exception as e:
        logger.exception(
            f"[VERIFY_DEBUG] Exception in verify_otp_utility for user {user.id}: {str(e)}"
        )
        return {
            "success": False,
            "message": "Failed to verify OTP. Please try again.",
            "error_code": "INTERNAL_ERROR",
        }
