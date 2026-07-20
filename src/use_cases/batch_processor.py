import asyncio
from typing import List, Callable, Dict
from use_cases.download_media import DownloadMediaUseCase
from use_cases.local_storage import LocalStorage

class BatchProcessor:
    """Concurrent multi-threaded download queue manager."""
    
    def __init__(self, storage: LocalStorage):
        self.downloader = DownloadMediaUseCase(storage.get_download_path())
        self.tasks: Dict[str, asyncio.Task] = {}
        
    async def process_batch(self, urls: List[str], progress_callback: Callable):
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
                    
            coro = self._download_single(url, task_id, hook, progress_callback)
            task = asyncio.create_task(coro)
            self.tasks[task_id] = task
            coroutines.append(task)
            
        await asyncio.gather(*coroutines, return_exceptions=True)
        
    async def _download_single(self, url: str, task_id: str, hook: Callable, callback: Callable):
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
            
            loop = asyncio.get_running_loop()
            file_path = await loop.run_in_executor(None, self._run_sync_download, url, hook)
            
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

    def _run_sync_download(self, url, hook):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(self.downloader.execute(url, progress_hook=hook))
        finally:
            new_loop.close()
