"""
Postcode Validation Services
Simplified service using only Google Maps API for clean, structured address data
"""

import requests
import re
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)


class PostcodeValidationService:
    """
    Simplified postcode validation service using Google Maps API only
    """

    def __init__(self):
        self.google_api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)

    def validate_postcode(self, postcode: str) -> Dict:
        """
        Validate a UK postcode and get structured addresses using Google Maps API

        Args:
            postcode (str): The postcode to validate

        Returns:
            Dict: Validation result with structured addresses
        """
        postcode = self._format_postcode(postcode)

        if not self.google_api_key:
            return {
                "is_valid": False,
                "message": "Google Maps API key not configured",
                "addresses": [],
            }

        try:
            # Use Google Geocoding to validate postcode and get addresses
            addresses = self._get_structured_addresses_from_google(postcode)

            if addresses:
                return {
                    "is_valid": True,
                    "source": "google_maps",
                    "postcode": postcode,
                    "message": f"Postcode is valid. Found {len(addresses)} addresses.",
                    "addresses": addresses,
                    "total_addresses": len(addresses),
                }
            else:
                return {
                    "is_valid": False,
                    "source": "google_maps",
                    "postcode": postcode,
                    "message": "Postcode not found or no addresses available",
                    "addresses": [],
                }

        except Exception as e:
            logger.error(f"Error validating postcode: {str(e)}")
            return {
                "is_valid": False,
                "source": "google_maps",
                "postcode": postcode,
                "message": f"Validation error: {str(e)}",
                "addresses": [],
            }

    def get_addresses_for_postcode(self, postcode: str) -> Dict:
        """
        Get structured addresses for a postcode using Google Maps API

        Args:
            postcode (str): The postcode to lookup

        Returns:
            Dict: Structured addresses and metadata
        """
        postcode = self._format_postcode(postcode)

        if not self.google_api_key:
            return {
                "is_valid": False,
                "message": "Google Maps API key not configured",
                "addresses": [],
            }

        try:
            addresses = self._get_structured_addresses_from_google(postcode)

            return {
                "is_valid": True,
                "postcode": postcode,
                "addresses": addresses,
                "total_found": len(addresses),
                "source": "google_maps",
            }

        except Exception as e:
            logger.error(f"Error getting addresses: {str(e)}")
            return {
                "is_valid": False,
                "postcode": postcode,
                "message": f"Address lookup error: {str(e)}",
                "addresses": [],
            }

    def _format_postcode(self, postcode: str) -> str:
        """Format postcode to standard UK format"""
        postcode = postcode.replace(" ", "").upper()
        if len(postcode) >= 5:
            return postcode[:-3] + " " + postcode[-3:]
        return postcode

    def _get_structured_addresses_from_google(self, postcode: str) -> List[Dict]:
        """
        Get structured addresses from Google Maps API with proper address components
        """
        addresses = []

        try:
            # Method 1: Google Places Autocomplete for the postcode
            places_addresses = self._get_addresses_from_google_places(postcode)
            addresses.extend(places_addresses)

            # Method 2: Google Geocoding for the postcode
            geocoding_addresses = self._get_addresses_from_google_geocoding(postcode)
            addresses.extend(geocoding_addresses)

            # Remove duplicates based on formatted_address
            seen_addresses = set()
            unique_addresses = []

            for addr in addresses:
                addr_key = addr.get("formatted_address", "").lower().strip()
                if addr_key and addr_key not in seen_addresses:
                    seen_addresses.add(addr_key)
                    unique_addresses.append(addr)

            return unique_addresses

        except Exception as e:
            logger.error(f"Error getting structured addresses from Google: {str(e)}")
            return []

    def _get_addresses_from_google_places(self, postcode: str) -> List[Dict]:
        """Get addresses from Google Places Autocomplete API"""
        try:
            params = {
                "input": postcode,
                "key": self.google_api_key,
                "language": "en",
                "components": "country:gb",
                "types": "address",
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

                    addresses = []
                    for pred in predictions:
                        # Get detailed place information
                        place_details = self._get_google_place_details(
                            pred.get("place_id")
                        )
                        if place_details:
                            addresses.append(place_details)

                    return addresses

        except Exception as e:
            logger.error(f"Error getting addresses from Google Places: {str(e)}")

        return []

    def _get_addresses_from_google_geocoding(self, postcode: str) -> List[Dict]:
        """Get addresses from Google Geocoding API"""
        try:
            params = {
                "address": postcode,
                "key": self.google_api_key,
                "components": "country:GB",
                "language": "en",
            }

            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    results = data.get("results", [])

                    addresses = []
                    for result in results:
                        structured_address = self._parse_google_address_components(
                            result
                        )
                        if structured_address:
                            addresses.append(structured_address)

                    return addresses

        except Exception as e:
            logger.error(f"Error getting addresses from Google Geocoding: {str(e)}")

        return []

    def _get_google_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed place information from Google Places API"""
        try:
            params = {
                "place_id": place_id,
                "key": self.google_api_key,
                "fields": "formatted_address,address_components,geometry,name",
                "language": "en",
            }

            response = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params=params,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    result = data.get("result", {})
                    return self._parse_google_address_components(result)

        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")

        return None

    def _parse_google_address_components(self, result: Dict) -> Dict:
        """
        Parse Google address components into structured format
        Returns: Dict with Address Line 1, Address Line 2, City/Town, County, etc.
        """
        try:
            address_components = result.get("address_components", [])
            formatted_address = result.get("formatted_address", "")
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})

            # Initialize structured address
            structured_address = {
                "formatted_address": formatted_address,
                "address_line_1": "",
                "address_line_2": "",
                "city_town": "",
                "county": "",
                "postcode": "",
                "country": "",
                "coordinates": {"lat": location.get("lat"), "lng": location.get("lng")},
                "source": "google_maps",
            }

            # Parse address components
            street_number = ""
            route = ""
            subpremise = ""
            premise = ""
            locality = ""
            administrative_area_level_1 = ""
            administrative_area_level_2 = ""
            postal_code = ""
            country = ""

            for component in address_components:
                types = component.get("types", [])
                long_name = component.get("long_name", "")
                short_name = component.get("short_name", "")

                if "street_number" in types:
                    street_number = long_name
                elif "route" in types:
                    route = long_name
                elif "subpremise" in types:
                    subpremise = long_name
                elif "premise" in types:
                    premise = long_name
                elif "locality" in types:
                    locality = long_name
                elif "administrative_area_level_1" in types:
                    administrative_area_level_1 = long_name
                elif "administrative_area_level_2" in types:
                    administrative_area_level_2 = long_name
                elif "postal_code" in types:
                    postal_code = long_name
                elif "country" in types:
                    country = long_name

            # Build Address Line 1
            address_line_1_parts = []
            if street_number:
                address_line_1_parts.append(street_number)
            if route:
                address_line_1_parts.append(route)

            if address_line_1_parts:
                structured_address["address_line_1"] = " ".join(address_line_1_parts)

            # Build Address Line 2
            address_line_2_parts = []
            if subpremise:
                address_line_2_parts.append(subpremise)
            if premise:
                address_line_2_parts.append(premise)

            if address_line_2_parts:
                structured_address["address_line_2"] = ", ".join(address_line_2_parts)

            # Set other fields
            structured_address["city_town"] = locality or administrative_area_level_2
            structured_address["county"] = administrative_area_level_1
            structured_address["postcode"] = postal_code
            structured_address["country"] = country

            return structured_address

        except Exception as e:
            logger.error(f"Error parsing address components: {str(e)}")
            return None


# Convenience functions for easy use
def validate_postcode(postcode: str) -> Dict:
    """Simple function to validate a postcode"""
    service = PostcodeValidationService()
    return service.validate_postcode(postcode)


def get_addresses_for_postcode(postcode: str) -> Dict:
    """Simple function to get addresses for a postcode"""
    service = PostcodeValidationService()
    return service.get_addresses_for_postcode(postcode)


import os
import requests


def get_distance_and_travel_time(locations, fuel_efficiency_l_per_100km=10.0):
    """
    Get distance and travel time between one or more Location instances or (lat, lon) tuples using OpenRouteService.
    locations: list of Location instances or (lat, lon) tuples
    Returns: dict with 'distance' (miles), 'duration' (seconds), 'unit' ('miles'), and 'estimated_fuel_liters'
    """
    api_key = os.getenv("OPENROUTESERVICE_API_KEY")
    if not api_key:
        raise Exception("OPENROUTESERVICE_API_KEY not set in environment")

    # Prepare coordinates in [lon, lat] format as required by OpenRouteService
    coords = []
    for loc in locations:
        if hasattr(loc, "latitude") and hasattr(loc, "longitude"):
            lat = float(loc.latitude)
            lon = float(loc.longitude)
        else:
            lat, lon = loc
        coords.append([lon, lat])

    print(f"[OpenRouteService] Coordinates sent: {coords}")

    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    body = {"coordinates": coords}
    response = requests.post(url, json=body, headers=headers)
    print(
        f"[OpenRouteService] Raw response: {response.status_code} {response.text[:500]}"
    )
    if response.status_code != 200:
        raise Exception(
            f"OpenRouteService error: {response.status_code} {response.text}"
        )
    data = response.json()
    summary = data["routes"][0]["summary"]
    distance_miles = summary["distance"] / 1609.34
    distance_km = distance_miles * 1.60934
    estimated_fuel_liters = distance_km * (fuel_efficiency_l_per_100km / 100)
    print(
        f"[OpenRouteService] Calculated: {distance_miles:.2f} miles, {summary['duration']} seconds, {estimated_fuel_liters:.2f} liters"
    )
    return {
        "distance": distance_miles,  # in miles
        "duration": summary["duration"],  # in seconds
        "unit": "miles",
        "estimated_fuel_liters": estimated_fuel_liters,
    }
