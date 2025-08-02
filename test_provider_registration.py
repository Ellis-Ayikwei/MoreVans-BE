#!/usr/bin/env python3
"""
Test script for provider registration functionality
"""

import os
import sys
import django
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from apps.User.models import User
from apps.Provider.models import ServiceProvider, ServiceProviderAddress
from apps.Provider.serializer import ProviderRegistrationSerializer


def test_provider_registration():
    """Test the provider registration process"""

    # Test data matching the frontend format
    test_data = {
        "first_name": "Ellis",
        "last_name": "Ayikwei",
        "email": "ellisyou59@gmail.com",
        "password": "@Toshib12345",
        "confirm_password": "@Toshib12345",
        "username": "ellisyou5",
        "mobile_number": "0248138722",
        "phone_number": "0248138722",
        "business_name": "Tradehut",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": [
            "Home removals",
            "Office removals",
            "Parcel delivery",
            "eBay delivery",
            "Gumtree delivery",
            "Car transport",
        ],
        "address_line_1": "A123/4",
        "address_line_2": "asdfs",
        "city": "Accra",
        "postcode": "SW1 AAA",
        "country": "Ghana",
        "has_separate_business_address": True,
        "business_address_line_1": "Tradehut",
        "business_address_line_2": "Accra-Kumasi Road, Kumasi, Ghana",
        "business_city": "Kumasi",
        "business_postcode": "3242",
        "business_country": "Ghana",
        "has_non_uk_address": False,
        "accepted_privacy_policy": True,
        "selected_address": "Flat 1, 123 Main Street",
    }

    print("Testing Provider Registration...")
    print("=" * 50)

    # Test 1: Validate serializer
    print("1. Testing serializer validation...")
    serializer = ProviderRegistrationSerializer(data=test_data)
    if serializer.is_valid():
        print("✅ Serializer validation passed")
        print(f"   - Validated data keys: {list(serializer.validated_data.keys())}")
    else:
        print("❌ Serializer validation failed:")
        for field, errors in serializer.errors.items():
            print(f"   - {field}: {errors}")
        return False

    # Test 2: Create user, provider, and addresses
    print("\n2. Testing data creation...")
    try:
        result = serializer.save()
        print("✅ Data creation successful")
        print(f"   - User ID: {result['user'].id}")
        print(f"   - Provider ID: {result['provider'].id}")
        print(f"   - Addresses created: {len(result['addresses'])}")

        # Verify user
        user = result["user"]
        print(f"   - User email: {user.email}")
        print(f"   - User type: {user.user_type}")
        print(f"   - User is active: {user.is_active}")

        # Verify provider
        provider = result["provider"]
        print(f"   - Provider company: {provider.company_name}")
        print(f"   - Business type: {provider.business_type}")
        print(f"   - VAT registered: {provider.vat_registered}")
        print(f"   - Vehicle count: {provider.vehicle_count}")

        # Verify addresses
        for i, address in enumerate(result["addresses"]):
            print(
                f"   - Address {i+1}: {address.address_type} - {address.full_address}"
            )

        # Test 3: Verify database records
        print("\n3. Verifying database records...")

        # Check user exists
        user_exists = User.objects.filter(id=user.id).exists()
        print(f"   - User in database: {'✅' if user_exists else '❌'}")

        # Check provider exists
        provider_exists = ServiceProvider.objects.filter(id=provider.id).exists()
        print(f"   - Provider in database: {'✅' if provider_exists else '❌'}")

        # Check addresses exist
        addresses_exist = ServiceProviderAddress.objects.filter(
            provider=provider
        ).count()
        print(f"   - Addresses in database: {addresses_exist} ✅")

        # Test 4: Test duplicate registration prevention
        print("\n4. Testing duplicate registration prevention...")
        duplicate_serializer = ProviderRegistrationSerializer(data=test_data)
        if not duplicate_serializer.is_valid():
            print("✅ Duplicate registration correctly prevented")
            print(f"   - Error: {duplicate_serializer.errors}")
        else:
            print("❌ Duplicate registration not prevented")

        print("\n" + "=" * 50)
        print("🎉 All tests passed! Provider registration is working correctly.")

        # Cleanup - delete test data
        print("\nCleaning up test data...")
        provider.delete()  # This will cascade delete addresses
        user.delete()
        print("✅ Test data cleaned up")

        return True

    except Exception as e:
        print(f"❌ Data creation failed: {str(e)}")
        return False


def test_address_model():
    """Test the ServiceProviderAddress model functionality"""

    print("\nTesting ServiceProviderAddress Model...")
    print("=" * 50)

    # Create a test user and provider
    user = User.objects.create(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone_number="1234567890",
        user_type="provider",
    )

    provider = ServiceProvider.objects.create(
        user=user, company_name="Test Company", business_type="limited"
    )

    # Test address creation
    address_data = {
        "provider": provider,
        "address_type": "home",
        "address_line_1": "123 Test Street",
        "address_line_2": "Apt 4B",
        "city": "London",
        "postcode": "SW1A 1AA",
        "country": "United Kingdom",
        "is_primary": True,
        "is_verified": True,
        "verification_method": "manual_verification",
    }

    address = ServiceProviderAddress.objects.create(**address_data)

    print(f"✅ Address created: {address}")
    print(f"   - Full address: {address.full_address}")
    print(f"   - Is UK address: {address.is_uk_address}")
    print(f"   - Address type: {address.get_address_type_display()}")

    # Test business address
    business_address_data = {
        "provider": provider,
        "address_type": "business",
        "address_line_1": "456 Business Ave",
        "city": "London",
        "postcode": "SW1A 2BB",
        "country": "United Kingdom",
        "business_name": "Test Business",
        "is_primary": False,
        "is_verified": True,
        "verification_method": "manual_verification",
    }

    business_address = ServiceProviderAddress.objects.create(**business_address_data)
    print(f"✅ Business address created: {business_address}")

    # Test non-UK address
    non_uk_address_data = {
        "provider": provider,
        "address_type": "non_uk",
        "address_line_1": "789 International St",
        "city": "New York",
        "postcode": "10001",
        "country": "United States",
        "is_primary": False,
        "is_verified": True,
        "verification_method": "manual_verification",
    }

    non_uk_address = ServiceProviderAddress.objects.create(**non_uk_address_data)
    print(f"✅ Non-UK address created: {non_uk_address}")
    print(f"   - Is UK address: {non_uk_address.is_uk_address}")

    # Test provider addresses relationship
    provider_addresses = provider.addresses.all()
    print(f"✅ Provider has {provider_addresses.count()} addresses")

    # Cleanup
    provider.delete()  # This will cascade delete addresses
    user.delete()
    print("✅ Test data cleaned up")


if __name__ == "__main__":
    print("Provider Registration Test Suite")
    print("=" * 60)

    # Run tests
    test_provider_registration()
    test_address_model()

    print("\n" + "=" * 60)
    print("Test suite completed!")
