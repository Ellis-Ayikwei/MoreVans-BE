import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import OTP, LoginAttempt
from django.core.cache import cache

User = get_user_model()
logger = logging.getLogger(__name__)


class OTPService:
    """Service class to handle OTP operations"""

    @staticmethod
    def generate_otp(user, otp_type, email=None):
        """
        Generate and save OTP for a user
        
        Args:
            user: User instance
            otp_type: Type of OTP (signup_verification, login_verification, etc.)
            email: Email address (defaults to user.email)
        
        Returns:
            OTP instance
        """
        if email is None:
            email = user.email

        # Invalidate any existing unused OTPs for this user and type
        OTP.objects.filter(
            user=user,
            otp_type=otp_type,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(is_used=True)

        # Create new OTP
        otp = OTP.objects.create(
            user=user,
            otp_type=otp_type,
            email=email
        )

        logger.info(f"Generated OTP {otp.code} for user {user.email} (type: {otp_type})")
        return otp

    @staticmethod
    def verify_otp(code, otp_type, email, user=None):
        """
        Verify OTP code
        
        Args:
            code: OTP code to verify
            otp_type: Type of OTP
            email: Email address
            user: User instance (optional, for additional validation)
        
        Returns:
            dict: Verification result with success status and message
        """
        try:
            # Find valid OTP
            otp_query = OTP.objects.filter(
                code=code,
                otp_type=otp_type,
                email=email,
                is_used=False,
                expires_at__gt=timezone.now()
            )

            if user:
                otp_query = otp_query.filter(user=user)

            otp = otp_query.first()

            if not otp:
                logger.warning(f"Invalid OTP verification attempt: {code} for {email}")
                return {
                    'success': False,
                    'message': 'Invalid or expired verification code'
                }

            if otp.is_expired():
                logger.warning(f"Expired OTP verification attempt: {code} for {email}")
                return {
                    'success': False,
                    'message': 'Verification code has expired'
                }

            # Mark OTP as used
            otp.mark_as_used()
            
            logger.info(f"Successfully verified OTP {code} for {email}")
            return {
                'success': True,
                'message': 'Verification successful',
                'otp': otp
            }

        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during verification'
            }

    @staticmethod
    def send_otp_email(otp, request=None):
        """
        Send OTP via email using templates
        
        Args:
            otp: OTP instance
            request: HTTP request object (optional, for building URLs)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Determine subject based on OTP type
            subject_map = {
                'signup_verification': 'Welcome to MoreVans - Verify Your Account',
                'login_verification': 'MoreVans - Login Verification Code',
                'password_reset': 'MoreVans - Password Reset Verification',
                'email_change': 'MoreVans - Email Change Verification',
            }
            
            subject = subject_map.get(otp.otp_type, 'MoreVans - Verification Code')

            # Prepare context for template
            context = {
                'otp_code': otp.code,
                'otp_type': otp.otp_type,
                'user_name': otp.user.first_name or otp.user.email.split('@')[0],
                'company_name': 'MoreVans',
                'expiry_minutes': 10,
                'subject': subject,
                'support_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@morevans.com'),
                'support_phone': '+44 20 7946 0958',
                'sent_time': timezone.now(),
            }

            # Add purpose-specific context
            purpose_map = {
                'signup_verification': 'Account Verification',
                'login_verification': 'Login Verification',
                'password_reset': 'Password Reset',
                'email_change': 'Email Change Verification',
            }
            context['otp_purpose'] = purpose_map.get(otp.otp_type, 'Verification')

            # Add login URL if request is available
            if request:
                context['login_url'] = request.build_absolute_uri(reverse('login'))

            # Load templates
            html_template = get_template('emails/otp_verification.html')
            text_template = get_template('emails/otp_verification.txt')

            html_content = html_template.render(context)
            text_content = text_template.render(context)

            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@morevans.com'),
                to=[otp.email]
            )
            msg.attach_alternative(html_content, "text/html")

            # Send email
            msg.send()
            
            logger.info(f"OTP email sent successfully to {otp.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP email to {otp.email}: {str(e)}")
            return False

    @staticmethod
    def cleanup_expired_otps():
        """Clean up expired OTP records"""
        expired_count = OTP.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired OTP records")
        
        return expired_count

    @staticmethod
    def check_rate_limit(email, ip_address, max_attempts=5, window_minutes=15):
        """
        Check if user has exceeded rate limit for OTP requests
        
        Args:
            email: Email address
            ip_address: IP address
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
        
        Returns:
            dict: Rate limit check result
        """
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        
        # Count recent attempts for this email
        email_attempts = OTP.objects.filter(
            email=email,
            created_at__gte=window_start
        ).count()
        
        # Count recent attempts from this IP
        ip_attempts = OTP.objects.filter(
            user__last_login__isnull=False,  # Only count logged-in users
            created_at__gte=window_start
        ).values('user__email').distinct().count()

        if email_attempts >= max_attempts:
            logger.warning(f"Rate limit exceeded for email {email}: {email_attempts} attempts")
            return {
                'allowed': False,
                'message': f'Too many verification requests. Please wait {window_minutes} minutes before trying again.',
                'retry_after': window_minutes * 60
            }

        if ip_attempts >= max_attempts * 2:  # More lenient for IP-based limiting
            logger.warning(f"Rate limit exceeded for IP {ip_address}: {ip_attempts} attempts")
            return {
                'allowed': False,
                'message': 'Too many verification requests from this location. Please try again later.',
                'retry_after': window_minutes * 60
            }

        return {
            'allowed': True,
            'remaining_attempts': max_attempts - email_attempts
        }

    @staticmethod
    def record_login_attempt(email, ip_address, is_successful=False):
        """Record login attempt for tracking and rate limiting"""
        LoginAttempt.objects.create(
            email=email,
            ip_address=ip_address,
            is_successful=is_successful
        )

    @staticmethod
    def get_failed_login_attempts(email, window_minutes=30):
        """Get count of failed login attempts within time window"""
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        return LoginAttempt.objects.filter(
            email=email,
            is_successful=False,
            attempt_time__gte=window_start
        ).count()