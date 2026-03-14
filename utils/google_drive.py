import os
from functools import lru_cache
from typing import List, Dict, Any
from fastapi import HTTPException
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class GoogleDriveClient:
    """
    A utility class to handle interactions with Google Drive API.
    """

    def __init__(self):
        if not os.path.exists(settings.DRIVE_CREDENTIALS_PATH):
            logger.error(f"Credentials not found at {settings.DRIVE_CREDENTIALS_PATH}")
            raise HTTPException(
                status_code=500, detail=f"Google Drive credentials file not found at {settings.DRIVE_CREDENTIALS_PATH}."
            )
        try:
            scopes = ["https://www.googleapis.com/auth/drive.readonly"]
            creds = service_account.Credentials.from_service_account_file(
                settings.DRIVE_CREDENTIALS_PATH, scopes=scopes
            )
            self.service = build("drive", "v3", credentials=creds)
        except Exception as e:
            logger.exception("Failed to initialize Google Drive client")
            raise HTTPException(status_code=500, detail="Failed to initialize Google Drive client")

    def list_files(
        self, query: str, fields: str = "files(id, name, modifiedTime, createdTime, mimeType)", page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Executes a file list query against the Google Drive API.
        """
        try:
            results = self.service.files().list(q=query, fields=fields, pageSize=page_size).execute()
            return results.get("files", [])
        except HttpError as e:
            logger.error(f"Google Drive API HTTP error: {e.reason}")
            raise HTTPException(status_code=502, detail=f"Google Drive API error: {e.reason}")
        except Exception as e:
            logger.error(f"Error querying Google Drive: {e}")
            raise HTTPException(status_code=500, detail=f"Error querying Google Drive: {str(e)}")

    def get_subfolders(self, parent_folder_id: str) -> List[Dict[str, Any]]:
        """
        Fetches all subfolders for a given parent folder ID.
        """
        query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        return self.list_files(query)

    def get_images_in_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Fetches all image files within a specific folder ID, handling pagination internally to return all images.
        """
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
        fields = "files(id, name, createdTime, mimeType, thumbnailLink, webContentLink, imageMediaMetadata)"
        
        all_files = []
        page_token = None
        
        while True:
            try:
                results = self.service.files().list(
                    q=query, fields=f"nextPageToken, {fields}", pageSize=100, pageToken=page_token
                ).execute()
                all_files.extend(results.get("files", []))
                page_token = results.get("nextPageToken")
                if not page_token:
                    break
            except HttpError as e:
                logger.error(f"Google Drive API HTTP error: {e.reason}")
                raise HTTPException(status_code=502, detail=f"Google Drive API error: {e.reason}")
            except Exception as e:
                logger.error(f"Error querying Google Drive: {e}")
                raise HTTPException(status_code=500, detail=f"Error querying Google Drive: {str(e)}")
                
        return all_files


@lru_cache()
def get_drive_client() -> GoogleDriveClient:
    """
    Returns a cached (singleton) instance of the GoogleDriveClient.
    This prevents re-reading credentials and re-building the discovery service on every request.
    """
    return GoogleDriveClient()
