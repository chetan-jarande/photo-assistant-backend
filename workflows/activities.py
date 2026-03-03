# from temporalio import activity
from typing import List, Dict, Any


# Mock decorator
class activity:
    @staticmethod
    def defn(func):
        return func


@activity.defn
async def ingest_photo(photo_path: str) -> Dict[str, Any]:
    """
    Ingest a single photo: extract metadata, generate vectors, store in DB.
    """
    # TODO: Implement full ingestion pipeline
    # 1. Extract metadata
    # 2. Upload to storage (S3/MinIO)
    # 3. Generate embeddings
    # 4. Save to SurrealDB

    return {"status": "success", "id": "photo_123", "path": photo_path}


@activity.defn
async def generate_vector_batch(photo_ids: List[str]) -> int:
    """
    Generate vectors for a batch of photos.
    """
    # TODO: Implement batch vector generation
    return len(photo_ids)


@activity.defn
async def reverse_geocode_batch(photo_ids: List[str]) -> int:
    """
    Reverse geocode a batch of photos.
    """
    # TODO: Implement batch reverse geocoding
    return len(photo_ids)
