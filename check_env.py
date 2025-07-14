#!/usr/bin/env python3
"""
Check environment variables and settings
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
    """Check environment variables and settings"""

    print("=== Environment Variables ===")
    email_vars = [
        "EMAIL_HOST_PASSWORD",
        "EMAIL_HOST_USER",
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_USE_TLS",
        "DEFAULT_FROM_EMAIL",
    ]

    for var in email_vars:
        value = os.getenv(var)
        if var == "EMAIL_HOST_PASSWORD" and value:
            print(f"{var}: {'*' * len(value)}")
        else:
            print(f"{var}: {value}")

    print("\n=== Django Settings ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(
        f"EMAIL_HOST_PASSWORD: {'*' * len(getattr(settings, 'EMAIL_HOST_PASSWORD', '')) if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'None'}"
    )
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")

    print("\n=== Recommendations ===")
    if not os.getenv("EMAIL_HOST_PASSWORD"):
        print("❌ EMAIL_HOST_PASSWORD not set")
        print("   Create a .env file with:")
        print("   EMAIL_HOST_PASSWORD=your_app_password_here")
    else:
        print("✅ EMAIL_HOST_PASSWORD is set")

    if not os.getenv("EMAIL_HOST_USER"):
        print("❌ EMAIL_HOST_USER not set")
        print("   Add to .env file:")
        print("   EMAIL_HOST_USER=ellisarmahayikwei@gmail.com")
    else:
        print("✅ EMAIL_HOST_USER is set")


if __name__ == "__main__":
    check_environment()
