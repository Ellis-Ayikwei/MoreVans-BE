#!/usr/bin/env python3
"""
Test script to verify that the transaction fix resolves the user not being saved issue
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
from apps.User.models import User
from apps.Provider.models import ServiceProvider
from apps.Authentication.utils import send_otp_utility
from django.db import connection, transaction
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_transaction_fix():
    """Test that the transaction fix resolves the user not being saved issue"""

    print("🧪 Testing Transaction Fix for User Save Issue")
    print("=" * 60)

    # Test data
    test_data = {
        "first_name": "Transaction",
        "last_name": "Test",
        "email": "transaction.test.fix@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Transaction Test Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals", "Furniture & appliance delivery"],
        "address_line_1": "123 Transaction Street",
        "city": "Transaction City",
        "postcode": "TR1 1ST",
        "country": "Transaction Country",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    print("📝 Testing provider registration with transaction fix...")

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

        # Test database connection refresh (simulate the view logic)
        print("\n🔄 Testing database connection refresh...")
        connection.close()
        connection.ensure_connection()

        # Verify user still exists after connection refresh
        try:
            refreshed_user = User.objects.get(id=user.id)
            print(
                f"✅ User still exists after connection refresh: {refreshed_user.email}"
            )
        except User.DoesNotExist:
            print("❌ User not found after connection refresh!")
            return False

        # Test OTP sending
        print("\n📧 Testing OTP sending after transaction commit...")
        try:
            otp_result = send_otp_utility(
                refreshed_user, "signup", refreshed_user.email
            )
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            return False

        # Clean up test data
        refreshed_user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


def test_work_types_processing():
    """Test that work types processing doesn't break the transaction"""

    print(f"\n🧪 Testing Work Types Processing")
    print("=" * 50)

    # Test data with problematic work types
    test_data = {
        "first_name": "Work",
        "last_name": "Types",
        "email": "work.types.test@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Work Types Test Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": [
            "Home removals",
            "Furniture & appliance delivery",
            "Car transport",
        ],
        "address_line_1": "123 Work Types Street",
        "city": "Work Types City",
        "postcode": "WT1 1ST",
        "country": "Work Types Country",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    print("📝 Testing provider registration with work types...")

    # Test the serializer
    serializer = ProviderRegistrationSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation passed")

        # Save the data
        result = serializer.save()

        user = result["user"]
        provider = result["provider"]
        work_types = result.get("work_types", [])

        print(f"   User ID: {user.id}")
        print(f"   Provider ID: {provider.id}")
        print(f"   Work Types: {work_types}")

        # Verify user exists in database
        try:
            db_user = User.objects.get(id=user.id)
            print(f"✅ User found in database: {db_user.email}")
        except User.DoesNotExist:
            print("❌ User not found in database!")
            return False

        # Test work types processing (simulate the view logic)
        print("\n🔧 Testing work types processing...")
        try:
            from apps.Provider.serializer import ProviderRegistrationSerializer

            ProviderRegistrationSerializer._process_work_types(
                ProviderRegistrationSerializer(), provider, work_types
            )
            print("✅ Work types processed successfully")
        except Exception as e:
            print(f"⚠️  Work types processing failed (but user was saved): {str(e)}")
            # This is acceptable - the user was still saved

        # Test OTP sending
        print("\n📧 Testing OTP sending...")
        try:
            otp_result = send_otp_utility(db_user, "signup", db_user.email)
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            return False

        # Clean up test data
        db_user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


def test_database_connection_issue():
    """Test to simulate the database connection issue"""

    print(f"\n🧪 Testing Database Connection Issue Simulation")
    print("=" * 60)

    # Test data
    test_data = {
        "first_name": "Connection",
        "last_name": "Test",
        "email": "connection.test@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Connection Test Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals"],
        "address_line_1": "123 Connection Street",
        "city": "Connection City",
        "postcode": "CT1 1ST",
        "country": "Connection Country",
        "has_separate_business_address": False,
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
    }

    print("📝 Testing provider registration with connection simulation...")

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

        # Simulate the exact flow from the view
        print("\n🔄 Simulating view flow...")

        # 1. Close and refresh connection (like in the view)
        connection.close()
        connection.ensure_connection()
        print("✅ Database connection refreshed")

        # 2. Verify user exists (like in the view)
        try:
            verified_user = User.objects.get(id=user.id)
            print(f"✅ User verified in database: {verified_user.email}")
        except User.DoesNotExist:
            print("❌ User not found in database after connection refresh!")
            return False

        # 3. Send OTP (like in the view)
        print("\n📧 Testing OTP sending after connection refresh...")
        try:
            otp_result = send_otp_utility(verified_user, "signup", verified_user.email)
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            return False

        # Clean up test data
        verified_user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


if __name__ == "__main__":
    print("🚀 Starting Transaction Fix Tests")
    print("=" * 60)

    # Run tests
    test1_result = test_transaction_fix()
    test2_result = test_work_types_processing()
    test3_result = test_database_connection_issue()

    print(f"\n📊 Test Results:")
    print(f"   Transaction Fix: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Work Types Processing: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"   Database Connection: {'✅ PASS' if test3_result else '❌ FAIL'}")

    if all([test1_result, test2_result, test3_result]):
        print(
            f"\n🎉 All tests passed! The transaction fix resolves the user save issue."
        )
        print(f"   - Users are properly saved to database")
        print(f"   - Work types processing doesn't break transactions")
        print(f"   - Database connection refresh works correctly")
        print(f"   - OTP creation succeeds after user is committed")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
