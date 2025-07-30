from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from apps.User.models import User
from apps.User.serializer import UserAuthSerializer, UserSerializer
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, AccessToken
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.settings import api_settings
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import (
    TokenError,
    InvalidToken,
    AuthenticationFailed,
)
from django.core.cache import cache
from django.utils import timezone
import logging

from .serializer import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordRecoverySerializer,
    PasswordResetConfirmSerializer,
    RegisterSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginWithOTPSerializer,
    MFALoginVerifySerializer,
)
from .utils import (
    mask_email,
    get_client_ip,
    increment_failed_logins,
    is_account_locked,
    reset_failed_logins,
)
from .utils import send_otp_utility, verify_otp_utility

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate and send OTP for email verification using custom OTP utility
            otp_result = send_otp_utility(user, "signup", user.email)

            if otp_result["success"]:
                return Response(
                    {
                        "message": "User created successfully. Please check your email for verification code.",
                        "email": otp_result.get("masked_email"),
                        "user_id": str(user.id),
                        "otp_sent": True,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {
                        "message": "User created but failed to send verification email. Please request a new OTP.",
                        "user_id": str(user.id),
                        "otp_sent": False,
                        "error": otp_result.get("message"),
                    },
                    status=status.HTTP_201_CREATED,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Explicitly skip authentication for login
    throttle_classes = [AnonRateThrottle]  # Add rate limiting

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})

        try:
            serializer.is_valid(raise_exception=False)
            if not serializer.is_valid():
                # Log failed login attempt but return generic error
                ip = get_client_ip(request)
                email = request.data.get("email", "unknown")
                logger.warning(f"Failed login attempt for {email} from IP {ip}")
                # Increment failed login counter in cache
                increment_failed_logins(email, ip)
                return Response(
                    {"detail": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user = serializer.validated_data["user"]

            # Check if account requires further verification
            if hasattr(user, "requires_verification") and user.requires_verification:
                return Response(
                    {
                        "detail": "Account requires verification. Please check your email."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if account is locked due to too many failed attempts
            if is_account_locked(user.email):
                return Response(
                    {
                        "detail": "Account temporarily locked. Try again later or reset your password."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Record successful login
            ip = get_client_ip(request)
            logger.info(f"Successful login for user {user.id} from IP {ip}")
            reset_failed_logins(user.email)

            # Log user activity
            from apps.User.models import UserActivity

            UserActivity.objects.create(
                user=user, activity_type="login", details={"ip": ip}
            )

            # Update last login timestamp
            user.last_login = timezone.now()
            user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Create response with user data but no tokens in the body
            response = Response({"user": UserAuthSerializer(user).data})

            # Add tokens to response headers
            response["Authorization"] = f"Bearer {access_token}"
            response["X-Refresh-Token"] = refresh_token

            # Set Access-Control-Expose-Headers to make headers available to JavaScript
            response["Access-Control-Expose-Headers"] = "Authorization, X-Refresh-Token"

            return response

        except Exception as e:
            # Log the exception securely without exposing details
            logger.exception(f"Login error: {str(e)}")
            return Response(
                {"detail": "Authentication failed. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "No valid token provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Extract the token
            token = auth_header.split(" ")[1]

            # Verify the token
            token_backend = TokenBackend(algorithm=api_settings.ALGORITHM)
            token_data = token_backend.decode(token, verify=False)

            # Blacklist the token
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

            BlacklistedToken.objects.create(
                token=token,
                user_id=token_data.get("user_id"),
                expires_at=timezone.datetime.fromtimestamp(
                    token_data.get("exp"), tz=timezone.utc
                ),
            )

            return Response(
                {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {"detail": "Logout failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordRecoveryAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, don't reveal if user exists or not
            return Response(
                {
                    "detail": "If an account exists, a password reset email has been sent."
                },
                status=status.HTTP_200_OK,
            )

        # Generate password reset token
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Create reset URL
        reset_url = request.build_absolute_uri(
            reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
        )

        # Send password reset email
        try:
            send_mail(
                subject="Password Reset Request",
                message=f"Click the following link to reset your password: {reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {"detail": "Password reset email sent successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return Response(
                {"detail": "Failed to send password reset email. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetConfirmAPIView(APIView):
    """
    API endpoint for confirming a password reset.

    - Accepts a JSON payload with the following format:
      {
        "password": "<new password>",
        "uidb64": "<base64 encoded user id>",
        "token": "<reset token>"
      }

    - Returns a JSON response with the following format:
      {
        "detail": "Password reset successfully"
      }

    - If the token is invalid, returns a JSON response with the following format:
      {
        "detail": "Invalid token"
      }
      with a 400 status code.

    :param request: The request object.
    :param uidb64: The base64 encoded user id.
    :param token: The token to verify the user.
    :return: A JSON response with the result of the operation.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode user ID
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            # Verify token
            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return Response(
                    {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
                )

            # Set new password
            user.set_password(serializer.validated_data["password"])
            user.save()

            return Response(
                {"detail": "Password reset successfully."}, status=status.HTTP_200_OK
            )

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )


class PasswordChangeAPIView(APIView):
    """
    API endpoint for changing the current user's password.

    - Accepts a JSON payload with the following format:
      {
        "old_password": "<current password>",
        "new_password": "<new password>"
      }

    - Returns a JSON response with the following format:
      {
        "detail": "Password updated successfully"
      }

    - Returns a JSON response with the following format in case of an error:
      {
        "old_password": "<error message>"
      }

    - Requires the "is_authenticated" permission.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Check old password
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": "Password updated successfully."}, status=status.HTTP_200_OK
        )


class TokenRefreshView(APIView):
    """
    Takes a refresh token and returns an access token if the refresh token is valid.
    This view expects the refresh token to be in an HTTP-only cookie.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Detailed header logging
        logger.debug("=== Token Refresh Request Headers ===")
        for header, value in request.headers.items():
            logger.debug(f"{header}: {value}")
        logger.debug("=====================================")

        # Get refresh token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "No valid refresh token provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = auth_header.split(" ")[1]

        try:
            # Verify and decode the refresh token
            token_backend = TokenBackend(algorithm=api_settings.ALGORITHM)
            token_data = token_backend.decode(refresh_token, verify=True)

            # Get user from token
            user_id = token_data.get("user_id")
            if not user_id:
                return Response(
                    {"detail": "Invalid token format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.get(id=user_id)

            # Check if token is blacklisted
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

            if BlacklistedToken.objects.filter(token=refresh_token).exists():
                return Response(
                    {"detail": "Token has been blacklisted."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Generate new access token
            refresh = RefreshToken.for_user(user)
            new_access_token = str(refresh.access_token)

            return Response(
                {
                    "access_token": new_access_token,
                    "refresh_token": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_active": user.is_active,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except TokenError as e:
            logger.warning(f"Token refresh error: {str(e)}")
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.exception(f"Token refresh error: {str(e)}")
            return Response(
                {"detail": "An error occurred during token refresh."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TokenVerifyView(APIView):
    """
    Takes a token and returns a success response if it is valid.
    This allows clients to validate both access and refresh tokens.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "No valid token provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = auth_header.split(" ")[1]

        try:
            # Verify and decode the token
            token_backend = TokenBackend(algorithm=api_settings.ALGORITHM)
            token_data = token_backend.decode(token, verify=True)

            # Get user from token
            user_id = token_data.get("user_id")
            if not user_id:
                return Response(
                    {"detail": "Invalid token format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.get(id=user_id)

            # Check if token is blacklisted
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

            if BlacklistedToken.objects.filter(token=token).exists():
                return Response(
                    {"detail": "Token has been blacklisted."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return Response(
                {
                    "valid": True,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_active": user.is_active,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except TokenError as e:
            logger.warning(f"Token verification error: {str(e)}")
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.exception(f"Token verification error: {str(e)}")
            return Response(
                {"detail": "An error occurred during token verification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SendOTPView(APIView):
    """Send OTP to user's email"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        phone_number = serializer.validated_data.get("phone_number")
        otp_type = serializer.validated_data["otp_type"]

        try:
            # Get user based on email or phone
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response(
                        {
                            "message": "User not found with this email address.",
                            "error_code": "USER_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    return Response(
                        {
                            "message": "User not found with this phone number.",
                            "error_code": "USER_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {
                        "message": "Either email or phone number is required.",
                        "error_code": "MISSING_CONTACT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Send OTP
            result = send_otp_utility(user, otp_type, user.email)

            if result["success"]:
                return Response(
                    {
                        "message": result["message"],
                        "masked_email": result.get("masked_email"),
                        "validity_minutes": result.get("validity_minutes"),
                        "otp_type": otp_type,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "message": result["message"],
                        "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error in SendOTPView: {str(e)}")
            return Response(
                {
                    "message": "Failed to send OTP. Please try again.",
                    "error_code": "SEND_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyOTPView(APIView):
    """Verify OTP and perform action based on type"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = MFALoginVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data["otp_code"]

        try:
            # Get user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {
                        "message": "User not found with this email address.",
                        "error_code": "USER_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Verify OTP
            result = verify_otp_utility(user, otp_code, otp_type)

            if result["success"]:
                response_data = {
                    "message": result["message"],
                    "action": result.get("action"),
                    "user_id": str(user.id),
                }

                # Handle different OTP types
                if otp_type == "signup":
                    # Activate user account
                    user.is_active = True
                    user.save()

                    # Update verification status
                    verification, created = UserVerification.objects.get_or_create(
                        user=user, defaults={"email_verified": True}
                    )
                    if not created:
                        verification.email_verified = True
                        verification.email_verified_at = timezone.now()
                        verification.save()

                    response_data["message"] = (
                        "Email verified successfully. Your account is now active."
                    )

                elif otp_type == "login":
                    # Generate JWT tokens for login
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)

                    response_data.update({"user": UserAuthSerializer(user).data})

                    # Create response with user data but no tokens in the body
                    response = Response(response_data, status=status.HTTP_200_OK)

                    # Add tokens to response headers
                    response["Authorization"] = f"Bearer {access_token}"
                    response["X-Refresh-Token"] = refresh_token

                    # Set Access-Control-Expose-Headers to make headers available to JavaScript
                    response["Access-Control-Expose-Headers"] = (
                        "Authorization, X-Refresh-Token"
                    )

                    return response

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {
                        "message": result["message"],
                        "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error in VerifyOTPView: {str(e)}")
            return Response(
                {
                    "message": "Failed to verify OTP. Please try again.",
                    "error_code": "VERIFICATION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResendOTPView(APIView):
    """Resend OTP with cooldown"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        phone_number = serializer.validated_data.get("phone_number")
        otp_type = serializer.validated_data["otp_type"]

        try:
            # Get user based on email or phone
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response(
                        {
                            "message": "User not found with this email address.",
                            "error_code": "USER_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    return Response(
                        {
                            "message": "User not found with this phone number.",
                            "error_code": "USER_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {
                        "message": "Either email or phone number is required.",
                        "error_code": "MISSING_CONTACT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check cooldown
            cooldown_key = f"otp_cooldown:{user.id}:{otp_type}"
            if cache.get(cooldown_key):
                return Response(
                    {
                        "message": "Please wait before requesting another OTP.",
                        "error_code": "COOLDOWN_ACTIVE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Send OTP
            result = send_otp_utility(user, otp_type, user.email)

            if result["success"]:
                # Set cooldown
                cache.set(cooldown_key, True, timeout=60)  # 1 minute cooldown

                return Response(
                    {
                        "message": result["message"],
                        "masked_email": result.get("masked_email"),
                        "validity_minutes": result.get("validity_minutes"),
                        "otp_type": otp_type,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "message": result["message"],
                        "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error in ResendOTPView: {str(e)}")
            return Response(
                {
                    "message": "Failed to resend OTP. Please try again.",
                    "error_code": "RESEND_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginWithOTPView(APIView):
    """Login with OTP (passwordless login)"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = LoginWithOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data.get("otp_code")
        request_otp = serializer.validated_data.get("request_otp", False)

        try:
            # Get user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {
                        "message": "User not found with this email address.",
                        "error_code": "USER_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # If requesting OTP
            if request_otp or not otp_code:
                result = send_otp_utility(user, "login", user.email)

                if result["success"]:
                    return Response(
                        {
                            "message": result["message"],
                            "masked_email": result.get("masked_email"),
                            "validity_minutes": result.get("validity_minutes"),
                            "next_step": "verify_otp",
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "message": result["message"],
                            "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # If verifying OTP
            if otp_code:
                result = verify_otp_utility(user, otp_code, "login")

                if result["success"]:
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)

                    # Create response with user data but no tokens in the body
                    response = Response(
                        {
                            "message": "Login successful.",
                            "user": UserAuthSerializer(user).data,
                        },
                        status=status.HTTP_200_OK,
                    )

                    # Add tokens to response headers
                    response["Authorization"] = f"Bearer {access_token}"
                    response["X-Refresh-Token"] = refresh_token

                    # Set Access-Control-Expose-Headers to make headers available to JavaScript
                    response["Access-Control-Expose-Headers"] = (
                        "Authorization, X-Refresh-Token"
                    )

                    return response
                else:
                    return Response(
                        {
                            "message": result["message"],
                            "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            logger.error(f"Error in LoginWithOTPView: {str(e)}")
            return Response(
                {
                    "message": "Failed to process login request. Please try again.",
                    "error_code": "LOGIN_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MFALoginView(APIView):
    """MFA Login - Step 1: Authenticate with email/password and send OTP"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})

        try:
            serializer.is_valid(raise_exception=False)
            if not serializer.is_valid():
                # Log failed login attempt but return generic error
                ip = get_client_ip(request)
                email = request.data.get("email", "unknown")
                logger.warning(f"Failed MFA login attempt for {email} from IP {ip}")
                # Increment failed login counter in cache
                increment_failed_logins(email, ip)
                return Response(
                    {"detail": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user = serializer.validated_data["user"]

            # Check if account requires further verification
            if hasattr(user, "requires_verification") and user.requires_verification:
                return Response(
                    {
                        "detail": "Account requires verification. Please check your email."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if account is locked due to too many failed attempts
            if is_account_locked(user.email):
                return Response(
                    {
                        "detail": "Account temporarily locked. Try again later or reset your password."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Reset failed login attempts since first factor passed
            reset_failed_logins(user.email)

            # Send OTP for second factor
            result = send_otp_utility(user, "login", user.email)

            if result["success"]:
                return Response(
                    {
                        "message": "First factor authentication successful. Please check your email for OTP.",
                        "masked_email": result.get("masked_email"),
                        "validity_minutes": result.get("validity_minutes"),
                        "next_step": "verify_otp",
                        "user_id": str(user.id),
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "message": "Authentication successful but failed to send OTP. Please try again.",
                        "error_code": result.get("error_code", "OTP_SEND_FAILED"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.exception(f"MFA login error: {str(e)}")
            return Response(
                {"detail": "Authentication failed. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class VerifyMFALoginView(APIView):
    """MFA Login - Step 2: Verify OTP and complete login"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        phone_number = serializer.validated_data.get("phone_number")
        otp_code = serializer.validated_data["otp_code"]

        try:
            # Get user based on email or phone
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response(
                        {
                            "message": "User not found with this email address.",
                            "error_code": "USER_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    return Response(
                        {
                            "message": "User not found with this phone number.",
                            "error_code": "USER_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {
                        "message": "Either email or phone number is required.",
                        "error_code": "MISSING_CONTACT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify OTP
            result = verify_otp_utility(user, otp_code, "login")

            if result["success"]:
                # Record successful login
                ip = get_client_ip(request)
                logger.info(f"Successful MFA login for user {user.id} from IP {ip}")

                # Log user activity
                from apps.User.models import UserActivity

                UserActivity.objects.create(
                    user=user, activity_type="mfa_login", details={"ip": ip}
                )

                # Update last login timestamp
                user.last_login = timezone.now()
                user.save()

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Create response with user data but no tokens in the body
                response = Response(
                    {
                        "message": "MFA login successful.",
                        "user": UserAuthSerializer(user).data,
                    }
                )

                # Add tokens to response headers
                response["Authorization"] = f"Bearer {access_token}"
                response["X-Refresh-Token"] = refresh_token

                # Set Access-Control-Expose-Headers to make headers available to JavaScript
                response["Access-Control-Expose-Headers"] = (
                    "Authorization, X-Refresh-Token"
                )

                return response
            else:
                return Response(
                    {
                        "message": result["message"],
                        "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error in VerifyMFALoginView: {str(e)}")
            return Response(
                {
                    "message": "Failed to verify MFA login. Please try again.",
                    "error_code": "VERIFICATION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
