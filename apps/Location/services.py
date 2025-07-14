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
