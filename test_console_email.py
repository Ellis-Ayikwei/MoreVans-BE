#!/usr/bin/env python3
"""
Test console email backend
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

from django.core.mail import send_mail
from django.conf import settings


def test_console_email():
    """Test console email backend"""

    print("=== Testing Console Email Backend ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")

    try:
        send_mail(
            "Test Email",
            "This is a test email from console backend.",
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            ["test@example.com"],
            fail_silently=False,
        )
        print("✅ Console email test successful!")
        print("You should see the email content printed above.")

    except Exception as e:
        print(f"❌ Console email test failed: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_console_email()
