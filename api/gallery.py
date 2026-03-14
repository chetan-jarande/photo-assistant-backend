from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import List, Optional, Annotated
import random
from datetime import datetime
from enum import Enum
import os

from fastapi import APIRouter, Query, HTTPException, Depends
from googleapiclient.errors import HttpError
from core.config import settings
from utils.google_drive import GoogleDriveClient, get_drive_client

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
    "/picsum-photos",
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
    description="Endpoint to fetch actual sub-folders and images from the configured Google Drive root folder.",
)
async def get_drive_assets(drive_client: GoogleDriveClient = Depends(get_drive_client)):
    """
    Dynamically fetches structured data from the Google Drive root folder using Service Account credentials.
    """
    # 1. Fetch sub-folders within the root folder
    folders = drive_client.get_subfolders(settings.DRIVE_ROOT_FOLDER_ID)
    assets_list = []

    # 2. Iterate over folders and fetch their images
    for folder in folders:
        images = drive_client.get_images_in_folder(folder["id"])

        for img in images:
            # Handle missing links gracefully if Drive didn't generate them
            thumbnail_link = img.get("thumbnailLink", "")
            original_link = img.get("webContentLink", f"https://drive.google.com/uc?export=view&id={img['id']}")

            asset = GoogleDriveAsset(
                _id=f"{folder['id']}_{img['id']}",
                folderId=folder["id"],
                folderName=folder.get("name", "Unknown"),
                folderUpdatedAt=folder.get("modifiedTime", datetime.now()),
                folderCreatedTime=folder.get("createdTime", datetime.now()),
                folderMimeType=folder.get("mimeType", MimeTypeEnum.FOLDER),
                imgId=img["id"],
                imgThumbnailLink=thumbnail_link,
                imgOriginalLink=original_link,
                imgCreatedTime=img.get("createdTime", datetime.now()),
                imgMimeType=img.get("mimeType", MimeTypeEnum.JPEG),
            )
            assets_list.append(asset)

    return assets_list


class Section(BaseModel):
    id: str = Field(..., title="Folder ID", description="The ID of the folder")
    name: str = Field(..., title="Folder Name", description="The name of the section")
    coverImage: Optional[GalleryImage] = Field(None, title="Cover Image", description="A representative image for the section cover")
    updatedAt: datetime = Field(..., title="Updated At", description="Timestamp when the folder was last modified")


@gallery_router.get(
    "/sections",
    response_model=List[Section],
    summary="Get Gallery Sections",
    description="Fetch all category folders from the Google Drive root folder and their cover images.",
)
async def get_sections(drive_client: GoogleDriveClient = Depends(get_drive_client)):
    """
    Fetches the sub-folders (sections) from the root Google Drive directory.
    """
    folders = drive_client.get_subfolders(settings.DRIVE_ROOT_FOLDER_ID)
    sections = []
    
    for folder in folders:
        # Fetch just 1 image for the cover
        query = f"'{folder['id']}' in parents and mimeType contains 'image/' and trashed=false"
        fields = "files(id, name, createdTime, mimeType, thumbnailLink, webContentLink, imageMediaMetadata)"
        images = drive_client.list_files(query, fields=fields, page_size=1)
        
        cover_image = None
        if images:
            img = images[0]
            metadata = img.get("imageMediaMetadata", {})
            width = int(metadata.get("width", 800))
            height = int(metadata.get("height", 600))
            
            cover_image = GalleryImage(
                id=img["id"],
                url=img.get("webContentLink", img.get("thumbnailLink", "")),
                width=width,
                height=height,
                aspectRatio=width / height if height > 0 else 1.33,
                title=img.get("name", "Untitled"),
                author="Google Drive",
                date=img.get("createdTime", datetime.now().isoformat())
            )
            
        sections.append(
            Section(
                id=folder["id"],
                name=folder.get("name", "Unknown"),
                coverImage=cover_image,
                updatedAt=folder.get("modifiedTime", datetime.now())
            )
        )

    return sections


@gallery_router.get(
    "/sections/{folder_id}/images",
    response_model=PaginatedImagesResponse,
    summary="Get Section Images",
    description="Fetch a paginated list of images from a specific Google Drive folder.",
)
async def get_section_images(
    folder_id: str,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 15,
    drive_client: GoogleDriveClient = Depends(get_drive_client)
):
    """
    Get paginated gallery images from a specific Google Drive folder.
    """
    all_images = drive_client.get_images_in_folder(folder_id)
    
    # Calculate pagination indices
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    if start_index >= len(all_images):
        return PaginatedImagesResponse(data=[], hasMore=False, nextCursor=None)
        
    paginated_images = all_images[start_index:end_index]
    
    fetched_data = []
    for img in paginated_images:
        metadata = img.get("imageMediaMetadata", {})
        width = int(metadata.get("width", 800))
        height = int(metadata.get("height", 600))
        
        fetched_data.append(
            GalleryImage(
                id=img["id"],
                url=img.get("webContentLink", img.get("thumbnailLink", "")),
                width=width,
                height=height,
                aspectRatio=width / height if height > 0 else 1.33,
                title=img.get("name", "Untitled"),
                author="Google Drive",
                date=img.get("createdTime", datetime.now().isoformat())
            )
        )

    has_more = end_index < len(all_images)
    next_cursor = page + 1 if has_more else None

    return PaginatedImagesResponse(data=fetched_data, hasMore=has_more, nextCursor=next_cursor)

