from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class SearchByLocationInput(BaseModel):
    location_name: str = Field(
        ...,
        description="Name of the location to search for (e.g., 'Paris', 'Central Park').",
    )
    radius_km: int = Field(
        default=10, description="Radius in kilometers around the location to search."
    )


@tool("search_by_location", args_schema=SearchByLocationInput)
def search_by_location(location_name: str, radius_km: int = 10) -> List[Dict[str, Any]]:
    """
    Search for photos taken at or near a specific location.

    This tool converts the location name to coordinates (using geolocation service)
    and queries the database for photos within the specified radius.
    """
    # TODO: Implement geolocation service integration (Phase 4)
    # TODO: Implement SurrealDB query
    return [{"id": "mock_photo_1", "location": location_name, "distance_km": 0.5}]


class FilterByCameraSettingsInput(BaseModel):
    iso: Optional[int] = Field(
        None, description="ISO value to filter by (exact match or range logic)."
    )
    aperture: Optional[str] = Field(
        None, description="Aperture value to filter by (e.g., 'f/1.8')."
    )
    shutter_speed: Optional[str] = Field(
        None, description="Shutter speed to filter by (e.g., '1/1000')."
    )
    camera_model: Optional[str] = Field(
        None, description="Camera model name to filter by."
    )


@tool("filter_by_camera_settings", args_schema=FilterByCameraSettingsInput)
def filter_by_camera_settings(
    iso: Optional[int] = None,
    aperture: Optional[str] = None,
    shutter_speed: Optional[str] = None,
    camera_model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter photos based on technical camera settings (EXIF data).

    Allows searching for photos taken with specific settings like low light (high ISO),
    shallow depth of field (low f-stop), or fast action (high shutter speed).
    """
    # TODO: Implement SurrealDB query with filters
    return [{"id": "mock_photo_2", "iso": iso or 100, "aperture": aperture or "f/2.8"}]
