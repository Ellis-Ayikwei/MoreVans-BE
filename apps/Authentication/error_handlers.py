from rest_framework.response import Response
from rest_framework import status
from .utils import mask_email


def get_verification_required_response(user):
    """
    Generate a standardized response for when account verification is required
    """
    return Response(
        {
            "detail": "Account requires verification. Please check your email for verification code.",
            "error_code": "ACCOUNT_VERIFICATION_REQUIRED",
            "error_type": "verification_required",
            "message": "Your account needs to be verified before you can access this feature.",
            "action_required": "verify_email",
            "user_id": str(user.id),
            "email": mask_email(user.email) if user.email else None,
            "next_steps": [
                "Check your email for the verification code",
                "Enter the 6-digit code in the verification form",
                "If you don't see the email, check your spam folder",
                "You can request a new verification code if needed",
            ],
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def get_account_locked_response(email):
    """
    Generate a standardized response for when account is locked
    """
    return Response(
        {
            "detail": "Account temporarily locked due to too many failed attempts.",
            "error_code": "ACCOUNT_LOCKED",
            "error_type": "account_locked",
            "message": "Your account has been temporarily locked for security reasons.",
            "action_required": "wait_or_reset_password",
            "email": mask_email(email) if email else None,
            "next_steps": [
                "Wait 15 minutes before trying again",
                "Or reset your password using the forgot password option",
                "Contact support if the issue persists",
            ],
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def get_invalid_credentials_response():
    """
    Generate a standardized response for invalid credentials
    """
    return Response(
        {
            "detail": "Invalid email or password.",
            "error_code": "INVALID_CREDENTIALS",
            "error_type": "authentication_failed",
            "message": "The email or password you entered is incorrect.",
            "action_required": "check_credentials",
            "next_steps": [
                "Double-check your email address",
                "Ensure your password is correct",
                "Check if Caps Lock is on",
                "Try the forgot password option if needed",
            ],
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


def get_user_not_found_response(identifier_type="email"):
    """
    Generate a standardized response for when user is not found
    """
    return Response(
        {
            "detail": f"User not found with this {identifier_type}.",
            "error_code": "USER_NOT_FOUND",
            "error_type": "user_not_found",
            "message": f"No account exists with the provided {identifier_type}.",
            "action_required": "check_identifier",
            "next_steps": [
                f"Verify the {identifier_type} is correct",
                "Check for typos or extra spaces",
                "Consider creating a new account if you don't have one",
            ],
        },
        status=status.HTTP_404_NOT_FOUND,
    )
