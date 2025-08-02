from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Location
from .serializer import LocationSerializer
from rest_framework.response import Response
from rest_framework import status
import requests
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import re
from .services import PostcodeValidationService

logger = logging.getLogger(__name__)


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Location instances.
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Location.objects.all()
        postcode = self.request.query_params.get("postcode", None)
        contact_name = self.request.query_params.get("contact_name", None)

        if postcode:
            queryset = queryset.filter(postcode__icontains=postcode)
        if contact_name:
            queryset = queryset.filter(contact_name__icontains=contact_name)

        return queryset


# Option 1: Using Ideal Postcodes API (recommended for production)
@api_view(["GET"])
@permission_classes([AllowAny])
def validate_postcode_ideal(request, postcode):
    """
    Validate a UK postcode and return available addresses using Ideal Postcodes API
    """
    try:
        logger.info(f"Validating postcode: {postcode}")

        # Format postcode for API (remove extra spaces and convert to uppercase)
        formatted_postcode = postcode.replace(" ", "").upper()

        # Insert space in correct position for UK postcode format
        if len(formatted_postcode) > 3:
            formatted_postcode = formatted_postcode[:-3] + " " + formatted_postcode[-3:]

        logger.info(f"Formatted postcode: {formatted_postcode}")

        # Ideal Postcodes API endpoint
        # You'll need to sign up for API key at https://ideal-postcodes.co.uk/
        API_KEY = "YOUR_IDEAL_POSTCODES_API_KEY"  # Get from settings
        api_url = f"https://api.ideal-postcodes.co.uk/v1/postcodes/{formatted_postcode}"

        headers = {"Authorization": f"api_key={API_KEY}"}

        logger.info(f"Calling Ideal Postcodes API: {api_url}")
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            addresses = data.get("result", [])
            logger.info(f"Found {len(addresses)} addresses")

            # Format addresses for frontend
            formatted_addresses = []
            for addr in addresses:
                formatted_addresses.append(
                    {
                        "line1": addr.get("line_1", ""),
                        "line2": addr.get("line_2", ""),
                        "line3": addr.get("line_3", ""),
                        "city": addr.get("post_town", ""),
                        "county": addr.get("county", ""),
                        "postcode": addr.get("postcode", ""),
                        "building_name": addr.get("building_name", ""),
                        "building_number": addr.get("building_number", ""),
                        "thoroughfare": addr.get("thoroughfare", ""),
                        "dependent_locality": addr.get("dependent_locality", ""),
                    }
                )

            logger.info(f"Returning {len(formatted_addresses)} formatted addresses")
            return Response({"isValid": True, "addresses": formatted_addresses})

        elif response.status_code == 404:
            logger.warning(f"Postcode not found: {postcode}")
            return Response({"isValid": False, "message": "Postcode not found"})

        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return Response(
                {"isValid": False, "message": "Error validating postcode"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Error validating postcode: {str(e)}", exc_info=True)
        return Response(
            {"isValid": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def validate_postcode_mock(request, postcode):
    """
    Mock implementation for development/testing
    """
    try:
        logger.info(f"Mock validating postcode: {postcode}")

        # Format postcode
        formatted_postcode = postcode.replace(" ", "").upper()
        if len(formatted_postcode) > 3:
            formatted_postcode = formatted_postcode[:-3] + " " + formatted_postcode[-3:]

        # Basic UK postcode validation
        import re

        uk_postcode_regex = r"^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$"
        if not re.match(uk_postcode_regex, formatted_postcode, re.IGNORECASE):
            return Response({"isValid": False, "message": "Invalid UK postcode format"})

        # Mock addresses for valid postcodes
        mock_addresses = [
            {
                "line1": "123 High Street",
                "line2": "",
                "city": "London",
                "county": "Greater London",
                "postcode": formatted_postcode,
                "building_number": "123",
                "thoroughfare": "High Street",
            },
            {
                "line1": "45 High Street",
                "line2": "Flat 2",
                "city": "London",
                "county": "Greater London",
                "postcode": formatted_postcode,
                "building_number": "45",
                "thoroughfare": "High Street",
            },
            {
                "line1": "67 High Street",
                "line2": "",
                "city": "London",
                "county": "Greater London",
                "postcode": formatted_postcode,
                "building_number": "67",
                "thoroughfare": "High Street",
            },
        ]

        return Response({"isValid": True, "addresses": mock_addresses})

    except Exception as e:
        logger.error(f"Error in mock validation: {str(e)}", exc_info=True)
        return Response(
            {"isValid": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Option 3: Using postcodes.io for validation only + manual address entry
@api_view(["GET"])
@permission_classes([AllowAny])
def validate_postcode(request, postcode):
    """
    Simple postcode validation using postcodes.io (validation only, no addresses)
    """
    try:
        logger.info(f"Validating postcode: {postcode}")
        formatted_postcode = postcode.replace(" ", "").upper()

        # Call postcodes.io API to validate postcode only
        validate_url = (
            f"https://api.postcodes.io/postcodes/{formatted_postcode}/validate"
        )
        response = requests.get(validate_url)

        if response.status_code == 200:
            data = response.json()
            is_valid = data.get("result", False)

            if is_valid:
                # Get postcode details for context
                details_url = f"https://api.postcodes.io/postcodes/{formatted_postcode}"
                details_response = requests.get(details_url)

                context = {}
                if details_response.status_code == 200:
                    details_data = details_response.json()
                    result = details_data.get("result", {})
                    context = {
                        "post_town": result.get("admin_district", ""),
                        "county": result.get("admin_county", ""),
                        "region": result.get("region", ""),
                    }

                return Response(
                    {
                        "isValid": True,
                        "requiresManualEntry": True,  # Signal frontend to show manual entry
                        "context": context,  # Provide context for manual entry
                        "message": "Postcode is valid. Please enter your full address.",
                    }
                )
            else:
                return Response({"isValid": False, "message": "Invalid postcode"})
        else:
            return Response(
                {"isValid": False, "message": "Unable to validate postcode"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Error validating postcode: {str(e)}", exc_info=True)
        return Response(
            {"isValid": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class PostcodeSuggestionsView(APIView):
    """
    Get postcode suggestions based on the search query.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return Response({"suggestions": []})

        try:
            # Call postcodes.io API for suggestions
            response = requests.get(
                f"https://api.postcodes.io/postcodes/{query}/autocomplete"
            )
            data = response.json()

            if response.status_code == 200 and data.get("result"):
                suggestions = data["result"]
                logger.info(
                    f"Found {len(suggestions)} postcode suggestions for query: {query}"
                )
                return Response({"suggestions": suggestions})
            else:
                logger.warning(f"No postcode suggestions found for query: {query}")
                return Response({"suggestions": []})

        except Exception as e:
            logger.error(f"Error getting postcode suggestions: {str(e)}", exc_info=True)
            return Response({"error": "Error getting postcode suggestions"}, status=500)


class GoogleAddressAutocompleteView(APIView):
    """
    Google Maps Address Autocomplete API proxy to avoid CORS issues
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        from django.conf import settings

        try:
            input_text = request.GET.get("input", "").strip()
            if not input_text:
                return Response({"predictions": []})

            # Get Google Maps API key from settings
            google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
            if not google_api_key:
                logger.error("Google Maps API key not configured")
                return Response(
                    {"error": "Google Maps API key not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Build Google Places Autocomplete request
            params = {
                "input": input_text,
                "key": google_api_key,
                "language": "en",
            }

            # Add session token if provided (for billing optimization)
            session_token = request.GET.get("sessiontoken")
            if session_token:
                params["sessiontoken"] = session_token

            response = requests.get(
                "https://maps.googleapis.com/maps/api/place/autocomplete/json",
                params=params,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()

                # Check for API errors
                if data.get("status") != "OK":
                    logger.warning(f'Google API returned status: {data.get("status")}')
                    return Response({"predictions": [], "status": data.get("status")})

                predictions = data.get("predictions", [])
                logger.info(
                    f"Found {len(predictions)} address predictions for: {input_text}"
                )

                return Response({"predictions": predictions, "status": "OK"})
            else:
                logger.error(
                    f"Google API error: {response.status_code} - {response.text}"
                )
                return Response(
                    {"error": "Google API request failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(
                f"Error in Google address autocomplete: {str(e)}", exc_info=True
            )
            return Response(
                {"error": "Address autocomplete failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@csrf_exempt
@api_view(["GET"])
@permission_classes([AllowAny])
def google_place_details(request):
    """
    Google Maps Place Details API proxy to get full address and coordinates
    """
    from django.conf import settings

    try:
        place_id = request.GET.get("place_id", "").strip()
        if not place_id:
            return Response({"error": "place_id parameter required"}, status=400)

        print(f"🏠 ADDRESS SELECTED - Getting details for place_id: {place_id}")

        # Get Google Maps API key from settings
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            logger.error("Google Maps API key not configured")
            return Response(
                {"error": "Google Maps API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Build Google Place Details request
        params = {
            "place_id": place_id,
            "key": google_api_key,
            "fields": "formatted_address,geometry,address_components,name",
            "language": "en",
        }

        # Add session token if provided (for billing optimization)
        session_token = request.GET.get("sessiontoken")
        if session_token:
            params["sessiontoken"] = session_token

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            # Check for API errors
            if data.get("status") != "OK":
                logger.warning(
                    f'Google Place Details API returned status: {data.get("status")}'
                )
                return Response({"error": data.get("status")}, status=400)

            result = data.get("result", {})

            # Print selected address details
            formatted_address = result.get("formatted_address", "")
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})

            print(f"📍 SELECTED ADDRESS: {formatted_address}")
            if location:
                print(
                    f"🌍 COORDINATES: Lat {location.get('lat')}, Lng {location.get('lng')}"
                )

            # Parse address components for easier frontend use
            parsed_address = parse_google_address_components(
                result.get("address_components", [])
            )

            if parsed_address:
                print(f"🏘️  ADDRESS COMPONENTS:")
                if parsed_address.get("street_number"):
                    print(f"   - Street Number: {parsed_address['street_number']}")
                if parsed_address.get("route"):
                    print(f"   - Street: {parsed_address['route']}")
                if parsed_address.get("locality"):
                    print(f"   - City: {parsed_address['locality']}")
                if parsed_address.get("postal_code"):
                    print(f"   - Postcode: {parsed_address['postal_code']}")
                if parsed_address.get("country"):
                    print(f"   - Country: {parsed_address['country']}")

            # Extract useful information
            place_data = {
                "formatted_address": formatted_address,
                "geometry": geometry,
                "address_components": result.get("address_components", []),
                "name": result.get("name", ""),
            }

            place_data["parsed_address"] = parsed_address

            logger.info(f"Retrieved place details for place_id: {place_id}")
            print(f"✅ ADDRESS SELECTION COMPLETE\n")

            return Response({"result": place_data, "status": "OK"})
        else:
            logger.error(
                f"Google Place Details API error: {response.status_code} - {response.text}"
            )
            return Response(
                {"error": "Google API request failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Error in Google place details: {str(e)}", exc_info=True)
        print(f"❌ ERROR getting address details: {str(e)}")
        return Response(
            {"error": "Place details request failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def parse_google_address_components(components):
    """
    Parse Google Maps address components into a more usable format
    """
    parsed = {
        "street_number": "",
        "route": "",
        "locality": "",
        "postal_town": "",
        "administrative_area_level_1": "",
        "administrative_area_level_2": "",
        "country": "",
        "postal_code": "",
    }

    for component in components:
        types = component.get("types", [])
        long_name = component.get("long_name", "")

        if "street_number" in types:
            parsed["street_number"] = long_name
        elif "route" in types:
            parsed["route"] = long_name
        elif "locality" in types:
            parsed["locality"] = long_name
        elif "postal_town" in types:
            parsed["postal_town"] = long_name
        elif "administrative_area_level_1" in types:
            parsed["administrative_area_level_1"] = long_name
        elif "administrative_area_level_2" in types:
            parsed["administrative_area_level_2"] = long_name
        elif "country" in types:
            parsed["country"] = long_name
        elif "postal_code" in types:
            parsed["postal_code"] = long_name

    return parsed


@api_view(["GET"])
@permission_classes([AllowAny])
def geocode_address(request):
    """
    Geocode an address using Google Maps Geocoding API
    """
    from django.conf import settings

    try:
        address = request.GET.get("address", "").strip()
        if not address:
            return Response({"error": "address parameter required"}, status=400)

        # Get Google Maps API key from settings
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            logger.error("Google Maps API key not configured")
            return Response(
                {"error": "Google Maps API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Build Google Geocoding request
        params = {
            "address": address,
            "key": google_api_key,
            "components": "country:GB",  # Restrict to UK
            "language": "en",
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            # Check for API errors
            if data.get("status") not in ["OK", "ZERO_RESULTS"]:
                logger.warning(
                    f'Google Geocoding API returned status: {data.get("status")}'
                )
                return Response({"error": data.get("status")}, status=400)

            results = data.get("results", [])
            logger.info(f"Found {len(results)} geocoding results for: {address}")

            return Response({"results": results, "status": data.get("status", "OK")})
        else:
            logger.error(
                f"Google Geocoding API error: {response.status_code} - {response.text}"
            )
            return Response(
                {"error": "Google API request failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Error in geocoding: {str(e)}", exc_info=True)
        return Response(
            {"error": "Geocoding request failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Keep the original function-based views as backup
postcode_suggestions = PostcodeSuggestionsView.as_view()
google_address_autocomplete = GoogleAddressAutocompleteView.as_view()


@csrf_exempt
@require_http_methods(["GET"])
def google_address_autocomplete_simple(request):
    """
    Simple Django view for Google Maps Address Autocomplete API proxy
    This bypasses DRF authentication entirely
    """
    from django.conf import settings
    import json

    try:
        input_text = request.GET.get("input", "").strip()
        if not input_text:
            return JsonResponse({"predictions": []})

        print(f"🔍 SEARCHING ADDRESSES for: '{input_text}'")

        # Get Google Maps API key from settings
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            logger.error("Google Maps API key not configured")
            return JsonResponse(
                {"error": "Google Maps API key not configured"}, status=500
            )

        # Build Google Places Autocomplete request
        params = {
            "input": input_text,
            "key": google_api_key,
            "language": "en",
        }

        # Add session token if provided (for billing optimization)
        session_token = request.GET.get("sessiontoken")
        if session_token:
            params["sessiontoken"] = session_token

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/autocomplete/json",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            # Check for API errors
            if data.get("status") != "OK":
                logger.warning(f'Google API returned status: {data.get("status")}')
                print(f"⚠️  API Status: {data.get('status')} for search: '{input_text}'")
                return JsonResponse({"predictions": [], "status": data.get("status")})

            predictions = data.get("predictions", [])
            logger.info(
                f"Found {len(predictions)} address predictions for: {input_text}"
            )

            print(f"📋 FOUND {len(predictions)} ADDRESSES:")
            for i, prediction in enumerate(predictions[:5], 1):  # Show first 5 results
                description = prediction.get("description", "")
                print(f"   {i}. {description}")
            if len(predictions) > 5:
                print(f"   ... and {len(predictions) - 5} more")
            print()  # Empty line for readability

            return JsonResponse({"predictions": predictions, "status": "OK"})
        else:
            logger.error(f"Google API error: {response.status_code} - {response.text}")
            print(f"❌ API ERROR: {response.status_code} for search: '{input_text}'")
            return JsonResponse({"error": "Google API request failed"}, status=500)

    except Exception as e:
        logger.error(f"Error in Google address autocomplete: {str(e)}", exc_info=True)
        print(f"❌ SEARCH ERROR for '{input_text}': {str(e)}")
        return JsonResponse({"error": "Address autocomplete failed"}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def postcode_suggestions_simple(request):
    """
    Simple Django view for postcode suggestions
    This bypasses DRF authentication entirely
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"suggestions": []})

    try:
        # Call postcodes.io API for suggestions
        response = requests.get(
            f"https://api.postcodes.io/postcodes/{query}/autocomplete"
        )
        data = response.json()

        if response.status_code == 200 and data.get("result"):
            suggestions = data["result"]
            logger.info(
                f"Found {len(suggestions)} postcode suggestions for query: {query}"
            )
            return JsonResponse({"suggestions": suggestions})
        else:
            logger.warning(f"No postcode suggestions found for query: {query}")
            return JsonResponse({"suggestions": []})

    except Exception as e:
        logger.error(f"Error getting postcode suggestions: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Error getting postcode suggestions"}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def postcode_address_lookup(request):
    """
    Get all available addresses for a specific UK postcode
    Uses multiple data sources for comprehensive results
    """
    from django.conf import settings
    import re

    try:
        postcode = request.GET.get("postcode", "").strip().upper()
        if not postcode:
            return JsonResponse({"error": "postcode parameter required"}, status=400)

        # Format postcode properly (add space if missing)
        postcode = format_uk_postcode(postcode)

        if not is_valid_uk_postcode(postcode):
            return JsonResponse({"error": "Invalid UK postcode format"}, status=400)

        logger.info(f"Looking up addresses for postcode: {postcode}")

        # Method 1: Try Google Places API first (works for many postcodes)
        google_addresses = get_addresses_from_google_places(postcode)

        # Method 2: Try Ideal Postcodes API if available
        ideal_addresses = get_addresses_from_ideal_postcodes(postcode)

        # Method 3: Get basic postcode info from postcodes.io
        postcode_info = get_postcode_info(postcode)

        # Combine and deduplicate results
        all_addresses = []

        # Add Google Places results
        for addr in google_addresses:
            all_addresses.append(
                {
                    "source": "google_places",
                    "formatted_address": addr.get("description", ""),
                    "place_id": addr.get("place_id"),
                    "main_text": addr.get("structured_formatting", {}).get(
                        "main_text", ""
                    ),
                    "secondary_text": addr.get("structured_formatting", {}).get(
                        "secondary_text", ""
                    ),
                }
            )

        # Add Ideal Postcodes results (if API key configured)
        for addr in ideal_addresses:
            all_addresses.append(
                {
                    "source": "ideal_postcodes",
                    "formatted_address": format_ideal_address(addr),
                    "address_line1": addr.get("line_1", ""),
                    "address_line2": addr.get("line_2", ""),
                    "address_line3": addr.get("line_3", ""),
                    "city": addr.get("post_town", ""),
                    "county": addr.get("county", ""),
                    "postcode": addr.get("postcode", ""),
                    "building_name": addr.get("building_name", ""),
                    "building_number": addr.get("building_number", ""),
                    "street": addr.get("thoroughfare", ""),
                }
            )

        # If no addresses found, provide postcode info
        if not all_addresses and postcode_info:
            all_addresses.append(
                {
                    "source": "postcodes_io",
                    "formatted_address": f"{postcode}, {postcode_info.get('admin_district', 'UK')}",
                    "postcode": postcode,
                    "city": postcode_info.get("admin_district", ""),
                    "county": postcode_info.get("admin_county", ""),
                    "country": postcode_info.get("country", "England"),
                    "coordinates": {
                        "lat": postcode_info.get("latitude"),
                        "lng": postcode_info.get("longitude"),
                    },
                }
            )

        logger.info(f"Found {len(all_addresses)} addresses for postcode: {postcode}")

        return JsonResponse(
            {
                "postcode": postcode,
                "addresses": all_addresses,
                "total_found": len(all_addresses),
                "sources_used": list(set(addr["source"] for addr in all_addresses)),
            }
        )

    except Exception as e:
        logger.error(f"Error in postcode address lookup: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Address lookup failed"}, status=500)


def format_uk_postcode(postcode):
    """Format UK postcode with proper spacing"""
    postcode = postcode.replace(" ", "").upper()
    if len(postcode) >= 5:
        return postcode[:-3] + " " + postcode[-3:]
    return postcode


def is_valid_uk_postcode(postcode):
    """Validate UK postcode format"""
    uk_postcode_regex = r"^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$"
    return bool(re.match(uk_postcode_regex, postcode, re.IGNORECASE))


def get_addresses_from_google_places(postcode):
    """Get addresses for postcode using Google Places API"""
    from django.conf import settings

    try:
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            return []

        # Search for the postcode in Google Places
        params = {
            "input": postcode,
            "key": google_api_key,
            "language": "en",
            "components": "country:gb",
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/autocomplete/json",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                return data.get("predictions", [])

    except Exception as e:
        logger.error(f"Error getting addresses from Google Places: {str(e)}")

    return []


def get_addresses_from_ideal_postcodes(postcode):
    """Get addresses for postcode using Ideal Postcodes API"""
    from django.conf import settings

    try:
        # Check if Ideal Postcodes API key is configured
        api_key = getattr(settings, "IDEAL_POSTCODES_API_KEY", None)
        if not api_key or api_key == "YOUR_IDEAL_POSTCODES_API_KEY":
            return []

        api_url = f"https://api.ideal-postcodes.co.uk/v1/postcodes/{postcode}"
        headers = {"Authorization": f"api_key={api_key}"}

        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("result", [])

    except Exception as e:
        logger.error(f"Error getting addresses from Ideal Postcodes: {str(e)}")

    return []


def get_postcode_info(postcode):
    """Get basic postcode information from postcodes.io"""
    try:
        api_url = f"https://api.postcodes.io/postcodes/{postcode}"
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get("result", {})

    except Exception as e:
        logger.error(f"Error getting postcode info: {str(e)}")

    return {}


def format_ideal_address(addr):
    """Format Ideal Postcodes address into readable string"""
    parts = []

    if addr.get("building_number"):
        parts.append(addr["building_number"])

    if addr.get("building_name"):
        parts.append(addr["building_name"])

    if addr.get("thoroughfare"):
        parts.append(addr["thoroughfare"])

    if addr.get("line_2"):
        parts.append(addr["line_2"])

    if addr.get("post_town"):
        parts.append(addr["post_town"])

    if addr.get("postcode"):
        parts.append(addr["postcode"])

    return ", ".join(filter(None, parts))


@csrf_exempt
@require_http_methods(["GET"])
def postcode_address_lookup_enhanced(request):
    """
    Enhanced postcode address lookup using Google Places Text Search
    More efficient than multiple autocomplete calls
    """
    from django.conf import settings
    import re

    try:
        postcode = request.GET.get("postcode", "").strip().upper()
        if not postcode:
            return JsonResponse({"error": "postcode parameter required"}, status=400)

        # Format postcode properly (add space if missing)
        postcode = format_uk_postcode(postcode)

        if not is_valid_uk_postcode(postcode):
            return JsonResponse({"error": "Invalid UK postcode format"}, status=400)

        logger.info(f"Enhanced lookup for postcode: {postcode}")

        # Method 1: Google Places Text Search (more comprehensive than autocomplete)
        google_addresses = get_addresses_from_google_text_search(postcode)

        # Method 2: Google Geocoding + Nearby Search
        geocoded_addresses = get_addresses_from_geocoding_nearby(postcode)

        # Method 3: Ideal Postcodes API if available (most comprehensive for UK)
        ideal_addresses = get_addresses_from_ideal_postcodes(postcode)

        # Method 4: Get basic postcode info from postcodes.io
        postcode_info = get_postcode_info(postcode)

        # Combine and deduplicate results
        all_addresses = []

        # Add Google Text Search results (better than autocomplete)
        for addr in google_addresses:
            all_addresses.append(
                {
                    "source": "google_text_search",
                    "formatted_address": addr.get("formatted_address", ""),
                    "place_id": addr.get("place_id"),
                    "name": addr.get("name", ""),
                    "types": addr.get("types", []),
                    "geometry": addr.get("geometry", {}),
                }
            )

        # Add Google Geocoding + Nearby results
        for addr in geocoded_addresses:
            all_addresses.append(
                {
                    "source": "google_geocoding_nearby",
                    "formatted_address": addr.get("formatted_address", ""),
                    "place_id": addr.get("place_id"),
                    "name": addr.get("name", ""),
                    "types": addr.get("types", []),
                    "geometry": addr.get("geometry", {}),
                }
            )

        # Add Ideal Postcodes results (best for residential addresses)
        for addr in ideal_addresses:
            all_addresses.append(
                {
                    "source": "ideal_postcodes",
                    "formatted_address": format_ideal_address(addr),
                    "address_line1": addr.get("line_1", ""),
                    "address_line2": addr.get("line_2", ""),
                    "address_line3": addr.get("line_3", ""),
                    "city": addr.get("post_town", ""),
                    "county": addr.get("county", ""),
                    "postcode": addr.get("postcode", ""),
                    "building_name": addr.get("building_name", ""),
                    "building_number": addr.get("building_number", ""),
                    "street": addr.get("thoroughfare", ""),
                }
            )

        # If no addresses found, provide postcode info for manual entry
        if not all_addresses and postcode_info:
            all_addresses.append(
                {
                    "source": "postcodes_io",
                    "formatted_address": f"{postcode}, {postcode_info.get('admin_district', 'UK')}",
                    "postcode": postcode,
                    "city": postcode_info.get("admin_district", ""),
                    "county": postcode_info.get("admin_county", ""),
                    "country": postcode_info.get("country", "England"),
                    "coordinates": {
                        "lat": postcode_info.get("latitude"),
                        "lng": postcode_info.get("longitude"),
                    },
                    "requires_manual_entry": True,
                }
            )

        # Deduplicate based on formatted_address
        seen_addresses = set()
        unique_addresses = []
        for addr in all_addresses:
            addr_key = addr.get("formatted_address", "").lower().strip()
            if addr_key and addr_key not in seen_addresses:
                seen_addresses.add(addr_key)
                unique_addresses.append(addr)

        logger.info(
            f"Found {len(unique_addresses)} unique addresses for postcode: {postcode}"
        )

        return JsonResponse(
            {
                "postcode": postcode,
                "addresses": unique_addresses,
                "total_found": len(unique_addresses),
                "sources_used": list(set(addr["source"] for addr in unique_addresses)),
                "recommendations": {
                    "use_ideal_postcodes": len(ideal_addresses) == 0
                    and len(unique_addresses) < 5,
                    "manual_entry_required": len(unique_addresses) == 0,
                },
            }
        )

    except Exception as e:
        logger.error(
            f"Error in enhanced postcode address lookup: {str(e)}", exc_info=True
        )
        return JsonResponse({"error": "Address lookup failed"}, status=500)


def get_addresses_from_google_text_search(postcode):
    """
    Use Google Places Text Search to find addresses for postcode
    More comprehensive than autocomplete for this use case
    """
    from django.conf import settings

    try:
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            return []

        # Use Text Search to find places in this postcode area
        params = {
            "query": f"addresses in {postcode} UK",
            "key": google_api_key,
            "language": "en",
            "type": "street_address",  # Focus on addresses
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                results = data.get("results", [])
                # Filter to only include results that actually contain our postcode
                filtered_results = []
                for result in results:
                    formatted_address = result.get("formatted_address", "").upper()
                    if postcode.replace(" ", "") in formatted_address.replace(" ", ""):
                        filtered_results.append(result)
                return filtered_results[:20]  # Limit to 20 results

    except Exception as e:
        logger.error(f"Error getting addresses from Google Text Search: {str(e)}")

    return []


def get_addresses_from_geocoding_nearby(postcode):
    """
    Geocode the postcode, then search for nearby addresses
    """
    from django.conf import settings

    try:
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            return []

        # First, geocode the postcode to get coordinates
        geocode_params = {
            "address": postcode,
            "key": google_api_key,
            "components": "country:GB",
        }

        geocode_response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params=geocode_params,
            timeout=10,
        )

        if geocode_response.status_code == 200:
            geocode_data = geocode_response.json()
            if geocode_data.get("status") == "OK" and geocode_data.get("results"):
                location = geocode_data["results"][0]["geometry"]["location"]
                lat, lng = location["lat"], location["lng"]

                # Now search for nearby places
                nearby_params = {
                    "location": f"{lat},{lng}",
                    "radius": 500,  # 500 meter radius
                    "type": "street_address",
                    "key": google_api_key,
                }

                nearby_response = requests.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params=nearby_params,
                    timeout=10,
                )

                if nearby_response.status_code == 200:
                    nearby_data = nearby_response.json()
                    if nearby_data.get("status") == "OK":
                        return nearby_data.get("results", [])[
                            :15
                        ]  # Limit to 15 results

    except Exception as e:
        logger.error(f"Error getting addresses from geocoding + nearby: {str(e)}")

    return []


@csrf_exempt
@require_http_methods(["GET"])
def simple_postcode_addresses(request):
    """
    Simple postcode address lookup using Google Places Autocomplete
    Demonstrates getting multiple addresses for a postcode using the working method
    """
    from django.conf import settings

    try:
        postcode = request.GET.get("postcode", "").strip().upper()
        if not postcode:
            return JsonResponse({"error": "postcode parameter required"}, status=400)

        logger.info(f"Looking up addresses for postcode: {postcode}")

        # Get Google Maps API key from settings
        google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not google_api_key:
            logger.error("Google Maps API key not configured")
            return JsonResponse({"error": "API key not configured"}, status=500)

        # Try different search patterns to get more addresses
        search_patterns = [
            postcode,  # Basic postcode
            f"{postcode} UK",  # Postcode with UK
            f"addresses {postcode}",  # Addresses in postcode
            f"houses {postcode}",  # Houses in postcode
        ]

        all_addresses = []

        for pattern in search_patterns:
            # Build Google Places Autocomplete request
            params = {
                "input": pattern,
                "key": google_api_key,
                "language": "en",
            }

            response = requests.get(
                "https://maps.googleapis.com/maps/api/place/autocomplete/json",
                params=params,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    predictions = data.get("predictions", [])
                    for pred in predictions:
                        # Only include addresses that actually contain our postcode
                        formatted_address = pred.get("description", "").upper()
                        if postcode.replace(" ", "") in formatted_address.replace(
                            " ", ""
                        ):
                            all_addresses.append(
                                {
                                    "source": "google_autocomplete",
                                    "search_pattern": pattern,
                                    "formatted_address": pred.get("description", ""),
                                    "place_id": pred.get("place_id"),
                                    "main_text": pred.get(
                                        "structured_formatting", {}
                                    ).get("main_text", ""),
                                    "secondary_text": pred.get(
                                        "structured_formatting", {}
                                    ).get("secondary_text", ""),
                                    "types": pred.get("types", []),
                                }
                            )

        # Deduplicate based on place_id and formatted_address
        seen_places = set()
        unique_addresses = []
        for addr in all_addresses:
            key = (addr.get("place_id"), addr.get("formatted_address"))
            if key not in seen_places:
                seen_places.add(key)
                unique_addresses.append(addr)

        logger.info(
            f"Found {len(unique_addresses)} unique addresses for postcode: {postcode}"
        )

        return JsonResponse(
            {
                "postcode": postcode,
                "addresses": unique_addresses,
                "total_found": len(unique_addresses),
                "search_patterns_used": search_patterns,
                "note": "This demonstrates getting multiple addresses for a postcode using Google Places Autocomplete",
            }
        )

    except Exception as e:
        logger.error(
            f"Error in simple postcode address lookup: {str(e)}", exc_info=True
        )
        return JsonResponse({"error": f"Address lookup failed: {str(e)}"}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def validate_postcode_comprehensive(request, postcode):
    """
    Comprehensive postcode validation using multiple sources
    """
    try:
        service = PostcodeValidationService()
        result = service.validate_postcode(postcode)

        return Response(result)

    except Exception as e:
        logger.error(
            f"Error in comprehensive postcode validation: {str(e)}", exc_info=True
        )
        return Response(
            {"error": "Postcode validation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_postcode_addresses_comprehensive(request, postcode):
    """
    Get all available addresses for a postcode using multiple sources
    """
    try:
        service = PostcodeValidationService()
        result = service.get_addresses_for_postcode(postcode)

        return Response(result)

    except Exception as e:
        logger.error(
            f"Error in comprehensive postcode address lookup: {str(e)}", exc_info=True
        )
        return Response(
            {"error": "Address lookup failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
