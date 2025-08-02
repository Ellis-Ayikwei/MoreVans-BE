#!/usr/bin/env python3
"""
Test script to verify that users are properly saved to the database before OTP is sent
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from apps.Provider.serializer import ProviderRegistrationSerializer
from apps.Authentication.serializer import RegisterSerializer
from apps.User.models import User
from apps.Provider.models import ServiceProvider
from apps.Authentication.utils import send_otp_utility
from django.db import transaction


def test_provider_registration_user_save():
    """Test that provider registration properly saves user to database"""

    print("🧪 Testing Provider Registration User Save")
    print("=" * 50)

    # Test data
    test_data = {
        "first_name": "Test",
        "last_name": "Provider",
        "email": "test.provider@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Test Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals"],
        "address_line_1": "123 Test Street",
        "city": "Test City",
        "postcode": "TE1 1ST",
        "country": "Test Country",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    print("📝 Testing provider registration...")

    # Test the serializer
    serializer = ProviderRegistrationSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation passed")

        # Save the data
        result = serializer.save()

        user = result["user"]
        provider = result["provider"]

        print(f"   User ID: {user.id}")
        print(f"   Provider ID: {provider.id}")
        print(f"   User Email: {user.email}")

        # Verify user exists in database
        try:
            db_user = User.objects.get(id=user.id)
            print(f"✅ User found in database: {db_user.email}")
        except User.DoesNotExist:
            print("❌ User not found in database!")
            return False

        # Verify provider exists in database
        try:
            db_provider = ServiceProvider.objects.get(id=provider.id)
            print(f"✅ Provider found in database: {db_provider.company_name}")
        except ServiceProvider.DoesNotExist:
            print("❌ Provider not found in database!")
            return False

        # Test OTP sending after user is saved
        print("\n📧 Testing OTP sending...")
        try:
            otp_result = send_otp_utility(user, "signup", user.email)
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            return False

        # Clean up test data
        user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


def test_regular_registration_user_save():
    """Test that regular user registration properly saves user to database"""

    print(f"\n🧪 Testing Regular User Registration User Save")
    print("=" * 50)

    # Test data
    test_data = {
        "email": "test.user@example.com",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
    }

    print("📝 Testing regular user registration...")

    # Test the serializer
    serializer = RegisterSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation passed")

        # Save the data
        user = serializer.save()

        print(f"   User ID: {user.id}")
        print(f"   User Email: {user.email}")

        # Verify user exists in database
        try:
            db_user = User.objects.get(id=user.id)
            print(f"✅ User found in database: {db_user.email}")
        except User.DoesNotExist:
            print("❌ User not found in database!")
            return False

        # Test OTP sending after user is saved
        print("\n📧 Testing OTP sending...")
        try:
            otp_result = send_otp_utility(user, "signup", user.email)
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            return False

        # Clean up test data
        user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


def test_transaction_commit():
    """Test that transactions are properly committed"""

    print(f"\n🧪 Testing Transaction Commit")
    print("=" * 50)

    # Test data
    test_data = {
        "first_name": "Transaction",
        "last_name": "Test",
        "email": "transaction.test@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Transaction Test Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals"],
        "address_line_1": "123 Transaction Street",
        "city": "Transaction City",
        "postcode": "TR1 1ST",
        "country": "Transaction Country",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    print("📝 Testing transaction commit...")

    # Test the serializer
    serializer = ProviderRegistrationSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation passed")

        # Save the data
        result = serializer.save()

        user = result["user"]
        provider = result["provider"]

        print(f"   User ID: {user.id}")
        print(f"   Provider ID: {provider.id}")

        # Verify user exists in database immediately after save
        try:
            db_user = User.objects.get(id=user.id)
            print(f"✅ User found in database immediately after save: {db_user.email}")
        except User.DoesNotExist:
            print("❌ User not found in database immediately after save!")
            return False

        # Verify provider exists in database immediately after save
        try:
            db_provider = ServiceProvider.objects.get(id=provider.id)
            print(
                f"✅ Provider found in database immediately after save: {db_provider.company_name}"
            )
        except ServiceProvider.DoesNotExist:
            print("❌ Provider not found in database immediately after save!")
            return False

        # Test OTP sending
        print("\n📧 Testing OTP sending after transaction commit...")
        try:
            otp_result = send_otp_utility(user, "signup", user.email)
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            return False

        # Clean up test data
        user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


if __name__ == "__main__":
    print("🚀 Starting User Save and OTP Tests")
    print("=" * 60)

    # Run tests
    test1_result = test_provider_registration_user_save()
    test2_result = test_regular_registration_user_save()
    test3_result = test_transaction_commit()

    print(f"\n📊 Test Results:")
    print(f"   Provider Registration: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Regular Registration: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"   Transaction Commit: {'✅ PASS' if test3_result else '❌ FAIL'}")

    if all([test1_result, test2_result, test3_result]):
        print(f"\n🎉 All tests passed! Users are properly saved before OTP sending.")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
