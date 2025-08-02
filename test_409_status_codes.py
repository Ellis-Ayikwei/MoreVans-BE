#!/usr/bin/env python3
"""
Test script to verify 409 status codes for email and phone number conflicts
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from apps.Provider.serializer import (
    ProviderRegistrationSerializer,
    EmailAlreadyExistsException,
)
from apps.Authentication.serializer import (
    RegisterSerializer,
    EmailAlreadyExistsException as AuthEmailAlreadyExistsException,
    PhoneNumberAlreadyExistsException,
)
from apps.User.models import User
from django.contrib.auth.hashers import make_password


def test_409_status_codes():
    """Test that email and phone number conflicts return 409 status codes"""

    print("🧪 Testing 409 Status Codes for Conflicts")
    print("=" * 50)

    # Create a test user first
    test_user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "1234567890",
    }

    # Create user if it doesn't exist
    user, created = User.objects.get_or_create(
        email=test_user_data["email"],
        defaults={
            "password": make_password(test_user_data["password"]),
            "first_name": test_user_data["first_name"],
            "last_name": test_user_data["last_name"],
            "phone_number": test_user_data["phone_number"],
        },
    )

    if created:
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"ℹ️  Test user already exists: {user.email}")

    # Test Provider Registration Serializer
    print(f"\n🔧 Testing Provider Registration Serializer...")

    provider_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "test@example.com",  # Same email as existing user
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Test Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals", "Office removals"],
        "address_line_1": "123 Test Street",
        "city": "London",
        "postcode": "SW1A 1AA",
        "country": "United Kingdom",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    serializer = ProviderRegistrationSerializer(data=provider_data)

    try:
        serializer.is_valid(raise_exception=True)
        print("❌ Expected validation error but got success")
    except EmailAlreadyExistsException as e:
        print(
            f"✅ EmailAlreadyExistsException caught with status code: {e.status_code}"
        )
        print(f"   Detail: {e.detail}")
        print(f"   Code: {e.default_code}")

    except Exception as e:
        print(f"❌ Unexpected exception: {type(e).__name__}: {str(e)}")

    # Test Authentication Register Serializer
    print(f"\n🔧 Testing Authentication Register Serializer...")

    auth_data = {
        "email": "test@example.com",  # Same email as existing user
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "John",
        "last_name": "Doe",
    }

    auth_serializer = RegisterSerializer(data=auth_data)

    try:
        auth_serializer.is_valid(raise_exception=True)
        print("❌ Expected validation error but got success")
    except AuthEmailAlreadyExistsException as e:
        print(
            f"✅ AuthEmailAlreadyExistsException caught with status code: {e.status_code}"
        )
        print(f"   Detail: {e.detail}")
        print(f"   Code: {e.default_code}")
    except Exception as e:
        print(f"❌ Unexpected exception: {type(e).__name__}: {str(e)}")

    # Test with different email but same phone number
    print(f"\n🔧 Testing Phone Number Conflict...")

    phone_data = {
        "email": "different@example.com",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "1234567890",  # Same phone number as existing user
    }

    phone_serializer = RegisterSerializer(data=phone_data)

    try:
        phone_serializer.is_valid(raise_exception=True)
        print("❌ Expected validation error but got success")
    except PhoneNumberAlreadyExistsException as e:
        print(
            f"✅ PhoneNumberAlreadyExistsException caught with status code: {e.status_code}"
        )
        print(f"   Detail: {e.detail}")
        print(f"   Code: {e.default_code}")
    except Exception as e:
        print(f"❌ Unexpected exception: {type(e).__name__}: {str(e)}")

    print(f"\n✅ Testing complete!")
    print(f"📖 Email and phone number conflicts now return 409 status codes.")


if __name__ == "__main__":
    test_409_status_codes()
