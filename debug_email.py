#!/usr/bin/env python3
"""
Debug email configuration and test SMTP connection
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.conf import settings
from django.core.mail import send_mail
import smtplib


def debug_email_settings():
    """Debug email settings and test connection"""

    print("=== EMAIL SETTINGS DEBUG ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(
        f"EMAIL_HOST_PASSWORD: {'*' * len(getattr(settings, 'EMAIL_HOST_PASSWORD', '')) if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'None'}"
    )
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
    print("============================")

    # Test SMTP connection
    print("\n=== SMTP CONNECTION TEST ===")
    try:
        smtp_server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        print(
            f"✅ SMTP Connection created: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}"
        )

        if settings.EMAIL_USE_TLS:
            print("🔄 Starting TLS...")
            smtp_server.starttls()
            print("✅ TLS started successfully")

        print(f"🔐 Attempting login with: {settings.EMAIL_HOST_USER}")
        smtp_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✅ SMTP Login successful!")

        # Test sending a simple email
        print("📧 Testing email send...")
        msg = f"Subject: Test Email\n\nThis is a test email from Django."
        smtp_server.sendmail(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_USER, msg)
        print("✅ Test email sent successfully!")

        smtp_server.quit()
        print("✅ SMTP connection closed")

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("This usually means the app password is incorrect or expired.")
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print(
            "This could be due to network/firewall issues or Gmail blocking the connection."
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")

    # Test Django's send_mail
    print("\n=== DJANGO SEND_MAIL TEST ===")
    try:
        send_mail(
            "Django Test Email",
            "This is a test email from Django send_mail function.",
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Send to self for testing
            fail_silently=False,
        )
        print("✅ Django send_mail test successful!")
    except Exception as e:
        print(f"❌ Django send_mail failed: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    debug_email_settings()
