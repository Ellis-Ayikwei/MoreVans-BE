import json
import os
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
from datetime import timezone as dt_timezone
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
    MFALoginSerializer,
)
from .utils import (
    mask_email,
    get_client_ip,
    increment_failed_logins,
    is_account_locked,
    reset_failed_logins,
)
from .error_handlers import (
    get_verification_required_response,
    get_account_locked_response,
    get_invalid_credentials_response,
    get_user_not_found_response,
)
from .utils import send_otp_utility, verify_otp_utility, OTPValidator
from .models import OTP, UserVerification
from .models import TrustedDevice, LoginSession

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
        print("request.data", request.data)

        try:
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
                            "validity_minutes": otp_result.get("validity_minutes"),
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    # Handle different OTP send failure types with appropriate status codes
                    if otp_result.get("status_code") == 429:
                        return Response(
                            {
                                "message": "User created but rate limit exceeded for verification email. Please wait before requesting a new OTP.",
                                "user_id": str(user.id),
                                "otp_sent": False,
                                "error_code": otp_result.get(
                                    "error_code", "OTP_RATE_LIMIT"
                                ),
                            },
                            status=status.HTTP_201_CREATED,
                        )
                    elif otp_result.get("status_code") == 503:
                        return Response(
                            {
                                "message": "User created but email service is temporarily unavailable. Please request a new OTP later.",
                                "user_id": str(user.id),
                                "otp_sent": False,
                                "error_code": otp_result.get(
                                    "error_code", "EMAIL_SERVICE_UNAVAILABLE"
                                ),
                            },
                            status=status.HTTP_201_CREATED,
                        )
                    else:
                        return Response(
                            {
                                "message": "User created but failed to send verification email. Please request a new OTP.",
                                "user_id": str(user.id),
                                "otp_sent": False,
                                "error_code": otp_result.get(
                                    "error_code", "OTP_SEND_FAILED"
                                ),
                            },
                            status=status.HTTP_201_CREATED,
                        )
            else:
                # Return structured validation errors
                return Response(
                    {
                        "message": "Registration failed due to validation errors.",
                        "error_code": "VALIDATION_ERROR",
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"User registration error: {str(e)}")

            # Import custom exceptions
            from apps.Authentication.serializer import (
                EmailAlreadyExistsException,
                PhoneNumberAlreadyExistsException,
            )

            # Handle specific conflict exceptions
            if isinstance(e, EmailAlreadyExistsException):
                return Response(
                    {
                        "message": "User with this email address already exists.",
                        "error_code": "EMAIL_ALREADY_EXISTS",
                        "detail": str(e.detail),
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            elif isinstance(e, PhoneNumberAlreadyExistsException):
                return Response(
                    {
                        "message": "User with this phone number already exists.",
                        "error_code": "PHONE_NUMBER_ALREADY_EXISTS",
                        "detail": str(e.detail),
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    {
                        "message": "Registration failed due to a server error. Please try again later.",
                        "error_code": "INTERNAL_SERVER_ERROR",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


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
            # if hasattr(user, "requires_verification") and user.requires_verification:
            #     return Response(
            #         {
            #             "action_required": "VERIFY_EMAIL",
            #             "detail": "Account requires verification. Please check your email.",
            #         },
            #         status=status.HTTP_403_FORBIDDEN,
            #     )

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

            # Use JWT's built-in blacklisting mechanism
            from rest_framework_simplejwt.tokens import AccessToken
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            # Decode the token to get user info
            token_backend = TokenBackend(algorithm=api_settings.ALGORITHM)
            token_data = token_backend.decode(token, verify=False)

            # Find the outstanding token and blacklist it
            try:
                outstanding_token = OutstandingToken.objects.get(
                    jti=token_data.get("jti"), user_id=token_data.get("user_id")
                )
                BlacklistedToken.objects.create(token=outstanding_token)
            except OutstandingToken.DoesNotExist:
                # If token not found in outstanding tokens, it's likely already expired or blacklisted
                # This is normal behavior, so we don't need to log it as a warning
                pass

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
    authentication_classes = (
        []
    )  # Avoid SessionAuthentication CSRF enforcement for anonymous POST

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

        frontend_base_url = os.getenv("FRONTEND_URL")
        frontend_url = f"{frontend_base_url}/reset-password/{uidb64}/{token}"
        reset_url = frontend_url

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
    authentication_classes = (
        []
    )  # Avoid SessionAuthentication CSRF enforcement for anonymous POST

    def post(self, request, uidb64, token):
        print("request data", request.data)
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get uidb64 and token from the validated data
        uidb64 = serializer.validated_data["uidb64"]
        token = serializer.validated_data["token"]

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
    authentication_classes = []

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
        # Minimal diagnostics without leaking secrets
        try:
            has_auth = bool(request.headers.get("Authorization"))
            has_x_refresh = bool(request.headers.get("X-Refresh-Token"))
            logger.debug(
                f"TokenRefreshView headers -> Authorization: {'present' if has_auth else 'missing'}, X-Refresh-Token: {'present' if has_x_refresh else 'missing'}"
            )
        except Exception:
            pass

        # Extract refresh token from multiple sources
        refresh_token_raw = (
            request.headers.get("X-Refresh-Token")
            or (
                request.data.get("refresh_token")
                if isinstance(request.data, dict)
                else None
            )
            or request.COOKIES.get("_auth_refresh")
            or None
        )

        if not refresh_token_raw:
            # Fallback: try Authorization header if client mistakenly sends refresh there
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                refresh_token_raw = auth_header.split(" ", 1)[1]

        if not refresh_token_raw:
            return Response(
                {"detail": "Refresh token not found in headers, body, or cookies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Normalize token string
        try:
            refresh_token_str = str(refresh_token_raw).strip().strip('"').strip("'")
        except Exception:
            return Response(
                {"detail": "Invalid refresh token format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(refresh_token_str) < 20:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Validate via SimpleJWT (raises TokenError on invalid/expired)
            refresh_obj = RefreshToken(refresh_token_str)

            # Ensure token type is refresh
            if refresh_obj.get("token_type") != "refresh":
                return Response(
                    {"detail": "Invalid token type for refresh."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Optional blacklist check omitted to avoid dependency on blacklist app state

            user_id = refresh_obj.get("user_id")
            if not user_id:
                return Response(
                    {"detail": "Invalid token payload."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_active:
                raise AuthenticationFailed("User is inactive")

            # Non-rotating: only issue a new access token
            access_token = str(refresh_obj.access_token)

            response = Response(status=status.HTTP_200_OK)
            response["Authorization"] = f"Bearer {access_token}"
            response["Access-Control-Expose-Headers"] = "Authorization"
            return response

        except TokenError as e:
            logger.warning(f"Token refresh error: {str(e)}")
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.exception(f"Token refresh error: {str(e)}")
            return Response(
                {"detail": "An error occurred during token refresh."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListTrustedDevicesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        if str(request.user.id) != str(user_id) and not request.user.is_staff:
            return Response(status=403)
        devices = TrustedDevice.objects.filter(user_id=user_id).order_by("-last_used")
        current_hash = None
        token = request.COOKIES.get("_auth_refresh")
        if token:
            import hashlib

            current_hash = hashlib.sha256(token.encode()).hexdigest()
        data = [
            {
                "id": str(d.id),
                "device_name": d.device_name,
                "device_info": d.device_info,
                "last_used": d.last_used,
                "created_at": d.created_at,
                "expires_at": d.expires_at,
                "is_active": d.is_active,
                "is_current": bool(
                    current_hash and current_hash == d.refresh_token_hash
                ),
            }
            for d in devices
        ]
        return Response(data)


class RevokeTrustedDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, device_id):
        td = TrustedDevice.objects.filter(id=device_id, user=request.user).first()
        if not td:
            return Response(status=404)
        td.is_active = False
        td.refresh_token_hash = ""
        td.save(update_fields=["is_active", "refresh_token_hash"])
        resp = Response({"success": True})
        # If current device, clear cookie
        token = request.COOKIES.get("_auth_refresh")
        if token:
            import hashlib

            if hashlib.sha256(token.encode()).hexdigest() == td.refresh_token_hash:
                resp.delete_cookie("_auth_refresh")
        return resp


class RevokeAllTrustedDevicesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        if str(request.user.id) != str(user_id) and not request.user.is_staff:
            return Response(status=403)
        TrustedDevice.objects.filter(user_id=user_id).update(
            is_active=False, refresh_token_hash=""
        )
        resp = Response({"success": True})
        resp.delete_cookie("_auth_refresh")
        return resp


# class TokenRefreshView(APIView):
#     """
#     Takes a refresh token and returns an access token if the refresh token is valid.
#     This view expects the refresh token to be in an HTTP-only cookie.
#     """

#     permission_classes = [permissions.AllowAny]

#     def post(self, request):
#         print("TokenRefreshView", request.headers)
#         # Detailed header logging
#         logger.debug("=== Token Refresh Request Headers ===")
#         for header, value in request.headers.items():
#             logger.debug(f"{header}: {value}")
#         logger.debug("=====================================")

#         # Get refresh token from X-Refresh-Token header first, then Authorization header
#         refresh_token = request.headers.get("X-Refresh-Token")
#         if not refresh_token:
#             # Fallback to Authorization header
#             auth_header = request.headers.get("Authorization")
#             if not auth_header or not auth_header.startswith("Bearer "):
#                 return Response(
#                     {"detail": "No valid refresh token provided."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             refresh_token = auth_header.split(" ")[1]

#         print("the refresh token", refresh_token)

#         try:
#             # Verify and decode the refresh token
#             token_backend = TokenBackend(algorithm=api_settings.ALGORITHM)

#             # Debug: Check if refresh_token is a string
#             if not isinstance(refresh_token, str):
#                 logger.error(
#                     f"Refresh token is not a string: {type(refresh_token)} - {refresh_token}"
#                 )
#                 return Response(
#                     {"detail": "Invalid refresh token format."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Debug: Check token length
#             if len(refresh_token) < 10:
#                 logger.error(
#                     f"Refresh token too short: {len(refresh_token)} characters"
#                 )
#                 return Response(
#                     {"detail": "Invalid refresh token length."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             token_data = token_backend.decode(refresh_token, verify=True)
#             print("the token data", token_data)

#             # Debug: Check token type
#             token_type = token_data.get("token_type")
#             if token_type != "refresh":
#                 logger.warning(f"Token type is {token_type}, expected 'refresh'")
#                 return Response(
#                     {"detail": "Invalid token type for refresh."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Get user from token
#             user_id = token_data.get("user_id")
#             if not user_id:
#                 return Response(
#                     {"detail": "Invalid token format."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             user = User.objects.get(id=user_id)

#             # Check if token is blacklisted
#             from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

#             if BlacklistedToken.objects.filter(token=refresh_token).exists():
#                 return Response(
#                     {"detail": "Token has been blacklisted."},
#                     status=status.HTTP_401_UNAUTHORIZED,
#                 )

#             # Generate new access token
#             refresh = RefreshToken.for_user(user)
#             new_access_token = str(refresh.access_token)

#             return Response(
#                 {
#                     "access_token": new_access_token,
#                     "refresh_token": str(refresh),
#                     "user": {
#                         "id": user.id,
#                         "email": user.email,
#                         "first_name": user.first_name,
#                         "last_name": user.last_name,
#                         "is_active": user.is_active,
#                     },
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except TokenError as e:
#             logger.warning(f"Token refresh error: {str(e)}")
#             return Response(
#                 {"detail": "Invalid refresh token."},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )
#         except User.DoesNotExist:
#             return Response(
#                 {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
#             )
#         except (TypeError, ValueError) as e:
#             # Handle JWT decoding errors (like "Expected a string value")
#             logger.warning(f"JWT decoding error: {str(e)}")
#             return Response(
#                 {"detail": "Invalid token format."},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )
#         except Exception as e:
#             logger.exception(f"Token refresh error: {str(e)}")
#             return Response(
#                 {"detail": "An error occurred during token refresh."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )


class TokenVerifyView(APIView):
    """
    Takes a token and returns a success response if it is valid.
    This allows clients to validate both access and refresh tokens.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Extract token from Authorization header, body, or cookies
        token_raw = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_raw = auth_header.split(" ", 1)[1]

        if not token_raw and isinstance(request.data, dict):
            token_raw = request.data.get("token")

        if not token_raw:
            cookie_token = request.COOKIES.get("_auth") or request.COOKIES.get(
                "access_token"
            )
            if cookie_token:
                token_raw = cookie_token

        if not token_raw:
            return Response(
                {"detail": "No valid token provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize token string
        token_str = str(token_raw).strip().strip('"').strip("'")
        if token_str.startswith("Bearer "):
            token_str = token_str.split(" ", 1)[1]

        if len(token_str) < 20:
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Try as access token first
        try:
            access = AccessToken(token_str)
            user_id = access.get("user_id")
            if not user_id:
                return Response(
                    {"detail": "Invalid token payload."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
                )

            return Response(
                {
                    "valid": True,
                    "token_type": "access",
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
        except TokenError:
            pass

        # Fallback: treat as refresh token
        try:
            refresh = RefreshToken(token_str)

            # Optional blacklist check omitted to reduce coupling to blacklist models

            user_id = refresh.get("user_id")
            if not user_id:
                return Response(
                    {"detail": "Invalid token payload."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
                )

            return Response(
                {
                    "valid": True,
                    "token_type": "refresh",
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
        except Exception as e:
            logger.exception(f"Token verification error: {str(e)}")
            return Response(
                {"detail": "An error occurred during token verification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DebugTokenView(APIView):
    """
    Debug endpoint to check JWT configuration and token decoding
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.conf import settings
        import os

        debug_info = {
            "secret_key_set": bool(settings.SECRET_KEY),
            "secret_key_length": len(settings.SECRET_KEY) if settings.SECRET_KEY else 0,
            "secret_key_start": (
                settings.SECRET_KEY[:10] + "..." if settings.SECRET_KEY else None
            ),
            "jwt_algorithm": getattr(settings, "SIMPLE_JWT", {}).get(
                "ALGORITHM", "Not set"
            ),
            "jwt_signing_key_set": bool(
                getattr(settings, "SIMPLE_JWT", {}).get("SIGNING_KEY")
            ),
            "env_secret_key": bool(os.getenv("DJANGO_SECRET_KEY")),
        }

        return Response(debug_info)


class SendOTPView(APIView):
    """Send OTP to user's email"""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
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
    authentication_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        print("the otp data", request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get("email")
        phone_number = serializer.validated_data.get("phone_number")
        otp_code = serializer.validated_data["otp_code"]
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
    authentication_classes = []

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
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
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
                if result["status_code"] == 429:
                    return Response(
                        {
                            "message": result["message"],
                            "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                elif result["status_code"] == 503:
                    return Response(
                        {
                            "message": result["message"],
                            "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
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
    authentication_classes = []

    def post(self, request):
        serializer = LoginWithOTPSerializer(data=request.data)
        print("the login with otp data", json.dumps(request.data, indent=4))
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
                    # Return appropriate error status based on error type
                    error_code = result.get("error_code", "UNKNOWN_ERROR")

                    if (
                        error_code == "RATE_LIMIT_EXCEEDED"
                        or error_code == "COOLDOWN_ACTIVE"
                    ):
                        status_code = status.HTTP_429_TOO_MANY_REQUESTS
                    elif error_code == "EMAIL_SEND_FAILED":
                        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                    else:
                        status_code = status.HTTP_400_BAD_REQUEST

                    return Response(
                        {
                            "message": result["message"],
                            "error_code": error_code,
                        },
                        status=status_code,
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
                    # Return appropriate error status based on error type
                    error_code = result.get("error_code", "UNKNOWN_ERROR")

                    if error_code == "INVALID_FORMAT":
                        status_code = status.HTTP_400_BAD_REQUEST
                    elif error_code == "OTP_NOT_FOUND":
                        status_code = status.HTTP_404_NOT_FOUND
                    elif error_code == "OTP_EXPIRED":
                        status_code = status.HTTP_410_GONE
                    elif error_code == "INVALID_OTP":
                        status_code = status.HTTP_401_UNAUTHORIZED
                    else:
                        status_code = status.HTTP_400_BAD_REQUEST

                    return Response(
                        {
                            "message": result["message"],
                            "error_code": error_code,
                            "remaining_attempts": result.get("remaining_attempts"),
                        },
                        status=status_code,
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
    authentication_classes = []

    def post(self, request):
        serializer = MFALoginSerializer(data=request.data, context={"request": request})
        print("the mfa login data", json.dumps(request.data, indent=4))
        try:
            serializer.is_valid(raise_exception=False)
            if not serializer.is_valid():
                # Check for specific error types before returning generic error
                ip = get_client_ip(request)
                email = request.data.get("email", "unknown")

                # Check for specific account status errors
                for field_errors in serializer.errors.values():
                    if isinstance(field_errors, list):
                        for error in field_errors:
                            # Handle ErrorDetail objects from ValidationError
                            if hasattr(error, "code"):
                                error_code = error.code
                                error_detail = str(error)
                            elif isinstance(error, dict):
                                error_code = error.get("code")
                                error_detail = error.get(
                                    "detail", "Authentication failed"
                                )
                            else:
                                continue

                            # Handle different account status errors
                            if error_code == "inactive_account":
                                logger.warning(
                                    f"Inactive account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "NOT_ACTIVATED",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "acount_inactive":
                                logger.warning(
                                    f"Inactive account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_DISABLED",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "account_inactive":
                                logger.warning(
                                    f"Account inactive MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_INACTIVE",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "account_pending":
                                logger.warning(
                                    f"Pending account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_PENDING",
                                        "action_required": "WAIT_FOR_APPROVAL",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "account_suspended":
                                logger.warning(
                                    f"Suspended account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_SUSPENDED",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "account_deleted":
                                logger.warning(
                                    f"Deleted account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_DELETED",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_410_GONE,
                                )
                            elif error_code == "account_banned":
                                logger.warning(
                                    f"Banned account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_BANNED",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "account_expired":
                                logger.warning(
                                    f"Expired account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_EXPIRED",
                                        "action_required": "RENEW_SUBSCRIPTION",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_402_PAYMENT_REQUIRED,
                                )
                            elif error_code == "account_unknown_status":
                                logger.warning(
                                    f"Unknown status account MFA login attempt for {email} from IP {ip}"
                                )
                                return Response(
                                    {
                                        "message": error_detail,
                                        "error_code": "ACCOUNT_UNKNOWN_STATUS",
                                        "support_email": "support@morevans.com",
                                    },
                                    status=status.HTTP_403_FORBIDDEN,
                                )
                            elif error_code == "user_not_found":
                                logger.warning(
                                    f"User not found for {email} from IP {ip}"
                                )
                                # Still return generic message for security
                                increment_failed_logins(email, ip)
                                return Response(
                                    {
                                        "message": "Invalid credentials provided.",
                                        "error_code": "INVALID_CREDENTIALS",
                                    },
                                    status=status.HTTP_401_UNAUTHORIZED,
                                )

                # Log failed login attempt and return generic error for other validation failures
                logger.warning(f"Failed MFA login attempt for {email} from IP {ip}")
                increment_failed_logins(email, ip)
                return Response(
                    {
                        "message": "Invalid credentials provided.",
                        "error_code": "INVALID_CREDENTIALS",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user = serializer.validated_data["user"]

            # Check if account requires further verification
            if hasattr(user, "requires_verification") and user.requires_verification:
                result = send_otp_utility(user, "signup", user.email)

                return Response(
                    {
                        "message": "Account requires verification. Please check your email.",
                        "error_code": "EMAIL_VERIFICATION_REQUIRED",
                        "action_required": "VERIFY_EMAIL",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if account is locked due to too many failed attempts
            if is_account_locked(user.email):
                return Response(
                    {
                        "message": "Account temporarily locked due to too many failed attempts. Try again later or reset your password.",
                        "error_code": "ACCOUNT_LOCKED",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Reset failed login attempts since first factor passed
            reset_failed_logins(user.email)

            # Trusted device fast-path: if device is recognized and valid, skip OTP
            try:
                import hashlib, os

                device_id = request.data.get("device_id")
                device_name = request.data.get("device_name")
                device_fp = request.data.get("fingerprint") or request.data.get(
                    "device_fingerprint"
                )
                device_info = request.data.get("device_info")

                if device_id and device_fp:
                    salt = os.getenv("DEVICE_FINGERPRINT_SALT", "")
                    fp_hash = hashlib.sha256(
                        (salt + (device_fp or "")).encode()
                    ).hexdigest()
                    print("the fp hash", fp_hash)
                    td = TrustedDevice.objects.filter(
                        user=user, device_id=device_id, is_active=True
                    ).first()
                    print("the td", td)
                    now = timezone.now()
                    if (
                        td
                        and td.expires_at
                        and td.expires_at > now
                        and td.device_fingerprint_hash == fp_hash
                    ):
                        # Issue tokens directly
                        refresh = RefreshToken.for_user(user)
                        access = str(refresh.access_token)

                        # Bind refresh to device by storing hash
                        td.refresh_token_hash = hashlib.sha256(
                            str(refresh).encode()
                        ).hexdigest()
                        td.last_used = now
                        td.save(update_fields=["refresh_token_hash", "last_used"])

                        resp = Response(
                            {
                                "message": "Trusted device recognized. Login successful.",
                                "requires_otp": False,
                                "user": UserAuthSerializer(user).data,
                            }
                        )
                        resp["Authorization"] = f"Bearer {access}"
                        resp["X-Refresh-Token"] = str(refresh)
                        resp["Access-Control-Expose-Headers"] = (
                            "Authorization, X-Refresh-Token"
                        )
                        return resp
            except Exception:
                # Fall back to OTP flow silently if trust check fails
                pass

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
                # Handle different OTP send failure types with appropriate status codes
                if result.get("status_code") == 429:
                    return Response(
                        {
                            "message": result.get(
                                "message", "Rate limit exceeded for OTP requests."
                            ),
                            "error_code": result.get("error_code", "OTP_RATE_LIMIT"),
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                elif result.get("status_code") == 503:
                    return Response(
                        {
                            "message": result.get(
                                "message", "Email service temporarily unavailable."
                            ),
                            "error_code": result.get(
                                "error_code", "EMAIL_SERVICE_UNAVAILABLE"
                            ),
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                else:
                    return Response(
                        {
                            "message": result.get(
                                "message",
                                "Authentication successful but failed to send OTP. Please try again.",
                            ),
                            "error_code": result.get("error_code", "OTP_SEND_FAILED"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            logger.exception(f"MFA login error: {str(e)}")
            return Response(
                {
                    "message": "Authentication failed due to a server error. Please try again.",
                    "error_code": "INTERNAL_SERVER_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyMFALoginView(APIView):
    """MFA Login - Step 2: Verify OTP and complete login"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        print("the verify mfa login data", json.dumps(request.data, indent=4))
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

                # Optionally trust this device if requested
                try:
                    trust_device = bool(
                        request.data.get("trust_device")
                        or request.data.get("remember_device")
                    )
                    if trust_device:
                        import hashlib, os
                        from datetime import timedelta

                        device_id = request.data.get("device_id")
                        device_name = request.data.get("device_name")
                        device_fp = request.data.get("fingerprint") or request.data.get(
                            "device_fingerprint"
                        )
                        device_info = request.data.get("device_info")

                        if device_id and device_fp:
                            salt = os.getenv("DEVICE_FINGERPRINT_SALT", "")
                            fp_hash = hashlib.sha256(
                                (salt + (device_fp or "")).encode()
                            ).hexdigest()
                            now = timezone.now()
                            expires_at = now + timedelta(
                                days=int(os.getenv("DEVICE_TRUST_EXPIRY_DAYS", "30"))
                            )

                            new_trusted_device = TrustedDevice.objects.update_or_create(
                                user=user,
                                device_id=device_id,
                                defaults={
                                    "device_fingerprint_hash": fp_hash,
                                    "device_name": device_name,
                                    "device_info": device_info,
                                    "refresh_token_hash": hashlib.sha256(
                                        str(refresh).encode()
                                    ).hexdigest(),
                                    "last_used": now,
                                    "expires_at": expires_at,
                                    "is_active": True,
                                },
                            )
                            print("the new trusted device", new_trusted_device)
                            new_trusted_device.save()
                except Exception:
                    # Do not fail login if trust persistence fails
                    pass

                return response
            else:
                # Return appropriate error status based on error type
                error_code = result.get("error_code", "UNKNOWN_ERROR")

                if error_code == "INVALID_FORMAT":
                    status_code = status.HTTP_400_BAD_REQUEST
                elif error_code == "OTP_NOT_FOUND":
                    status_code = status.HTTP_404_NOT_FOUND
                elif error_code == "OTP_EXPIRED":
                    status_code = status.HTTP_410_GONE
                elif error_code == "INVALID_OTP":
                    status_code = status.HTTP_401_UNAUTHORIZED
                else:
                    status_code = status.HTTP_400_BAD_REQUEST

                return Response(
                    {
                        "message": result["message"],
                        "error_code": error_code,
                        "remaining_attempts": result.get("remaining_attempts"),
                    },
                    status=status_code,
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


class AdminSendOTPView(APIView):
    """Admin endpoint to send OTP with override capabilities"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {
                    "message": "Only staff members can perform admin OTP operations.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate required fields
        user_id = request.data.get("user_id")
        otp_type = request.data.get("otp_type")

        if not user_id or not otp_type:
            return Response(
                {
                    "message": "user_id and otp_type are required.",
                    "error_code": "MISSING_FIELDS",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get target user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        "message": "User not found.",
                        "error_code": "USER_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate OTP type
            valid_otp_types = [choice[0] for choice in OTP.OTP_TYPES]
            if otp_type not in valid_otp_types:
                return Response(
                    {
                        "message": f"Invalid OTP type. Valid types: {valid_otp_types}",
                        "error_code": "INVALID_OTP_TYPE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Send OTP with admin override
            result = send_otp_utility(
                user=user,
                otp_type=otp_type,
                admin_override=True,
                admin_user=request.user,
            )

            if result["success"]:
                return Response(
                    {
                        "message": result["message"],
                        "masked_email": result.get("masked_email"),
                        "validity_minutes": result.get("validity_minutes"),
                        "otp_type": otp_type,
                        "user_id": str(user.id),
                        "admin_override": True,
                        "admin_user_id": str(request.user.id),
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
            logger.error(f"Error in AdminSendOTPView: {str(e)}")
            return Response(
                {
                    "message": "Failed to send OTP. Please try again.",
                    "error_code": "SEND_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminVerifyOTPView(APIView):
    """Admin endpoint to verify OTP with override capabilities"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {
                    "message": "Only staff members can perform admin OTP operations.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate required fields
        user_id = request.data.get("user_id")
        otp_code = request.data.get("otp_code")
        otp_type = request.data.get("otp_type")

        if not user_id or not otp_code or not otp_type:
            return Response(
                {
                    "message": "user_id, otp_code, and otp_type are required.",
                    "error_code": "MISSING_FIELDS",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get target user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        "message": "User not found.",
                        "error_code": "USER_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate OTP type
            valid_otp_types = [choice[0] for choice in OTP.OTP_TYPES]
            if otp_type not in valid_otp_types:
                return Response(
                    {
                        "message": f"Invalid OTP type. Valid types: {valid_otp_types}",
                        "error_code": "INVALID_OTP_TYPE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify OTP with admin override
            result = verify_otp_utility(
                user=user,
                otp_code=otp_code,
                otp_type=otp_type,
                admin_override=True,
                admin_user=request.user,
            )

            if result["success"]:
                response_data = {
                    "message": result["message"],
                    "action": result.get("action"),
                    "user_id": str(user.id),
                    "admin_override": True,
                    "admin_user_id": str(request.user.id),
                }

                # Handle different OTP types
                if otp_type == "signup":
                    response_data["message"] = (
                        "Email verified successfully. User account is now active. (Admin Override)"
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
                        "admin_override": True,
                        "admin_user_id": str(request.user.id),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error in AdminVerifyOTPView: {str(e)}")
            return Response(
                {
                    "message": "Failed to verify OTP. Please try again.",
                    "error_code": "VERIFICATION_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminResetOTPLimitsView(APIView):
    """Admin endpoint to reset OTP rate limits for a user"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {
                    "message": "Only staff members can perform admin OTP operations.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate required fields
        user_id = request.data.get("user_id")
        otp_type = request.data.get(
            "otp_type"
        )  # Optional, if not provided, reset all types

        if not user_id:
            return Response(
                {
                    "message": "user_id is required.",
                    "error_code": "MISSING_FIELDS",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get target user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {
                        "message": "User not found.",
                        "error_code": "USER_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Reset rate limits
            reset_count = 0

            if otp_type:
                # Reset specific OTP type
                valid_otp_types = [choice[0] for choice in OTP.OTP_TYPES]
                if otp_type not in valid_otp_types:
                    return Response(
                        {
                            "message": f"Invalid OTP type. Valid types: {valid_otp_types}",
                            "error_code": "INVALID_OTP_TYPE",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Reset sending rate limit
                rate_limit_key = OTPValidator.get_rate_limit_key(user, otp_type)
                if cache.get(rate_limit_key):
                    cache.delete(rate_limit_key)
                    reset_count += 1

                # Reset cooldown
                cooldown_key = OTPValidator.get_resend_cooldown_key(user, otp_type)
                if cache.get(cooldown_key):
                    cache.delete(cooldown_key)
                    reset_count += 1

                # Reset hourly verification limit
                hourly_verification_key = OTPValidator.get_hourly_verification_key(
                    user, otp_type
                )
                if cache.get(hourly_verification_key):
                    cache.delete(hourly_verification_key)
                    reset_count += 1

                # Reset all OTP verification attempts for this type
                # This is a bit more complex as we need to find all OTPs for this user and type
                otps = OTP.objects.filter(user=user, otp_type=otp_type, is_used=False)
                for otp in otps:
                    otp_verification_key = OTPValidator.get_otp_verification_key(
                        user, otp_type, otp.id
                    )
                    if cache.get(otp_verification_key):
                        cache.delete(otp_verification_key)
                        reset_count += 1
            else:
                # Reset all OTP types
                valid_otp_types = [choice[0] for choice in OTP.OTP_TYPES]
                for otp_type in valid_otp_types:
                    # Reset sending rate limit
                    rate_limit_key = OTPValidator.get_rate_limit_key(user, otp_type)
                    if cache.get(rate_limit_key):
                        cache.delete(rate_limit_key)
                        reset_count += 1

                    # Reset cooldown
                    cooldown_key = OTPValidator.get_resend_cooldown_key(user, otp_type)
                    if cache.get(cooldown_key):
                        cache.delete(cooldown_key)
                        reset_count += 1

                    # Reset hourly verification limit
                    hourly_verification_key = OTPValidator.get_hourly_verification_key(
                        user, otp_type
                    )
                    if cache.get(hourly_verification_key):
                        cache.delete(hourly_verification_key)
                        reset_count += 1

                    # Reset all OTP verification attempts for this type
                    otps = OTP.objects.filter(
                        user=user, otp_type=otp_type, is_used=False
                    )
                    for otp in otps:
                        otp_verification_key = OTPValidator.get_otp_verification_key(
                            user, otp_type, otp.id
                        )
                        if cache.get(otp_verification_key):
                            cache.delete(otp_verification_key)
                            reset_count += 1

            # Log the admin action
            logger.info(
                f"Admin reset OTP limits: {request.user.email} reset {reset_count} rate limit entries for user {user.email} ({otp_type or 'all types'})"
            )

            return Response(
                {
                    "message": f"Successfully reset {reset_count} rate limit entries for user {user.email}",
                    "user_id": str(user.id),
                    "otp_type": otp_type or "all types",
                    "reset_count": reset_count,
                    "admin_user_id": str(request.user.id),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in AdminResetOTPLimitsView: {str(e)}")
            return Response(
                {
                    "message": "Failed to reset OTP limits. Please try again.",
                    "error_code": "RESET_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminEmailStatsView(APIView):
    """Admin endpoint to view global email sending statistics"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {
                    "message": "Only staff members can view email statistics.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Get email statistics
            stats = OTPValidator.get_global_email_stats()

            return Response(
                {
                    "message": "Email statistics retrieved successfully",
                    "stats": stats,
                    "admin_user_id": str(request.user.id),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in AdminEmailStatsView: {str(e)}")
            return Response(
                {
                    "message": "Failed to retrieve email statistics.",
                    "error_code": "STATS_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminResetGlobalEmailLimitView(APIView):
    """Admin endpoint to reset global email sending limit"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {
                    "message": "Only staff members can reset global email limits.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Get current stats before reset
            stats_before = OTPValidator.get_global_email_stats()

            # Reset global email limit
            OTPValidator.reset_global_email_limit()

            # Get stats after reset
            stats_after = OTPValidator.get_global_email_stats()

            # Log the admin action
            logger.info(
                f"Admin reset global email limit: {request.user.email} reset global email counter from {stats_before['current_count']} to {stats_after['current_count']}"
            )

            return Response(
                {
                    "message": f"Successfully reset global email limit. Previous count: {stats_before['current_count']}, New count: {stats_after['current_count']}",
                    "stats_before": stats_before,
                    "stats_after": stats_after,
                    "admin_user_id": str(request.user.id),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in AdminResetGlobalEmailLimitView: {str(e)}")
            return Response(
                {
                    "message": "Failed to reset global email limit.",
                    "error_code": "RESET_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminOTPDebugLogsView(APIView):
    """Admin endpoint to view recent OTP debug logs"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {
                    "message": "Only staff members can view debug logs.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Get query parameters
            user_id = request.query_params.get("user_id")
            otp_type = request.query_params.get("otp_type")
            limit = int(request.query_params.get("limit", 50))

            # This is a simplified log viewer - in production, you might want to use a proper log aggregation service
            # For now, we'll return a message about how to check logs
            debug_info = {
                "message": "Debug logs are written to the application log files",
                "log_patterns": {
                    "otp_send": "[OTP_DEBUG]",
                    "otp_verify": "[VERIFY_DEBUG]",
                    "otp_generation": "[OTP_GEN_DEBUG]",
                    "email_send": "[EMAIL_DEBUG]",
                    "admin_operations": "Admin override:",
                    "rate_limits": "rate limit",
                    "global_limits": "Global email limit",
                },
                "common_issues": {
                    "email_not_sent": "Check [EMAIL_DEBUG] logs for SMTP errors",
                    "otp_not_found": "Check [OTP_GEN_DEBUG] logs for OTP generation",
                    "rate_limit_issues": "Check [OTP_DEBUG] logs for rate limiting",
                    "verification_fails": "Check [VERIFY_DEBUG] logs for verification issues",
                },
                "log_locations": {
                    "development": "Console output or log files",
                    "production": "Application log files (e.g., /var/log/app/)",
                    "docker": "docker logs <container_name>",
                },
                "filters": {
                    "user_id": user_id,
                    "otp_type": otp_type,
                    "limit": limit,
                },
            }

            return Response(
                debug_info,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in AdminOTPDebugLogsView: {str(e)}")
            return Response(
                {
                    "message": "Failed to retrieve debug information.",
                    "error_code": "DEBUG_FAILED",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterProviderAPIView(APIView):
    """API endpoint for provider registration"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        """
        Register a new provider with user, provider profile, and addresses

        Expected data format:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "securepassword",
            "confirm_password": "securepassword",
            "username": "johndoe",
            "mobile_number": "1234567890",
            "phone_number": "1234567890",
            "business_name": "John's Transport",
            "business_type": "limited",
            "vat_registered": "yes",
            "number_of_vehicles": "2-5",
            "work_types": ["Home removals", "Parcel delivery"],
            "address_line_1": "123 Main St",
            "address_line_2": "Apt 4B",
            "city": "London",
            "postcode": "SW1A 1AA",
            "country": "United Kingdom",
            "has_separate_business_address": true,
            "business_address_line_1": "456 Business Ave",
            "business_city": "London",
            "business_postcode": "SW1A 2BB",
            "business_country": "United Kingdom",
            "has_non_uk_address": false,
            "accepted_privacy_policy": true
        }
        """
        print("request data", request.data)
        try:
            from apps.Provider.serializer import ProviderRegistrationSerializer

            serializer = ProviderRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                # Create user, provider, and addresses in transaction
                result = serializer.save()

                logger.info(
                    f"Provider registration successful: User ID {result['user'].id}, Provider ID {result['provider'].id}"
                )

                # Process work types after transaction (to avoid transaction issues)
                if result.get("work_types"):
                    try:
                        from apps.Provider.serializer import (
                            ProviderRegistrationSerializer,
                        )

                        ProviderRegistrationSerializer._process_work_types(
                            ProviderRegistrationSerializer(),
                            result["provider"],
                            result["work_types"],
                        )
                        logger.info(
                            f"Work types processed successfully for provider {result['provider'].id}"
                        )
                    except Exception as e:
                        logger.error(f"Error processing work types: {str(e)}")
                        # Don't fail the registration, just log the error

                # Force a fresh database query to ensure user is committed
                from apps.User.models import User
                from django.db import transaction

                # Use a new transaction to verify the user exists
                with transaction.atomic():
                    try:
                        user = User.objects.select_for_update().get(
                            id=result["user"].id
                        )
                        logger.info(f"User verified in database: {user.email}")
                    except User.DoesNotExist:
                        logger.error(
                            f"User not found in database after transaction: {result['user'].id}"
                        )
                        return Response(
                            {
                                "message": "Registration completed but user verification failed. Please contact support.",
                                "error": "User not found in database",
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                # Send OTP for email verification after transaction is committed
                try:
                    from .utils import send_otp_utility

                    # Double-check user exists before sending OTP
                    logger.info(f"About to send OTP for user: {user.id} ({user.email})")

                    # Force a database refresh
                    user.refresh_from_db()
                    logger.info(
                        f"User refreshed from database: {user.id} ({user.email})"
                    )

                    otp_result = send_otp_utility(user, "signup", user.email)

                    return Response(
                        {
                            "message": "Provider registration successful. Please check your email for verification.",
                            "user_id": user.id,
                            "provider_id": result["provider"].id,
                            "email": user.email,
                            "status": "pending_verification",
                        },
                        status=status.HTTP_201_CREATED,
                    )

                except Exception as e:
                    logger.error(
                        f"Error sending OTP after provider registration: {str(e)}"
                    )
                    # Registration succeeded but OTP failed - return success with warning
                    return Response(
                        {
                            "message": "Provider registration successful but verification email could not be sent. Please contact support.",
                            "user_id": user.id,
                            "provider_id": result["provider"].id,
                            "email": user.email,
                            "status": "registered_no_otp",
                            "warning": "Email verification not sent",
                            "otp_error": str(e),
                        },
                        status=status.HTTP_201_CREATED,
                    )
            else:
                return Response(
                    {
                        "message": "Registration failed. Please check the provided information.",
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Provider registration error: {str(e)}")

            # Import custom exceptions
            from apps.Provider.serializer import EmailAlreadyExistsException

            # Handle specific conflict exceptions
            if isinstance(e, EmailAlreadyExistsException):
                return Response(
                    {
                        "message": "Email address is already registered",
                        "error": "email_already_exists",
                        "detail": str(e.detail),
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                return Response(
                    {
                        "message": "An error occurred during registration. Please try again.",
                        "error": str(e),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
