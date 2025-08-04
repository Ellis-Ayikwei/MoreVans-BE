#!/usr/bin/env python3
"""
Check environment variables and SendGrid settings
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


def check_environment():
    """Check environment variables and settings for SendGrid"""

    print("=== SendGrid Environment Variables ===")
    sendgrid_vars = [
        "SENDGRID_API_KEY",
        "DEFAULT_FROM_EMAIL",
    ]

    for var in sendgrid_vars:
        value = os.getenv(var)
        if var == "SENDGRID_API_KEY" and value:
            print(f"{var}: {'*' * len(value)}")
        else:
            print(f"{var}: {value}")

    print("\n=== Django SendGrid Settings ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(
        f"SENDGRID_API_KEY: {'*' * len(getattr(settings, 'SENDGRID_API_KEY', '')) if getattr(settings, 'SENDGRID_API_KEY', None) else 'None'}"
    )
    print(
        f"SENDGRID_SANDBOX_MODE_IN_DEBUG: {getattr(settings, 'SENDGRID_SANDBOX_MODE_IN_DEBUG', 'Not set')}"
    )

    print("\n=== Recommendations ===")
    if not os.getenv("SENDGRID_API_KEY"):
        print("❌ SENDGRID_API_KEY not set")
        print("   Create a .env file with:")
        print("   SENDGRID_API_KEY=your_sendgrid_api_key_here")
        print("   DEFAULT_FROM_EMAIL=noreply@morevans.com")
    else:
        print("✅ SENDGRID_API_KEY is set")

    if not os.getenv("DEFAULT_FROM_EMAIL"):
        print("❌ DEFAULT_FROM_EMAIL not set")
        print("   Add to your .env file:")
        print("   DEFAULT_FROM_EMAIL=noreply@morevans.com")
    else:
        print("✅ DEFAULT_FROM_EMAIL is set")

    # Check for conflicting SMTP variables
    smtp_vars = ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD"]
    smtp_found = any(os.getenv(var) for var in smtp_vars)

    if smtp_found:
        print("\n⚠️  WARNING: SMTP environment variables detected!")
        print("   These might conflict with SendGrid configuration:")
        for var in smtp_vars:
            if os.getenv(var):
                print(f"   - {var}")
        print("   Consider removing these from your .env file")


if __name__ == "__main__":
    check_environment()
