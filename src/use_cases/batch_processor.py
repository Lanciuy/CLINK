import asyncio
import logging
from typing import List, Callable, Dict
from use_cases.download_media import DownloadMediaUseCase
from domain.exceptions import ConcurrencyException

class BatchProcessor:
    """Concurrent multi-threaded download queue manager."""
    
    def __init__(self, downloader: DownloadMediaUseCase, max_concurrent: int = 5):
        self.downloader = downloader
        self.tasks: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)
        
    async def process_batch(self, urls: List[str], progress_callback: Callable[[Dict], None], enhance_images: bool = False, color_boost: bool = False, format_type: str = "video", is_playlist: bool = False, platform: str = "auto", media_filter: str = "all"):
        """
        Processes a list of URLs concurrently.
        """
        coroutines = []
        for url in urls:
            task_id = str(hash(url))
            
            def hook(d, url_capture=url, t_id=task_id):
                if d['status'] == 'downloading':
                    progress = 0
                    if d.get('total_bytes'):
                        progress = d['downloaded_bytes'] / d['total_bytes'] * 100
                    elif d.get('total_bytes_estimate'):
                         progress = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                         
                    speed = d.get('speed', 0)
                    speed_mbps = (speed / 1024 / 1024) if speed else 0
                    eta = d.get('eta', 0)
                    
                    progress_callback({
                        "id": t_id,
                        "url": url_capture,
                        "status": "downloading",
                        "progress_percentage": progress,
                        "speed_mbps": speed_mbps,
                        "eta_seconds": eta,
                        "tier_used": 1
                    })
                elif d['status'] == 'finished':
                     progress_callback({
                        "id": t_id,
                        "url": url_capture,
                        "status": "processing",
                        "progress_percentage": 100,
                        "speed_mbps": 0,
                        "eta_seconds": 0,
                        "tier_used": 1
                    })
                    
            coro = self._download_single(url, task_id, hook, progress_callback, enhance_images, color_boost, format_type, is_playlist, platform, media_filter)
            task = asyncio.create_task(coro)
            self.tasks[task_id] = task
            coroutines.append(task)
            
        await asyncio.gather(*coroutines, return_exceptions=True)
        
    async def _download_single(self, url: str, task_id: str, hook: Callable, callback: Callable, enhance_images: bool, color_boost: bool, format_type: str, is_playlist: bool, platform: str, media_filter: str):
        async with self.semaphore:
            try:
                callback({
                    "id": task_id,
                    "url": url,
                    "status": "pending",
                    "progress_percentage": 0,
                    "speed_mbps": 0,
                    "eta_seconds": None,
                    "tier_used": 1
                })
                
                file_path = await self.downloader.execute(
                    url, 
                    progress_callback=hook, 
                    enhance_images=enhance_images,
                    color_boost=color_boost,
                    format_type=format_type,
                    is_playlist=is_playlist,
                    platform=platform,
                    media_filter=media_filter
                )
                
                callback({
                    "id": task_id,
                    "url": url,
                    "status": "completed",
                    "progress_percentage": 100,
                    "speed_mbps": 0,
                    "eta_seconds": 0,
                    "file_path": file_path,
                    "tier_used": 1
                })
                
            except Exception as e:
                self.logger.error(f"Download task {task_id} failed: {e}")
                callback({
                    "id": task_id,
                    "url": url,
                    "status": "failed",
                    "progress_percentage": 0,
                    "speed_mbps": 0,
                    "eta_seconds": 0,
                    "error_message": str(e),
                    "tier_used": 1
                })

