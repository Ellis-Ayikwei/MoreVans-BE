from apps.User.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    # first_name = serializers.CharField(required=True)
    # last_name = serializers.CharField(required=True)
    # phone_number = serializers.CharField(required=False, allow_blank=True)
    # user_type = serializers.ChoiceField(
    #     choices=User.USER_TYPE_CHOICES,
    #     default='customer'
    # )

    class Meta:
        model = User
        fields = ("email", "password", "password2")

    def validate(self, attrs):
        # Check if passwords match
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        # Check if user with email already exists
        email = attrs.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "User with this email already exists."}
            )

        # Check if user with phone number already exists (if provided)
        phone_number = attrs.get("phone_number")
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError(
                {"phone_number": "User with this phone number already exists."}
            )

        return attrs

    def create(self, validated_data):
        try:
            # Remove confirmation field
            validated_data.pop("password2", None)

            # Create user with all provided fields
            user = User.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                # first_name=validated_data.get('first_name', ''),
                # last_name=validated_data.get('last_name', ''),
                # phone_number=validated_data.get('phone_number', ''),
                # user_type=validated_data.get('user_type', 'customer')
            )

            # Additional setup steps can be added here
            # For example, creating default profiles, settings, etc.

            return user
        except IntegrityError as e:
            # Handle case where a race condition might occur
            # (e.g., two users registering with the same email simultaneously)
            if "unique constraint" in str(e).lower() and "email" in str(e).lower():
                raise serializers.ValidationError(
                    {"email": "User with this email already exists."}
                )
            elif (
                "unique constraint" in str(e).lower()
                and "phone_number" in str(e).lower()
            ):
                raise serializers.ValidationError(
                    {"phone_number": "User with this phone number already exists."}
                )
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


# accounts/serializers.py (add these)
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


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
