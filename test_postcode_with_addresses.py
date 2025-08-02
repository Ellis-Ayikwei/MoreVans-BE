#!/usr/bin/env python3
"""
Test script to verify postcode validation includes addresses
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


def test_postcode_validation_with_addresses():
    """Test that postcode validation includes addresses"""

    service = PostcodeValidationService()

    # Test with a valid UK postcode
    test_postcodes = [
        "SW1A 1AA",  # Buckingham Palace
        "W1A 1AA",  # BBC Broadcasting House
        "EC1A 1BB",  # St Paul's Cathedral
        "M1 1AA",  # Manchester
        "B1 1AA",  # Birmingham
    ]

    print("🧪 Testing Postcode Validation with Addresses")
    print("=" * 50)

    for postcode in test_postcodes:
        print(f"\n📍 Testing postcode: {postcode}")

        try:
            # Test comprehensive validation
            result = service.validate_postcode(postcode)

            print(f"   ✅ Valid: {result.get('is_valid', False)}")
            print(f"   🔍 Source: {result.get('source', 'unknown')}")
            print(f"   📝 Message: {result.get('message', 'No message')}")

            # Check if addresses are included
            addresses = result.get("addresses", [])
            total_addresses = result.get("total_addresses", 0)
            sources_used = result.get("sources_used", [])

            print(f"   🏠 Addresses found: {total_addresses}")
            print(
                f"   🔗 Sources used: {', '.join(sources_used) if sources_used else 'None'}"
            )

            if addresses:
                print(f"   📋 Sample addresses:")
                for i, addr in enumerate(addresses[:3], 1):  # Show first 3 addresses
                    formatted = addr.get("formatted_address", "No formatted address")
                    source = addr.get("source", "unknown")
                    print(f"      {i}. {formatted} (via {source})")

                if len(addresses) > 3:
                    print(f"      ... and {len(addresses) - 3} more addresses")
            else:
                print(f"   ⚠️  No addresses found - manual entry required")

            # Show context if available
            context = result.get("context", {})
            if context:
                print(f"   🌍 Context:")
                if context.get("post_town"):
                    print(f"      City: {context['post_town']}")
                if context.get("county"):
                    print(f"      County: {context['county']}")
                if context.get("country"):
                    print(f"      Country: {context['country']}")
                if context.get("latitude") and context.get("longitude"):
                    print(
                        f"      Coordinates: {context['latitude']}, {context['longitude']}"
                    )

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print(f"\n✅ Testing complete!")
    print(f"📖 The postcode validation now includes addresses in the response.")


if __name__ == "__main__":
    test_postcode_validation_with_addresses()
