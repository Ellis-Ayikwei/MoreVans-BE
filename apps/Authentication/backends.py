from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from User.models import User
import logging

logger = logging.getLogger(__name__)

class EmailOrPhoneBackend(BaseBackend):
    def authenticate(self, request, email=None, email_or_phone=None, password=None, **kwargs):
        # For debugging purposes
        logger.debug(f"Authentication attempt with email: {email}, email_or_phone: {email_or_phone}")
        
        if password is None:
            logger.debug("No password provided, authentication failed")
            return None
            
        # Determine which parameter to use
        lookup_value = email if email is not None else email_or_phone
        
        if lookup_value is None:
            logger.debug("No lookup value provided, authentication failed")
            return None

        try:
            # Check if it's an email or phone number
            if '@' in lookup_value:
                # Normalize email to lowercase for case-insensitive comparison
                normalized_email = lookup_value.lower()
                logger.debug(f"Looking up user with email: {normalized_email}")
                user = User.objects.get(email__iexact=normalized_email)
            else:
                logger.debug(f"Looking up user with phone: {lookup_value}")
                user = User.objects.get(phone_number=lookup_value)
                
            logger.debug(f"User found: {user.email}")
        except User.DoesNotExist:
            logger.debug("User not found")
            return None
        except Exception as e:
            logger.exception("Error during user lookup")
            return None

        # Verify the password
        if user and check_password(password, user.password):
            logger.debug("Password verified, authentication successful")
            return user
            
        logger.debug("Password verification failed")
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None