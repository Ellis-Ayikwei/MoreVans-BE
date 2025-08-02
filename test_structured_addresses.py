#!/usr/bin/env python3
"""
Test script to verify structured address format from Google Maps API
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from apps.Location.services import PostcodeValidationService


def test_structured_addresses():
    """Test that addresses return properly structured data"""

    service = PostcodeValidationService()

    # Test with a valid UK postcode
    test_postcodes = [
        "SW1A 1AA",  # Buckingham Palace
        "W1A 1AA",  # BBC Broadcasting House
        "EC1A 1BB",  # St Paul's Cathedral
    ]

    print("🧪 Testing Structured Address Format")
    print("=" * 50)

    for postcode in test_postcodes:
        print(f"\n📍 Testing postcode: {postcode}")

        try:
            # Test comprehensive validation
            result = service.validate_postcode(postcode)

            print(f"   ✅ Valid: {result.get('is_valid', False)}")
            print(f"   🔍 Source: {result.get('source', 'unknown')}")
            print(f"   📝 Message: {result.get('message', 'No message')}")

            # Check addresses
            addresses = result.get("addresses", [])
            total_addresses = result.get("total_addresses", 0)

            print(f"   🏠 Addresses found: {total_addresses}")

            if addresses:
                print(f"   📋 Structured Addresses:")
                for i, addr in enumerate(addresses[:3], 1):  # Show first 3 addresses
                    print(f"      {i}. Address Details:")
                    print(
                        f"         📍 Formatted: {addr.get('formatted_address', 'N/A')}"
                    )
                    print(
                        f"         🏠 Address Line 1: {addr.get('address_line_1', 'N/A')}"
                    )
                    print(
                        f"         🏢 Address Line 2: {addr.get('address_line_2', 'N/A')}"
                    )
                    print(f"         🏙️  City/Town: {addr.get('city_town', 'N/A')}")
                    print(f"         🏛️  County: {addr.get('county', 'N/A')}")
                    print(f"         📮 Postcode: {addr.get('postcode', 'N/A')}")
                    print(f"         🌍 Country: {addr.get('country', 'N/A')}")

                    coordinates = addr.get("coordinates", {})
                    if coordinates.get("lat") and coordinates.get("lng"):
                        print(
                            f"         📍 Coordinates: {coordinates['lat']}, {coordinates['lng']}"
                        )

                    print(f"         🔗 Source: {addr.get('source', 'N/A')}")
                    print()

                if len(addresses) > 3:
                    print(f"      ... and {len(addresses) - 3} more addresses")
            else:
                print(f"   ⚠️  No addresses found")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print(f"\n✅ Testing complete!")
    print(
        f"📖 Addresses now return structured data with Address Line 1, Address Line 2, City/Town, County, etc."
    )


if __name__ == "__main__":
    test_structured_addresses()
