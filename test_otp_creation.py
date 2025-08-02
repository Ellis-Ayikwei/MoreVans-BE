#!/usr/bin/env python3
"""
Simple test to check OTP creation with existing users
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from apps.User.models import User
from apps.Authentication.utils import send_otp_utility
from apps.Authentication.models import OTP
from django.db import connection, transaction
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_otp_creation_with_existing_user():
    """Test OTP creation with an existing user"""

    print("🧪 Testing OTP Creation with Existing User")
    print("=" * 50)

    # Create a test user first
    test_email = "otp.test@example.com"

    try:
        # Check if user already exists
        user = User.objects.get(email=test_email)
        print(f"✅ Using existing user: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        # Create a new user
        user = User.objects.create(
            email=test_email,
            first_name="OTP",
            last_name="Test",
            phone_number="1234567890",
            user_type="provider",
        )
        print(f"✅ Created new user: {user.email} (ID: {user.id})")

    # Verify user exists in database
    try:
        db_user = User.objects.get(id=user.id)
        print(f"✅ User verified in database: {db_user.email}")
    except User.DoesNotExist:
        print("❌ User not found in database!")
        return False

    # Test OTP creation directly
    print("\n📧 Testing OTP creation...")
    try:
        otp_result = send_otp_utility(user, "signup", user.email)
        print(f"✅ OTP created successfully: {otp_result.get('success', False)}")
        return True
    except Exception as e:
        print(f"❌ OTP creation failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


def test_otp_model_directly():
    """Test OTP model creation directly"""

    print(f"\n🧪 Testing OTP Model Creation Directly")
    print("=" * 50)

    # Create a test user
    test_email = "otp.model.test@example.com"

    try:
        user = User.objects.get(email=test_email)
        print(f"✅ Using existing user: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        user = User.objects.create(
            email=test_email,
            first_name="OTP",
            last_name="Model",
            phone_number="1234567890",
            user_type="provider",
        )
        print(f"✅ Created new user: {user.email} (ID: {user.id})")

    # Test OTP model creation directly
    print("\n📧 Testing OTP model creation directly...")
    try:
        otp = OTP.generate_otp(user, "signup")
        print(f"✅ OTP model created successfully: {otp.id}")
        return True
    except Exception as e:
        print(f"❌ OTP model creation failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


def test_database_connection():
    """Test database connection and transaction isolation"""

    print(f"\n🧪 Testing Database Connection")
    print("=" * 50)

    # Test basic database operations
    try:
        # Test simple query
        user_count = User.objects.count()
        print(f"✅ Database query successful: {user_count} users found")

        # Test transaction
        with transaction.atomic():
            test_user = User.objects.create(
                email="db.test@example.com",
                first_name="DB",
                last_name="Test",
                phone_number="1234567890",
                user_type="provider",
            )
            print(f"✅ Transaction successful: Created user {test_user.id}")

            # Test OTP creation within transaction
            try:
                otp = OTP.generate_otp(test_user, "signup")
                print(f"✅ OTP creation within transaction successful: {otp.id}")
            except Exception as e:
                print(f"❌ OTP creation within transaction failed: {str(e)}")
                return False

        # Clean up
        test_user.delete()
        print("✅ Cleanup successful")
        return True

    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Starting OTP Creation Tests")
    print("=" * 60)

    # Run tests
    test1_result = test_otp_creation_with_existing_user()
    test2_result = test_otp_model_directly()
    test3_result = test_database_connection()

    print(f"\n📊 Test Results:")
    print(
        f"   OTP Creation with Existing User: {'✅ PASS' if test1_result else '❌ FAIL'}"
    )
    print(f"   OTP Model Creation Directly: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"   Database Connection: {'✅ PASS' if test3_result else '❌ FAIL'}")

    if all([test1_result, test2_result, test3_result]):
        print(
            f"\n🎉 All OTP tests passed! The issue is likely in the provider registration flow."
        )
    else:
        print(
            f"\n⚠️  Some OTP tests failed. This indicates a database or OTP model issue."
        )
