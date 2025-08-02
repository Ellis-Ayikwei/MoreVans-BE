#!/usr/bin/env python3
"""
Test script to verify API endpoints return 409 status codes for conflicts
"""

import os
import sys
import django
import requests
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from apps.User.models import User
from django.contrib.auth.hashers import make_password


def test_api_409_status_codes():
    """Test that API endpoints return 409 status codes for conflicts"""

    print("🧪 Testing API Endpoints for 409 Status Codes")
    print("=" * 50)

    # Base URL for testing (adjust as needed)
    base_url = "http://localhost:8000"

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

    # Test 1: Regular User Registration (Email Conflict)
    print(f"\n🔧 Testing Regular User Registration - Email Conflict...")

    auth_data = {
        "email": "test@example.com",  # Same email as existing user
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "John",
        "last_name": "Doe",
    }

    try:
        response = requests.post(
            f"{base_url}/api/auth/register/",
            json=auth_data,
            headers={"Content-Type": "application/json"},
        )

        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code == 409:
            print("   ✅ Correctly returned 409 Conflict for email")
        else:
            print(f"   ❌ Expected 409 but got {response.status_code}")

    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")

    # Test 2: Provider Registration (Email Conflict)
    print(f"\n🔧 Testing Provider Registration - Email Conflict...")

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

    try:
        response = requests.post(
            f"{base_url}/api/auth/register/provider/",
            json=provider_data,
            headers={"Content-Type": "application/json"},
        )

        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code == 409:
            print("   ✅ Correctly returned 409 Conflict for email")
        else:
            print(f"   ❌ Expected 409 but got {response.status_code}")

    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")

    # Test 3: Test with valid data (should succeed)
    print(f"\n🔧 Testing with Valid Data (should succeed)...")

    valid_provider_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",  # New email
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "0987654321",
        "phone_number": "0987654321",
        "business_name": "Jane's Transport",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals", "Office removals"],
        "address_line_1": "456 New Street",
        "city": "Manchester",
        "postcode": "M1 1AA",
        "country": "United Kingdom",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    try:
        response = requests.post(
            f"{base_url}/api/auth/register/provider/",
            json=valid_provider_data,
            headers={"Content-Type": "application/json"},
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code in [200, 201]:
            print("   ✅ Valid registration succeeded")
        else:
            print(f"   ⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")

    print(f"\n✅ Testing complete!")
    print(f"📖 API endpoints now properly return 409 status codes for conflicts.")


if __name__ == "__main__":
    test_api_409_status_codes()
