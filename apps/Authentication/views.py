from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from apps.User.models import User
from apps.User.serializer import UserSerializer
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
)

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
            # Send verification email here
            return Response(
                {
                    "message": "User created successfully. Please check your email for verification."
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Explicitly skip authentication for login
    throttle_classes = [AnonRateThrottle]  # Add rate limiting

    def post(self, request):
        # Force request.user to be AnonymousUser to prevent any token authentication influence
        # request._authenticator = None

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
            user.save(update_fields=["last_login"])

            # Create refresh token for the user
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Create response with user data but no tokens in the body
            response = Response({"user": UserSerializer(user).data})

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


# Helper functions - implement these in a utils.py file
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def increment_failed_logins(email, ip):
    # Implement with your caching system (Redis, Memcached, etc.)
    # Example with Django's cache framework:
    cache_key = f"login_attempts:{email}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=3600)  # 1 hour

    # Also track by IP to prevent attacks across multiple accounts
    ip_key = f"login_attempts_ip:{ip}"
    ip_attempts = cache.get(ip_key, 0) + 1
    cache.set(ip_key, ip_attempts, timeout=3600)


def is_account_locked(email):
    # Check if too many failed attempts
    cache_key = f"login_attempts:{email}"
    attempts = cache.get(cache_key, 0)
    return attempts >= 5  # Lock after 5 failed attempts


def reset_failed_logins(email):
    cache_key = f"login_attempts:{email}"
    cache.delete(cache_key)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Get the authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Invalid authorization header."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract the token
        refresh_token = request.headers.get("X-Refresh-Token")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log user activity
            from apps.User.models import UserActivity

            ip = get_client_ip(request)
            UserActivity.objects.create(
                user=request.user, activity_type="logout", details={"ip": ip}
            )

            return Response(
                {"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )


class PasswordRecoveryAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import os

        serializer = PasswordRecoverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        email_sent = False

        if user:
            token_generator = PasswordResetTokenGenerator()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)

            reset_url = reverse(
                "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
            )
            absolute_url = request.build_absolute_uri(reset_url)
            # Get frontend URL from request origin
            request_scheme = request.scheme  # http or https
            request_host = request.get_host()  # domain:port
            frontend_base_url = os.getenv("FRONTEND_URL")
            frontend_url = f"{frontend_base_url}/reset-password/{uid}/{token}"
            absolute_url = frontend_url
            try:
                send_mail(
                    "Password Reset Request",
                    f"Use this link to reset your password: {absolute_url}",
                    getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
                    [user.email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as e:
                # Log the error but don't expose it to the user
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Email Error in password reset: {str(e)}")
                email_sent = False

        if email_sent:
            return Response(
                {"detail": "Password reset link sent successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "detail": "Password reset link could not be sent. Please try again later."
                },
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
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        token_generator = PasswordResetTokenGenerator()
        if user and token_generator.check_token(
            user, serializer.validated_data["token"]
        ):
            user.set_password(serializer.validated_data["password"])
            user.save()
            return Response({"detail": "Password reset successfully"})

        return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


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
        """
        Handles the POST request to change the current user's password.
        """
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if the old password is correct
        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Wrong password"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update the user's password
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()

        # Return a success response
        return Response({"detail": "Password updated successfully"})


class TokenRefreshView(APIView):
    """
    Takes a refresh token and returns an access token if the refresh token is valid.
    This view expects the refresh token to be in an HTTP-only cookie.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Detailed header logging
        print("=== HEADERS RECEIVED IN TOKEN REFRESH ===")
        for header_name, header_value in request.headers.items():
            # Don't print actual token values for security
            if header_name.lower() in ["authorization", "x-refresh-token"]:
                print(f"{header_name}: {'PRESENT' if header_value else 'MISSING'}")
            else:
                print(f"{header_name}: {header_value}")
        print("======================================")

        # Check multiple possible sources for the refresh token
        refresh_token = None

        # 1. Check headers with detailed logging
        refresh_token = request.headers.get("X-Refresh-Token")
        print(f"X-Refresh-Token header: {refresh_token}")

        # 2. Try to get from request data
        if not refresh_token and request.data:
            print(f"Request data: {request.data}")
            if isinstance(request.data, dict) and "refresh_token" in request.data:
                refresh_token = request.data.get("refresh_token")
                print(f"refresh_token from request data: {refresh_token}")

        # 3. Try to get from cookies
        if not refresh_token:
            print(f"Cookies: {request.COOKIES}")
            refresh_token = request.COOKIES.get("_auth_refresh")
            print(f"_auth_refresh cookie: {refresh_token}")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found in headers, data, or cookies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Validate the refresh token
            refresh = RefreshToken(refresh_token)

            # Get user from token payload
            user_id = refresh.payload.get("user_id")

            try:
                user = User.objects.get(id=user_id)

                # Check if user is still active
                if not user.is_active:
                    raise AuthenticationFailed("User is inactive")

                # Generate new access token
                access_token = str(refresh.access_token)

                # Return empty response with token in header
                response = Response(status=status.HTTP_200_OK)

                # Add token to response header
                response["Authorization"] = f"Bearer {access_token}"

                # Set Access-Control-Expose-Headers
                response["Access-Control-Expose-Headers"] = "Authorization"

                return response

            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_401_UNAUTHORIZED
                )

        except TokenError as e:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except Exception as e:
            logger.exception(f"Token refresh error: {str(e)}")
            return Response(
                {"detail": "An error occurred while refreshing token."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TokenVerifyView(APIView):
    """
    Takes a token and returns a success response if it is valid.
    This allows clients to validate both access and refresh tokens.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Try to parse as access token first
            try:
                AccessToken(token)
                return Response({"status": "valid"})
            except TokenError:
                # If it's not an access token, try as refresh token
                RefreshToken(token)
                return Response({"status": "valid"})

        except TokenError as e:
            return Response(
                {"detail": "Token is invalid or expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except Exception as e:
            logger.exception(f"Token verification error: {str(e)}")
            return Response(
                {"detail": "An error occurred during token verification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
