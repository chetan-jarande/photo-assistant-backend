from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import List, Optional, Annotated
import random
from datetime import datetime
from enum import Enum

# Google Drive Dependencies
from googleapiclient.discovery import build
from google.oauth2 import service_account

gallery_router = APIRouter(prefix="/gallery", tags=["Gallery"])


class GalleryImage(BaseModel):
    id: str = Field(
        ..., title="Image ID", description="Unique identifier for the UI gallery component", examples=["img-123"]
    )
    url: HttpUrl = Field(
        ...,
        title="Image URL",
        description="Direct URL to the image to render",
        examples=["https://picsum.photos/800/600"],
    )
    width: int = Field(
        ...,
        title="Width",
        description="Width of the image in pixels",
        gt=0,
        examples=[800],
    )
    height: int = Field(
        ...,
        title="Height",
        description="Height of the image in pixels",
        gt=0,
        examples=[600],
    )
    aspectRatio: float = Field(
        ...,
        title="Aspect Ratio",
        description="Calculated aspect ratio (width / height)",
        gt=0,
        examples=[1.333],
    )
    title: str = Field(
        ...,
        title="Title",
        description="Display title for the image",
        examples=["Sunset Boulevard"],
    )
    author: str = Field(
        ...,
        title="Author",
        description="Author or photographer of the image",
        examples=["Creator 42"],
    )
    date: str = Field(
        ...,
        title="Date",
        description="Formatted date string for UI display",
        examples=["10/25/2023"],
    )


class PaginatedImagesResponse(BaseModel):
    data: List[GalleryImage] = Field(
        ...,
        title="Data",
        description="Array of images for the current page",
    )
    hasMore: bool = Field(
        ...,
        title="Has More",
        description="Boolean indicating if more pages are available",
        examples=[True],
    )
    nextCursor: Optional[int] = Field(
        default=None,
        title="Next Cursor",
        description="The cursor (page number) to use for the next request",
        examples=[2],
    )


@gallery_router.get(
    "/images",
    response_model=PaginatedImagesResponse,
    summary="Get Paginated Images",
    description="Fetch a paginated list of generated/curated gallery images for the UI.",
)
async def get_paginated_images(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 15,
    max_items_allowed: Annotated[
        int, Query(alias="maxItemsAllowed", description="Max items allowed across all pages")
    ] = -1,
):
    """
    Get paginated gallery images for the UI.
    """
    SERVER_MAX_PAGES = 8
    start_index = (page - 1) * limit

    if page > SERVER_MAX_PAGES:
        return PaginatedImagesResponse(data=[], hasMore=False, nextCursor=None)

    items_to_fetch = limit
    if max_items_allowed != -1:
        if start_index >= max_items_allowed:
            return PaginatedImagesResponse(data=[], hasMore=False, nextCursor=None)
        if start_index + limit > max_items_allowed:
            items_to_fetch = max_items_allowed - start_index

    fetched_data = []
    for idx in range(items_to_fetch):
        img_id = start_index + idx
        random_width = random.randint(600, 1200)
        random_height = random.randint(400, 1000)

        fetched_data.append(
            GalleryImage(
                id=f"img-{img_id}",
                url=f"https://picsum.photos/{random_width}/{random_height}?random={img_id}",
                width=random_width,
                height=random_height,
                aspectRatio=random_width / random_height,
                title=f"Curated Asset #{img_id + 1}",
                author=f"Creator {random.randint(1, 100)}",
                date=datetime.now().strftime("%m/%d/%Y"),
            )
        )

    has_more = True
    if page >= SERVER_MAX_PAGES:
        has_more = False
    if max_items_allowed != -1 and start_index + items_to_fetch >= max_items_allowed:
        has_more = False

    next_cursor = page + 1 if has_more else None

    return PaginatedImagesResponse(data=fetched_data, hasMore=has_more, nextCursor=next_cursor)


class MimeTypeEnum(str, Enum):
    """Enumeration of supported MIME types from Google Drive."""

    FOLDER = "application/vnd.google-apps.folder"
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"


class GoogleDriveAsset(BaseModel):
    id: str = Field(
        ...,
        alias="_id",
        title="Asset ID",
        description="Unique identifier for the asset record",
        examples=["13lP1m2LQZYi91B8-6LdqMb1T63aKcRCy"],
    )
    folderId: str = Field(
        ...,
        title="Folder ID",
        description="Google Drive ID of the parent folder",
        examples=["13lP1m2LQZYi91B8-6LdqMb1T63aKcRCy"],
    )
    folderName: str = Field(
        ...,
        title="Folder Name",
        description="Name of the parent category folder",
        examples=["Sky", "Portraits"],
    )
    folderUpdatedAt: datetime = Field(
        ...,
        title="Folder Updated At",
        description="Timestamp when the folder was last modified",
    )
    folderCreatedTime: datetime = Field(
        ...,
        title="Folder Created Time",
        description="Timestamp when the folder was created",
    )
    folderMimeType: MimeTypeEnum = Field(
        default=MimeTypeEnum.FOLDER,
        title="Folder MIME Type",
        description="MIME type of the folder",
    )

    imgId: str = Field(
        ...,
        title="Image ID",
        description="Google Drive ID of the image file",
        examples=["14Ut2D3TGkP8QxIIqS999JPhgpJN-MJyy"],
    )
    imgThumbnailLink: HttpUrl = Field(
        ...,
        title="Image Thumbnail Link",
        description="Direct link to a compressed thumbnail of the image",
        examples=["https://lh3.googleusercontent.com/drive-storage/..."],
    )
    imgOriginalLink: HttpUrl = Field(
        ...,
        title="Image Original Link",
        description="Link to view or download the original image",
        examples=["https://drive.google.com/uc?export=view&id=..."],
    )
    imgCreatedTime: datetime = Field(
        ...,
        title="Image Created Time",
        description="Timestamp when the image was uploaded/created",
    )
    imgMimeType: MimeTypeEnum = Field(
        ...,
        title="Image MIME Type",
        description="MIME type of the image file",
        examples=[MimeTypeEnum.JPEG],
    )

    model_config = ConfigDict(populate_by_name=True)


@gallery_router.get(
    "/drive-assets",
    response_model=List[GoogleDriveAsset],
    summary="Get Drive Assets",
    description="Endpoint to return data structured from a Google Drive folder as requested.",
)
async def get_drive_assets():
    """
    Dummy endpoint to return data structured from Google Drive folder as requested.
    """
    return [
        GoogleDriveAsset(
            _id="13lP1m2LQZYi91B8-6LdqMb1T63aKcRCy",
            folderId="13lP1m2LQZYi91B8-6LdqMb1T63aKcRCy",
            folderName="Sky",
            folderUpdatedAt="2023-09-16T13:53:25.026Z",
            folderCreatedTime="2023-10-23T17:49:53.328Z",
            folderMimeType="application/vnd.google-apps.folder",
            imgId="14Ut2D3TGkP8QxIIqS999JPhgpJN-MJyy",
            imgThumbnailLink="https://lh3.googleusercontent.com/drive-storage/AKHj6E6Mc3LYr9eij0zK1L2bf8my8cOyHINbsYj0SO74iVvcl6rIyIrKn1uGJA2NXR4rDyi2hEMNW2woBcuocjROwrVryNYssWveHBoYLXy9=s220",
            imgOriginalLink="https://drive.google.com/uc?export=view&id=14Ut2D3TGkP8QxIIqS999JPhgpJN-MJyy",
            imgCreatedTime="2023-09-16T13:53:25.026Z",
            imgMimeType="image/jpeg",
        )
    ]
