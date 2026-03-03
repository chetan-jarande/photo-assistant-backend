from typing import Dict, Any, Optional
# from PIL import Image, ExifTags # Uncomment when Pillow is installed


def extract_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extracts metadata from an image file, including EXIF data and dimensions.

    Args:
        image_path: Path to the image file.

    Returns:
        A dictionary containing extracted metadata.
    """
    metadata = {
        "width": 0,
        "height": 0,
        "camera_make": None,
        "camera_model": None,
        "iso": None,
        "aperture": None,
        "shutter_speed": None,
        "date_taken": None,
        "gps_latitude": None,
        "gps_longitude": None,
    }

    # TODO: Implement actual extraction using Pillow
    # with Image.open(image_path) as img:
    #     metadata["width"], metadata["height"] = img.size
    #     exif_data = img._getexif()
    #     # ... process exif tags ...

    # Mock return for now
    metadata["width"] = 1920
    metadata["height"] = 1080
    metadata["camera_make"] = "Sony"
    metadata["camera_model"] = "a7III"
    metadata["iso"] = 100
    metadata["aperture"] = "f/2.8"
    metadata["date_taken"] = "2023-10-15T14:30:00"

    return metadata
