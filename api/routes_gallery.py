from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from core.security import get_current_user, TokenData
# from database.surreal_client import surreal_client

router = APIRouter()


class PhotoAsset(BaseModel):
    id: str
    filename: str
    url: str
    location: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class PhotoCreate(BaseModel):
    filename: str
    url: str
    metadata: Optional[Dict[str, Any]] = None


@router.get("/photos", response_model=List[PhotoAsset])
async def list_photos(
    skip: int = 0, limit: int = 20, current_user: TokenData = Depends(get_current_user)
):
    """
    List photos for the current user.
    """
    # TODO: Fetch from SurrealDB
    # query = f"SELECT * FROM photo WHERE user_id = '{current_user.user_id}' LIMIT {limit} START {skip}"
    # result = await surreal_client.query(query)

    # Mock return
    return [
        PhotoAsset(
            id="photo_1",
            filename="vacation.jpg",
            url="https://mock.com/vacation.jpg",
            location="Hawaii",
            tags=["beach", "sunset"],
        ),
        PhotoAsset(
            id="photo_2",
            filename="family.jpg",
            url="https://mock.com/family.jpg",
            location="Home",
            tags=["family", "dinner"],
        ),
    ]


@router.post("/photos", response_model=PhotoAsset)
async def upload_photo(
    photo: PhotoCreate, current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new photo asset (metadata only for now).
    """
    # TODO: Create in SurrealDB

    return PhotoAsset(
        id="photo_new",
        filename=photo.filename,
        url=photo.url,
        metadata=photo.metadata or {},
    )


@router.get("/photos/{photo_id}", response_model=PhotoAsset)
async def get_photo(photo_id: str, current_user: TokenData = Depends(get_current_user)):
    """
    Get details of a specific photo.
    """
    # TODO: Fetch from SurrealDB

    if photo_id == "photo_1":
        return PhotoAsset(
            id="photo_1",
            filename="vacation.jpg",
            url="https://mock.com/vacation.jpg",
            location="Hawaii",
            tags=["beach", "sunset"],
        )

    raise HTTPException(status_code=404, detail="Photo not found")


@router.delete("/photos/{photo_id}")
async def delete_photo(
    photo_id: str, current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a photo.
    """
    # TODO: Delete from SurrealDB
    return {"status": "success", "id": photo_id}
