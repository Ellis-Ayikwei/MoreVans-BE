#!/usr/bin/env python3
"""
Debug script to diagnose Google Maps API issues
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_google_maps_api():
    """Test Google Maps API and provide detailed diagnostics"""

    print("🔍 Google Maps API Diagnostics")
    print("=" * 50)

    # 1. Check if API key exists
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY not found in environment variables")
        print("   Make sure your .env file contains: GOOGLE_MAPS_API_KEY=your-key-here")
        return False

    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")

    # 2. Test different Google Maps APIs
    apis_to_test = [
        {
            "name": "Places Autocomplete",
            "url": "https://maps.googleapis.com/maps/api/place/autocomplete/json",
            "params": {"input": "london", "key": api_key, "language": "en"},
        },
        {
            "name": "Geocoding",
            "url": "https://maps.googleapis.com/maps/api/geocode/json",
            "params": {"address": "London, UK", "key": api_key, "language": "en"},
        },
        {
            "name": "Place Details",
            "url": "https://maps.googleapis.com/maps/api/place/details/json",
            "params": {
                "place_id": "ChIJdd4hrwug2EcRmSrV3Vo6llI",  # London, UK
                "key": api_key,
                "fields": "formatted_address,name",
            },
        },
    ]

    for api_test in apis_to_test:
        print(f"\n🔧 Testing {api_test['name']}...")

        try:
            response = requests.get(
                api_test["url"], params=api_test["params"], timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")

                if status == "OK":
                    print(f"   ✅ {api_test['name']}: OK")
                    if "results" in data:
                        print(f"   📍 Found {len(data['results'])} results")
                    elif "predictions" in data:
                        print(f"   📍 Found {len(data['predictions'])} predictions")
                elif status == "REQUEST_DENIED":
                    print(f"   ❌ {api_test['name']}: REQUEST_DENIED")
                    error_message = data.get(
                        "error_message", "No error message provided"
                    )
                    print(f"   💬 Error: {error_message}")

                    # Provide specific troubleshooting steps
                    if "API key not valid" in error_message:
                        print(
                            "   🔧 Fix: Check if your API key is correct and not expired"
                        )
                    elif "not authorized" in error_message:
                        print(
                            "   🔧 Fix: Enable the required APIs in Google Cloud Console"
                        )
                    elif "billing" in error_message.lower():
                        print("   🔧 Fix: Enable billing for your Google Cloud project")
                    elif "quota" in error_message.lower():
                        print(
                            "   🔧 Fix: Check your API usage limits in Google Cloud Console"
                        )
                    elif "restriction" in error_message.lower():
                        print(
                            "   🔧 Fix: Check API key restrictions (domain/IP restrictions)"
                        )

                elif status == "ZERO_RESULTS":
                    print(f"   ⚠️  {api_test['name']}: ZERO_RESULTS (no results found)")
                elif status == "OVER_QUERY_LIMIT":
                    print(
                        f"   ⚠️  {api_test['name']}: OVER_QUERY_LIMIT (quota exceeded)"
                    )
                elif status == "INVALID_REQUEST":
                    print(f"   ❌ {api_test['name']}: INVALID_REQUEST (bad parameters)")
                else:
                    print(f"   ❓ {api_test['name']}: {status}")
                    print(f"   💬 Response: {data}")

            else:
                print(f"   ❌ {api_test['name']}: HTTP {response.status_code}")
                print(f"   💬 Response: {response.text}")

        except requests.exceptions.Timeout:
            print(f"   ⏰ {api_test['name']}: Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {api_test['name']}: Request failed - {str(e)}")
        except json.JSONDecodeError:
            print(f"   ❌ {api_test['name']}: Invalid JSON response")

    # 3. Check common issues
    print(f"\n🔍 Common Issues Check:")
    print("=" * 30)

    # Check if API key looks valid (basic format check)
    if len(api_key) < 20:
        print("❌ API key seems too short (should be ~40 characters)")
    elif not api_key.startswith("AIza"):
        print("❌ API key doesn't start with 'AIza' (unusual format)")
    else:
        print("✅ API key format looks correct")

    # 4. Provide next steps
    print(f"\n📋 Next Steps:")
    print("=" * 20)

    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Select your project")
    print("3. Go to 'APIs & Services' > 'Enabled APIs'")
    print("4. Make sure these APIs are enabled:")
    print("   - Google Maps JavaScript API")
    print("   - Places API")
    print("   - Geocoding API")
    print("5. Go to 'APIs & Services' > 'Credentials'")
    print("6. Check your API key restrictions")
    print("7. Verify billing is enabled for your project")

    return True


def test_specific_error():
    """Test for specific error patterns"""

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return

    print(f"\n🔍 Testing for specific error patterns...")

    # Test with minimal parameters
    test_url = "https://maps.googleapis.com/maps/api/geocode/json"
    test_params = {"address": "test", "key": api_key}

    try:
        response = requests.get(test_url, params=test_params, timeout=10)
        data = response.json()

        if data.get("status") == "REQUEST_DENIED":
            error_message = data.get("error_message", "").lower()

            if "api key not valid" in error_message:
                print("🎯 Issue: Invalid API key")
                print("   Solution: Generate a new API key in Google Cloud Console")
            elif "not authorized" in error_message:
                print("🎯 Issue: API not enabled")
                print("   Solution: Enable the required APIs in your project")
            elif "billing" in error_message:
                print("🎯 Issue: Billing not enabled")
                print("   Solution: Enable billing for your Google Cloud project")
            elif "quota" in error_message:
                print("🎯 Issue: Quota exceeded")
                print("   Solution: Check usage limits or upgrade billing plan")
            elif "restriction" in error_message:
                print("🎯 Issue: API key restrictions")
                print("   Solution: Check domain/IP restrictions on your API key")
            else:
                print(
                    f"🎯 Issue: Unknown - {data.get('error_message', 'No error message')}"
                )

    except Exception as e:
        print(f"❌ Error testing specific patterns: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Google Maps API Diagnostics...\n")

    # Run main diagnostics
    success = test_google_maps_api()

    # Run specific error testing
    test_specific_error()

    print(f"\n✅ Diagnostics complete!")
    print("📖 Check the GOOGLE_MAPS_API_SETUP.md file for detailed solutions.")
