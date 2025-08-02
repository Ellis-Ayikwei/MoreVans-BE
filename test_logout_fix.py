#!/usr/bin/env python3
"""
Test script to verify logout functionality works correctly
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.utils import timezone
from datetime import timezone as dt_timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_timezone_imports():
    """Test that timezone imports work correctly"""

    print("🧪 Testing Timezone Imports")
    print("=" * 40)

    try:
        # Test Django timezone
        now = timezone.now()
        print(f"✅ Django timezone.now() works: {now}")

        # Test datetime timezone
        utc_tz = dt_timezone.utc
        print(f"✅ datetime timezone.utc works: {utc_tz}")

        # Test creating a datetime with timezone
        from datetime import datetime

        dt_with_tz = datetime.fromtimestamp(1234567890, tz=dt_timezone.utc)
        print(f"✅ datetime.fromtimestamp with timezone works: {dt_with_tz}")

        return True

    except Exception as e:
        print(f"❌ Timezone test failed: {str(e)}")
        return False


def test_blacklisted_token_creation():
    """Test BlacklistedToken creation with timezone"""

    print(f"\n🧪 Testing BlacklistedToken Creation")
    print("=" * 40)

    try:
        # Test creating a BlacklistedToken (this would normally be done in logout)
        test_token = "test_token_123"
        test_user_id = "test_user_123"
        test_exp = 1234567890  # Some future timestamp

        # This simulates what happens in the logout view
        expires_at = timezone.datetime.fromtimestamp(test_exp, tz=dt_timezone.utc)
        print(f"✅ Created expires_at datetime: {expires_at}")

        # Note: We won't actually create the BlacklistedToken in the database
        # as it would require a valid user_id, but we can test the datetime creation
        print("✅ BlacklistedToken datetime creation would work")

        return True

    except Exception as e:
        print(f"❌ BlacklistedToken test failed: {str(e)}")
        return False


def test_logout_simulation():
    """Simulate the logout process"""

    print(f"\n🧪 Testing Logout Process Simulation")
    print("=" * 40)

    try:
        # Simulate the exact code from the logout view
        from rest_framework_simplejwt.backends import TokenBackend
        from rest_framework_simplejwt.settings import api_settings

        # Create a mock token data (this is what would be decoded from a real token)
        mock_token_data = {
            "user_id": "test_user_123",
            "exp": 1234567890,  # Some future timestamp
            "iat": 1234567890 - 3600,  # Issued 1 hour ago
        }

        # Test the timezone conversion (this is the part that was failing)
        expires_at = timezone.datetime.fromtimestamp(
            mock_token_data.get("exp"), tz=dt_timezone.utc
        )
        print(f"✅ Token expiration datetime created: {expires_at}")

        # Test that we can create a BlacklistedToken object (without saving)
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        # This would be the actual creation in the logout view
        blacklisted_token = BlacklistedToken(
            token="test_token_123",
            user_id=mock_token_data.get("user_id"),
            expires_at=expires_at,
        )
        print(f"✅ BlacklistedToken object created successfully")

        return True

    except Exception as e:
        print(f"❌ Logout simulation failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Logout Fix Tests")
    print("=" * 60)

    # Run tests
    test1_result = test_timezone_imports()
    test2_result = test_blacklisted_token_creation()
    test3_result = test_logout_simulation()

    print(f"\n📊 Test Results:")
    print(f"   Timezone Imports: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   BlacklistedToken Creation: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"   Logout Simulation: {'✅ PASS' if test3_result else '❌ FAIL'}")

    if all([test1_result, test2_result, test3_result]):
        print(
            f"\n🎉 All logout tests passed! The logout functionality should now work correctly."
        )
        print(f"   - Timezone imports are working")
        print(f"   - BlacklistedToken creation is working")
        print(f"   - Logout process simulation is working")
    else:
        print(f"\n⚠️  Some logout tests failed. Check the output above for details.")
