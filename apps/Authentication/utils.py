from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
                'user_name': user.first_name or user.email.split('@')[0],
                'otp_code': otp.otp_code,
                'validity_minutes': int((otp.expires_at - timezone.now()).total_seconds() / 60),
                'app_name': kwargs.get('app_name', 'MoveVans'),
                'current_year': datetime.now().year,
            }
            
            # Set specific messages and subjects based on OTP type
            if otp_type == 'signup':
                context['subject'] = 'Verify Your Email Address'
                context['message'] = 'Thank you for signing up! Please use the code below to verify your email address and complete your registration.'
                context['action_text'] = 'Complete Registration'
            elif otp_type == 'login':
                context['subject'] = 'Your Login Verification Code'
                context['message'] = 'You requested a login verification code. Please use the code below to complete your login.'
                context['action_text'] = 'Complete Login'
            elif otp_type == 'password_reset':
                context['subject'] = 'Reset Your Password'
                context['message'] = 'You requested to reset your password. Please use the code below to verify your identity.'
                context['action_text'] = 'Reset Password'
            elif otp_type == 'email_change':
                context['subject'] = 'Verify Your New Email Address'
                context['message'] = 'You requested to change your email address. Please use the code below to verify your new email.'
                context['action_text'] = 'Verify Email'
            else:
                context['subject'] = 'Your Verification Code'
                context['message'] = 'Please use the code below to complete your verification.'
                context['action_text'] = 'Verify'
            
            # Add any additional context passed in kwargs
            context.update(kwargs)
            
            # Render email templates
            html_content = render_to_string('emails/otp_verification.html', context)
            text_content = render_to_string('emails/otp_verification.txt', context)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=context['subject'],
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
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


def mask_email(email):
    """Mask email address for security (e.g., j***@example.com)"""
    if '@' not in email:
        return email
    
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone):
    """Mask phone number for security (e.g., +1 ***-***-1234)"""
    if not phone or len(phone) < 4:
        return phone
    
    # Keep last 4 digits visible
    return '*' * (len(phone) - 4) + phone[-4:]