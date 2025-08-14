from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from apps.User.models import User
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework import status
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db.models import Q
import logging
from .models import UserVerification, OTP
from .utils import mask_email, mask_phone, OTPValidator


class EmailAlreadyExistsException(APIException):
    """Custom exception for email already exists with 409 status code"""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "User with this email already exists"
    default_code = "email_already_exists"


class PhoneNumberAlreadyExistsException(APIException):
    """Custom exception for phone number already exists with 409 status code"""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "User with this phone number already exists"
    default_code = "phone_number_already_exists"


logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    # phone_number = serializers.CharField(required=False, allow_blank=True)
    # user_type = serializers.ChoiceField(
    #     choices=User.USER_TYPE_CHOICES,
    #     default='customer'
    # )

    class Meta:
        model = User
        fields = ("email", "password", "password2", "first_name", "last_name")

    def validate(self, attrs):
        # Check if passwords match
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        # Check if user with email already exists
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise EmailAlreadyExistsException()

        # Check if user with phone number already exists (if provided)
        phone_number = attrs.get("phone_number")
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise PhoneNumberAlreadyExistsException()

        return attrs

    def create(self, validated_data):
        try:
            # Remove confirmation field
            validated_data.pop("password2", None)

            # Create user with all provided fields
            user = User.objects.create_user(
                email=validated_data["email"].lower().strip(),
                password=validated_data["password"],
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
                # phone_number=validated_data.get('phone_number', ''),
                # user_type=validated_data.get('user_type', 'customer')
            )

            # Set user as inactive until email verification
            user.is_active = False
            user.save()

            # Create UserVerification record
            UserVerification.objects.create(user=user)

            # Additional setup steps can be added here
            # For example, creating default profiles, settings, etc.

            return user
        except IntegrityError as e:
            # Handle case where a race condition might occur
            # (e.g., two users registering with the same email simultaneously)
            if "unique constraint" in str(e).lower() and "email" in str(e).lower():
                raise EmailAlreadyExistsException()
            elif (
                "unique constraint" in str(e).lower()
                and "phone_number" in str(e).lower()
            ):
                raise PhoneNumberAlreadyExistsException()
            raise serializers.ValidationError(
                {"detail": "Registration failed due to database constraint."}
            )
        except Exception as e:
            # Log the exception for debugging
            logger.exception("Error creating user")

            # Return a generic error message to the user
            raise serializers.ValidationError(
                {"detail": "Registration failed. Please try again later."}
            )


class OTPSerializer(serializers.Serializer):
    """Serializer for OTP verification"""

    otp_code = serializers.CharField(max_length=6, min_length=6)


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp_type = serializers.ChoiceField(choices=[choice[0] for choice in OTP.OTP_TYPES])

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone_number"):
            raise serializers.ValidationError(
                "Either email or phone number is required"
            )
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_type = serializers.ChoiceField(choices=[choice[0] for choice in OTP.OTP_TYPES])

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone_number"):
            raise serializers.ValidationError(
                "Either email or phone number is required"
            )
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp_type = serializers.ChoiceField(choices=[choice[0] for choice in OTP.OTP_TYPES])

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone_number"):
            raise serializers.ValidationError(
                "Either email or phone number is required"
            )
        return attrs


class LoginWithOTPSerializer(serializers.Serializer):
    """Serializer for login with OTP"""

    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6, required=False)
    request_otp = serializers.BooleanField(default=False)


class MFALoginVerifySerializer(serializers.Serializer):
    """Serializer for MFA login verification"""

    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)


class MFALoginSerializer(serializers.Serializer):
    """Serializer for MFA login verification"""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        logger.info(f"Login attempt for email: {email}")

        if not email or not password:
            logger.warning("Login attempt without email or password")
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(
                {"detail": msg, "code": "missing_fields"}, code="authorization"
            )

        # Check if user exists before attempting authentication
        try:
            user_exists = User.objects.filter(email__iexact=email.lower()).exists()
            if not user_exists:
                logger.warning(f"User with email {email} not found in database")
                raise serializers.ValidationError(
                    {"detail": "User not found", "code": "user_not_found"},
                    code="authorization",
                )
        except Exception as e:
            logger.exception(f"Error checking user existence: {str(e)}")

        # Try both email and email_or_phone parameters for authentication
        # First attempt with email parameter
        user = authenticate(
            request=self.context.get("request"),
            email=email.lower(),  # Ensure lowercase email
            password=password,
        )

        # If that fails, try with email_or_phone parameter
        if not user:
            logger.info(
                f"First authentication attempt failed, trying with email_or_phone"
            )
            user = authenticate(
                request=self.context.get("request"),
                email_or_phone=email.lower(),  # Ensure lowercase
                password=password,
            )

        if user:
            # Check Django's is_active field first
            if not user.is_active:
                logger.warning(f"User {email} is inactive (Django is_active=False)")
                raise serializers.ValidationError(
                    "User account is disabled.",
                    code="inactive_account",
                )

            # Check custom account_status field for more specific statuses
            account_status = getattr(user, "account_status", "active")

            if account_status == "inactive":
                logger.warning(f"User {email} has inactive account status")
                raise serializers.ValidationError(
                    "Your account is currently inactive. Please contact support to reactivate your account.",
                    code="account_inactive",
                )
            elif account_status == "pending":
                logger.warning(f"User {email} has pending account status")
                raise serializers.ValidationError(
                    "Your account is pending approval. You will receive an email once your account is activated.",
                    code="account_pending",
                )
            elif account_status == "suspended":
                logger.warning(f"User {email} has suspended account status")
                raise serializers.ValidationError(
                    "Your account has been temporarily suspended. Please contact support for more information.",
                    code="account_suspended",
                )
            elif account_status == "deleted":
                logger.warning(f"User {email} has deleted account status")
                raise serializers.ValidationError(
                    "This account has been deleted. Please contact support if you believe this is an error.",
                    code="account_deleted",
                )
            elif account_status == "banned":
                logger.warning(f"User {email} has banned account status")
                raise serializers.ValidationError(
                    "Your account has been permanently banned due to policy violations.",
                    code="account_banned",
                )
            elif account_status == "expired":
                logger.warning(f"User {email} has expired account status")
                raise serializers.ValidationError(
                    "Your account has expired. Please renew your subscription or contact support.",
                    code="account_expired",
                )
            elif account_status != "active":
                # Catch any other unexpected status values
                logger.warning(
                    f"User {email} has unknown account status: {account_status}"
                )
                raise serializers.ValidationError(
                    "Your account status is unknown. Please contact support for assistance.",
                    code="account_unknown_status",
                )

            logger.info(f"Authentication successful for {email}")
        else:
            # Check if user exists but credentials are invalid
            user_exists = User.objects.filter(email__iexact=email.lower()).exists()
            if not user_exists:
                logger.warning(f"User with email {email} not found in database")
                raise serializers.ValidationError(
                    {"detail": "User not found 11", "code": "user_not_found"},
                    code="authorization",
                )
            else:
                # User exists but password is wrong
                logger.warning(
                    f"Authentication failed for {email} - invalid credentials"
                )
                raise serializers.ValidationError(
                    {"detail": "Invalid password", "code": "invalid_credentials"},
                    code="authorization",
                )

        attrs["user"] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        logger.info(f"Login attempt for email: {email}")

        if not email or not password:
            logger.warning("Login attempt without email or password")
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(
                {"detail": msg, "code": "missing_fields"}, code="authorization"
            )

        # Check if user exists before attempting authentication
        try:
            user_exists = User.objects.filter(email__iexact=email.lower()).exists()
            if not user_exists:
                logger.warning(f"User with email {email} not found in database")
                raise serializers.ValidationError(
                    {"detail": "User not found", "code": "user_not_found"},
                    code="authorization",
                )
        except Exception as e:
            logger.exception(f"Error checking user existence: {str(e)}")

        # Try both email and email_or_phone parameters for authentication
        # First attempt with email parameter
        user = authenticate(
            request=self.context.get("request"),
            email=email.lower(),
            password=password,
        )

        # If that fails, try with email_or_phone parameter
        if not user:
            logger.info(
                f"First authentication attempt failed, trying with email_or_phone"
            )
            user = authenticate(
                request=self.context.get("request"),
                email_or_phone=email.lower(),  # Ensure lowercase
                password=password,
            )

        if user:
            # Make sure the user is active
            if not user.is_active:
                logger.warning(f"User {email} is inactive")
                raise serializers.ValidationError(
                    {"detail": "User account is disabled.", "code": "inactive_account"},
                    code="authorization",
                )
            logger.info(f"Authentication successful for {email}")
        else:
            # Check if user exists but credentials are invalid
            user_exists = User.objects.filter(email__iexact=email.lower()).exists()
            if not user_exists:
                logger.warning(f"User with email {email} not found in database")
                raise serializers.ValidationError(
                    {"detail": "User not found 11", "code": "user_not_found"},
                    code="authorization",
                )
            else:
                # User exists but password is wrong
                logger.warning(
                    f"Authentication failed for {email} - invalid credentials"
                )
                raise serializers.ValidationError(
                    {"detail": "Invalid password", "code": "invalid_credentials"},
                    code="authorization",
                )

        attrs["user"] = user
        return attrs


class PasswordRecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    token = serializers.CharField(write_only=True, required=True)
    uidb64 = serializers.CharField(write_only=True, required=True)


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, validators=[validate_password])


from .models import OTP
from .utils import OTPValidator
