from typing import Tuple, Dict, Any, Optional


def get_location_info(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Reverse geocodes GPS coordinates to get human-readable location.

    Args:
        latitude: The latitude coordinate.
        longitude: The longitude coordinate.

    Returns:
        A dictionary with location details (e.g., city, country).
    """
    location_info = {"city": None, "country": None, "full_address": None}

    # TODO: Implement reverse geocoding using an external service or library (e.g., geopy, Google Maps API)
    # geolocator = Nominatim(user_agent="photo_assistant")
    # location = geolocator.reverse((latitude, longitude))

    # Mock return
    if latitude == 0 and longitude == 0:
        return location_info

    location_info["city"] = "San Francisco"
    location_info["country"] = "USA"
    location_info["full_address"] = "1 Market St, San Francisco, CA"

    return location_info
