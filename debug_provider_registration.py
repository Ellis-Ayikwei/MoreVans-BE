#!/usr/bin/env python3
"""
Debug script to identify the exact issue with provider registration
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


def debug_provider_registration():
    """Debug the exact issue with provider registration"""

    print("🔍 Debugging Provider Registration Issue")
    print("=" * 60)

    # Test data (same as your frontend)
    test_data = {
        "first_name": "Ellis",
        "last_name": "Ayikwei",
        "business_name": "Tradehut",
        "business_type": "limited",
        "postcode": "SW1 AAA",
        "selected_address": "London SW1, UK",
        "address_line_1": "London SW1",
        "address_line_2": "asdfs",
        "city": "Greater London",
        "country": "England",
        "has_non_uk_address": False,
        "has_separate_business_address": False,
        "non_uk_address_line_1": "",
        "non_uk_address_line_2": "",
        "non_uk_city": "",
        "non_uk_postal_code": "",
        "non_uk_country": "",
        "business_address_line_1": "",
        "business_address_line_2": "",
        "business_city": "",
        "business_postcode": "",
        "business_country": "",
        "email": "ellisarmahayikwei.debug@example.com",
        "password": "Toshib12345",
        "confirm_password": "Toshib12345",
        "mobile_number": "0248138722",
        "phone_number": "0248138722",
        "accepted_privacy_policy": True,
        "number_of_vehicles": "1",
        "work_types": [
            "Home removals",
            "Furniture & appliance delivery",
            "Gumtree delivery",
            "Car transport",
        ],
        "vat_registered": "yes",
        "account_type": "provider",
    }

    print("📝 Step 1: Testing serializer validation...")

    # Test the serializer
    serializer = ProviderRegistrationSerializer(data=test_data)

    if not serializer.is_valid():
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False

    print("✅ Serializer validation passed")

    print("\n📝 Step 2: Testing serializer save (transaction)...")

    # Save the data
    try:
        result = serializer.save()
        print("✅ Serializer save completed")

        user = result["user"]
        provider = result["provider"]

        print(f"   User ID: {user.id}")
        print(f"   Provider ID: {provider.id}")
        print(f"   User Email: {user.email}")

    except Exception as e:
        print(f"❌ Serializer save failed: {str(e)}")
        return False

    print("\n📝 Step 3: Verifying user exists immediately after save...")

    # Verify user exists in database immediately after save
    try:
        db_user = User.objects.get(id=user.id)
        print(f"✅ User found in database immediately after save: {db_user.email}")
    except User.DoesNotExist:
        print("❌ User not found in database immediately after save!")
        return False

    print("\n📝 Step 4: Testing database connection refresh...")

    # Test database connection refresh (like in the view)
    try:
        connection.close()
        connection.ensure_connection()
        print("✅ Database connection refreshed")
    except Exception as e:
        print(f"❌ Database connection refresh failed: {str(e)}")
        return False

    print("\n📝 Step 5: Verifying user exists after connection refresh...")

    # Verify user exists after connection refresh
    try:
        refreshed_user = User.objects.get(id=user.id)
        print(f"✅ User found after connection refresh: {refreshed_user.email}")
    except User.DoesNotExist:
        print("❌ User not found after connection refresh!")
        return False

    print("\n📝 Step 6: Testing transaction verification...")

    # Test the transaction verification (like in the updated view)
    try:
        with transaction.atomic():
            verified_user = User.objects.select_for_update().get(id=user.id)
            print(f"✅ User verified in transaction: {verified_user.email}")
    except User.DoesNotExist:
        print("❌ User not found in transaction verification!")
        return False
    except Exception as e:
        print(f"❌ Transaction verification failed: {str(e)}")
        return False

    print("\n📝 Step 7: Testing user refresh from database...")

    # Test user refresh from database
    try:
        verified_user.refresh_from_db()
        print(f"✅ User refreshed from database: {verified_user.email}")
    except Exception as e:
        print(f"❌ User refresh failed: {str(e)}")
        return False

    print("\n📝 Step 8: Testing OTP sending...")

    # Test OTP sending
    try:
        print(f"About to send OTP for user: {verified_user.id} ({verified_user.email})")
        otp_result = send_otp_utility(verified_user, "signup", verified_user.email)
        print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
    except Exception as e:
        print(f"❌ OTP sending failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        return False

    print("\n📝 Step 9: Final verification...")

    # Final verification
    try:
        final_user = User.objects.get(id=user.id)
        print(f"✅ Final verification - User exists: {final_user.email}")
    except User.DoesNotExist:
        print("❌ Final verification failed - User not found!")
        return False

    # Clean up test data
    try:
        final_user.delete()
        print("🧹 Test data cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup failed: {str(e)}")

    return True


def debug_work_types_processing():
    """Debug work types processing specifically"""

    print(f"\n🔍 Debugging Work Types Processing")
    print("=" * 50)

    # Test data with problematic work types
    test_data = {
        "first_name": "Work",
        "last_name": "Types",
        "email": "work.types.debug@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "Work Types Debug Business",
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

        # Test work types processing
        print("\n🔧 Testing work types processing...")
        try:
            from apps.Provider.serializer import ProviderRegistrationSerializer

            ProviderRegistrationSerializer._process_work_types(
                ProviderRegistrationSerializer(), provider, work_types
            )
            print("✅ Work types processed successfully")
        except Exception as e:
            print(f"⚠️  Work types processing failed: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            # This is acceptable - the user was still saved

        # Test OTP sending
        print("\n📧 Testing OTP sending...")
        try:
            otp_result = send_otp_utility(db_user, "signup", db_user.email)
            print(f"✅ OTP sent successfully: {otp_result.get('success', False)}")
        except Exception as e:
            print(f"❌ OTP sending failed: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            return False

        # Clean up test data
        db_user.delete()
        print("🧹 Test data cleaned up")

        return True

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)
        return False


if __name__ == "__main__":
    print("🚀 Starting Provider Registration Debug")
    print("=" * 60)

    # Run debug tests
    test1_result = debug_provider_registration()
    test2_result = debug_work_types_processing()

    print(f"\n📊 Debug Results:")
    print(f"   Provider Registration: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Work Types Processing: {'✅ PASS' if test2_result else '❌ FAIL'}")

    if all([test1_result, test2_result]):
        print(f"\n🎉 All debug tests passed! The issue might be elsewhere.")
        print(f"   - Check if the issue is in the actual API call")
        print(f"   - Check if there are any middleware issues")
        print(f"   - Check if there are any database configuration issues")
    else:
        print(f"\n⚠️  Some debug tests failed. This helps identify the exact issue.")
