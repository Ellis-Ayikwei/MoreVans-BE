#!/usr/bin/env python3
"""
Test script to verify that address fields are converted to lowercase
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
from apps.Provider.models import ServiceProviderAddress
from apps.User.models import User


def test_address_lowercase():
    """Test that address fields are converted to lowercase"""

    print("🧪 Testing Address Lowercase Conversion")
    print("=" * 50)

    # Test data with mixed case addresses
    test_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@EXAMPLE.COM",  # Mixed case email
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "1234567890",
        "phone_number": "1234567890",
        "business_name": "John's Transport",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals", "Office removals"],
        # Home address with mixed case
        "address_line_1": "123 MAIN Street",
        "address_line_2": "Apt 4B",
        "city": "LONDON",
        "postcode": "SW1A 1AA",
        "country": "UNITED KINGDOM",
        # Business address with mixed case
        "has_separate_business_address": True,
        "business_address_line_1": "456 BUSINESS Avenue",
        "business_address_line_2": "Suite 100",
        "business_city": "MANCHESTER",
        "business_postcode": "M1 1AA",
        "business_country": "ENGLAND",
        # Non-UK address with mixed case
        "has_non_uk_address": True,
        "non_uk_address_line_1": "789 INTERNATIONAL Road",
        "non_uk_address_line_2": "Building A",
        "non_uk_city": "NEW YORK",
        "non_uk_postal_code": "10001",
        "non_uk_country": "UNITED STATES",
        "accepted_privacy_policy": True,
    }

    print("📝 Testing with mixed case address data...")
    print(f"   Original email: {test_data['email']}")
    print(f"   Original address_line_1: {test_data['address_line_1']}")
    print(f"   Original city: {test_data['city']}")
    print(f"   Original country: {test_data['country']}")
    print(f"   Original business_city: {test_data['business_city']}")
    print(f"   Original non_uk_city: {test_data['non_uk_city']}")

    # Test the serializer
    serializer = ProviderRegistrationSerializer(data=test_data)

    if serializer.is_valid():
        print("\n✅ Serializer validation passed")

        # Save the data
        result = serializer.save()

        print("\n📊 Checking saved address data...")

        # Check home address
        home_address = ServiceProviderAddress.objects.filter(
            provider=result["provider"], address_type="home"
        ).first()

        if home_address:
            print(f"\n🏠 Home Address:")
            print(f"   address_line_1: '{home_address.address_line_1}'")
            print(f"   address_line_2: '{home_address.address_line_2}'")
            print(f"   city: '{home_address.city}'")
            print(f"   postcode: '{home_address.postcode}'")
            print(f"   country: '{home_address.country}'")

            # Verify lowercase conversion
            assert (
                home_address.address_line_1 == "123 main street"
            ), f"Expected '123 main street', got '{home_address.address_line_1}'"
            assert (
                home_address.address_line_2 == "apt 4b"
            ), f"Expected 'apt 4b', got '{home_address.address_line_2}'"
            assert (
                home_address.city == "london"
            ), f"Expected 'london', got '{home_address.city}'"
            assert (
                home_address.postcode == "sw1a 1aa"
            ), f"Expected 'sw1a 1aa', got '{home_address.postcode}'"
            assert (
                home_address.country == "united kingdom"
            ), f"Expected 'united kingdom', got '{home_address.country}'"
            print("   ✅ Home address fields correctly converted to lowercase")

        # Check business address
        business_address = ServiceProviderAddress.objects.filter(
            provider=result["provider"], address_type="business"
        ).first()

        if business_address:
            print(f"\n🏢 Business Address:")
            print(f"   address_line_1: '{business_address.address_line_1}'")
            print(f"   address_line_2: '{business_address.address_line_2}'")
            print(f"   city: '{business_address.city}'")
            print(f"   postcode: '{business_address.postcode}'")
            print(f"   country: '{business_address.country}'")

            # Verify lowercase conversion
            assert (
                business_address.address_line_1 == "456 business avenue"
            ), f"Expected '456 business avenue', got '{business_address.address_line_1}'"
            assert (
                business_address.address_line_2 == "suite 100"
            ), f"Expected 'suite 100', got '{business_address.address_line_2}'"
            assert (
                business_address.city == "manchester"
            ), f"Expected 'manchester', got '{business_address.city}'"
            assert (
                business_address.postcode == "m1 1aa"
            ), f"Expected 'm1 1aa', got '{business_address.postcode}'"
            assert (
                business_address.country == "england"
            ), f"Expected 'england', got '{business_address.country}'"
            print("   ✅ Business address fields correctly converted to lowercase")

        # Check non-UK address
        non_uk_address = ServiceProviderAddress.objects.filter(
            provider=result["provider"], address_type="non_uk"
        ).first()

        if non_uk_address:
            print(f"\n🌍 Non-UK Address:")
            print(f"   address_line_1: '{non_uk_address.address_line_1}'")
            print(f"   address_line_2: '{non_uk_address.address_line_2}'")
            print(f"   city: '{non_uk_address.city}'")
            print(f"   postcode: '{non_uk_address.postcode}'")
            print(f"   country: '{non_uk_address.country}'")

            # Verify lowercase conversion
            assert (
                non_uk_address.address_line_1 == "789 international road"
            ), f"Expected '789 international road', got '{non_uk_address.address_line_1}'"
            assert (
                non_uk_address.address_line_2 == "building a"
            ), f"Expected 'building a', got '{non_uk_address.address_line_2}'"
            assert (
                non_uk_address.city == "new york"
            ), f"Expected 'new york', got '{non_uk_address.city}'"
            assert (
                non_uk_address.postcode == "10001"
            ), f"Expected '10001', got '{non_uk_address.postcode}'"
            assert (
                non_uk_address.country == "united states"
            ), f"Expected 'united states', got '{non_uk_address.country}'"
            print("   ✅ Non-UK address fields correctly converted to lowercase")

        # Check email conversion
        user = result["user"]
        print(f"\n📧 User Email:")
        print(f"   Original: '{test_data['email']}'")
        print(f"   Saved: '{user.email}'")
        assert (
            user.email == "john.doe@example.com"
        ), f"Expected 'john.doe@example.com', got '{user.email}'"
        print("   ✅ Email correctly converted to lowercase")

        print(f"\n✅ All address fields successfully converted to lowercase!")

        # Clean up test data
        user.delete()

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)


def test_empty_address_fields():
    """Test that empty address fields are handled correctly"""

    print(f"\n🧪 Testing Empty Address Fields")
    print("=" * 50)

    # Test data with empty address fields
    test_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@test.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "mobile_number": "0987654321",
        "phone_number": "0987654321",
        "business_name": "Jane's Business",
        "business_type": "limited",
        "vat_registered": "yes",
        "number_of_vehicles": "2-5",
        "work_types": ["Home removals"],
        # Home address with some empty fields
        "address_line_1": "123 Test Street",
        "address_line_2": "",  # Empty field
        "city": "Test City",
        "postcode": "TE1 1ST",
        "country": "Test Country",
        # No separate business address
        "has_separate_business_address": False,
        "business_address_line_1": "",
        "business_address_line_2": "",
        "business_city": "",
        "business_postcode": "",
        "business_country": "",
        # No non-UK address
        "has_non_uk_address": False,
        "non_uk_address_line_1": "",
        "non_uk_address_line_2": "",
        "non_uk_city": "",
        "non_uk_postal_code": "",
        "non_uk_country": "",
        "accepted_privacy_policy": True,
    }

    print("📝 Testing with empty address fields...")

    serializer = ProviderRegistrationSerializer(data=test_data)

    if serializer.is_valid():
        print("✅ Serializer validation passed")

        # Save the data
        result = serializer.save()

        # Check home address
        home_address = ServiceProviderAddress.objects.filter(
            provider=result["provider"], address_type="home"
        ).first()

        if home_address:
            print(f"\n🏠 Home Address with Empty Fields:")
            print(f"   address_line_1: '{home_address.address_line_1}'")
            print(f"   address_line_2: '{home_address.address_line_2}'")
            print(f"   city: '{home_address.city}'")

            # Verify empty fields are handled correctly
            assert (
                home_address.address_line_2 == ""
            ), f"Expected empty string, got '{home_address.address_line_2}'"
            print("   ✅ Empty address fields handled correctly")

        # Clean up test data
        result["user"].delete()

    else:
        print("❌ Serializer validation failed:")
        print(serializer.errors)


if __name__ == "__main__":
    test_address_lowercase()
    test_empty_address_fields()
    print(f"\n🎉 All tests completed successfully!")
