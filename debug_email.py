#!/usr/bin/env python3
"""
Debug SendGrid email configuration and test connection
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


def debug_sendgrid_settings():
    """Debug SendGrid settings and test connection"""

    print("=== SENDGRID SETTINGS DEBUG ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(
        f"SENDGRID_API_KEY: {'*' * len(getattr(settings, 'SENDGRID_API_KEY', '')) if getattr(settings, 'SENDGRID_API_KEY', None) else 'None'}"
    )
    print(
        f"SENDGRID_SANDBOX_MODE_IN_DEBUG: {getattr(settings, 'SENDGRID_SANDBOX_MODE_IN_DEBUG', 'Not set')}"
    )
    print(
        f"SENDGRID_TRACK_CLICKS_PLAIN: {getattr(settings, 'SENDGRID_TRACK_CLICKS_PLAIN', 'Not set')}"
    )
    print(
        f"SENDGRID_TRACK_CLICKS_HTML: {getattr(settings, 'SENDGRID_TRACK_CLICKS_HTML', 'Not set')}"
    )
    print(
        f"SENDGRID_TRACK_OPENS: {getattr(settings, 'SENDGRID_TRACK_OPENS', 'Not set')}"
    )
    print("===============================")

    # Test email sending
    print("\n=== SENDGRID EMAIL TEST ===")
    try:
        # Test sending an email
        result = send_mail(
            subject="SendGrid Test Email",
            message="This is a test email sent through SendGrid API.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["ellisarmahayikwei@gmail.com"],
            fail_silently=False,
        )

        if result:
            print(f"✅ SendGrid email sent successfully! Result: {result}")
        else:
            print("❌ SendGrid email failed to send (result: 0)")

    except Exception as e:
        print(f"❌ SendGrid email error: {e}")
        print(f"Error type: {type(e).__name__}")

    # Environment variable recommendations
    print("\n=== RECOMMENDATIONS ===")
    if not getattr(settings, "SENDGRID_API_KEY", None):
        print("❌ SENDGRID_API_KEY not set")
        print("   Add to your .env file:")
        print("   SENDGRID_API_KEY=your_sendgrid_api_key_here")
    else:
        print("✅ SENDGRID_API_KEY is set")

    if getattr(settings, "SENDGRID_SANDBOX_MODE_IN_DEBUG", True):
        print("⚠️  Sandbox mode is enabled - emails won't be delivered")
        print(
            "   Set SENDGRID_SANDBOX_MODE_IN_DEBUG = False in settings.py for production"
        )
    else:
        print("✅ Sandbox mode is disabled - emails will be delivered")


if __name__ == "__main__":
    debug_sendgrid_settings()
