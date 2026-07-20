from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum

class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DownloadRequest(BaseModel):
    url: HttpUrl
    tier: Optional[int] = 1 # Start at Tier 1 by default

class BatchDownloadRequest(BaseModel):
    urls: List[HttpUrl]

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
