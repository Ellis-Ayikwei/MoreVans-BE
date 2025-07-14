#!/usr/bin/env python3
"""
SendGrid Email Setup - More reliable than Gmail SMTP
"""

# Install SendGrid: pip install sendgrid

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def setup_sendgrid():
    """Set up SendGrid for email sending"""

    # Get API key from environment or input
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        api_key = input("Enter your SendGrid API key: ")

    print("=== SendGrid Email Setup ===")
    print(f"API Key: {'*' * len(api_key) if api_key else 'None'}")

    try:
        # Create message
        message = Mail(
            from_email="ellisarmahayikwei@gmail.com",
            to_emails="ellisarmahayikwei@gmail.com",
            subject="SendGrid Test Email",
            html_content="<strong>This is a test email from SendGrid</strong>",
        )

        # Send email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)

        print(f"✅ SendGrid email sent successfully!")
        print(f"Status code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Body: {response.body}")

        return True

    except Exception as e:
        print(f"❌ SendGrid error: {e}")
        return False


def get_django_settings():
    """Get Django settings for SendGrid"""
    print("\n=== Django Settings for SendGrid ===")
    print("Add these to your settings.py:")
    print(
        """
# SendGrid Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your_sendgrid_api_key_here'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'ellisarmahayikwei@gmail.com'
"""
    )


if __name__ == "__main__":
    print("SendGrid Setup:")
    print("1. Sign up at https://sendgrid.com/ (free tier available)")
    print("2. Get your API key from SendGrid dashboard")
    print("3. Run this script to test")

    if setup_sendgrid():
        get_django_settings()
    else:
        print("Failed to set up SendGrid")
