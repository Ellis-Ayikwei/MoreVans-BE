#!/usr/bin/env python3
"""
Test custom email backend
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


def test_custom_backend():
    """Test the custom email backend"""

    print("=== Testing Custom Email Backend ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(
        f"EMAIL_HOST_PASSWORD: {'*' * len(getattr(settings, 'EMAIL_HOST_PASSWORD', '')) if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'None'}"
    )

    try:
        send_mail(
            "Custom Backend Test",
            "This is a test email from the custom SSL backend.",
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            ["ellisarmahayikwei@gmail.com"],
            fail_silently=False,
        )
        print("✅ Custom backend test successful!")

    except Exception as e:
        print(f"❌ Custom backend test failed: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_custom_backend()
