from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum

class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class MediaItem(BaseModel):
    id: str
    url: str # Raw CDN URL
    thumbnail: Optional[str] = None
    type: MediaType
    source_url: str

class AnalyzeRequest(BaseModel):
    urls: List[HttpUrl]
    format_type: str = "video"
    is_playlist: bool = False
    platform: str = "auto"
    media_filter: str = "all"

class AnalyzeResponse(BaseModel):
    source_url: str
    items: List[MediaItem]
    error: Optional[str] = None

class DownloadRequest(BaseModel):
    url: HttpUrl
    tier: Optional[int] = 1

class BatchDownloadRequest(BaseModel):
    urls: List[HttpUrl]
    enhance_images: bool = False
    color_boost: bool = False
    format_type: str = "video"
    is_playlist: bool = False
    platform: str = "auto"
    media_filter: str = "all"

class CookieSaveRequest(BaseModel):
    cookie_content: str

class CookieSaveResponse(BaseModel):
    message: str

class DownloadProgress(BaseModel):
    id: str
    url: str
    status: DownloadStatus
    progress_percentage: float = 0.0
    speed_mbps: float = 0.0
    eta_seconds: Optional[int] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    tier_used: int = 1
