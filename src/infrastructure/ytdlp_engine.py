import yt_dlp
import os
import logging
import asyncio
from typing import Callable, Optional, Dict, Any
from domain.interfaces import IExtractorEngine
from domain.exceptions import ExtractionFailedException, RateLimitException, LoginRequiredException

class YTDLPEngine(IExtractorEngine):
    """Tier 1: Fast-Path non-rendered extractor using yt-dlp."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)

    def extract(self, url: str, progress_hook: Optional[Callable[[Dict], None]] = None, use_cookies: bool = False) -> str:
        """
        Extracts media from URL.
        Returns the path to the downloaded file.
        """
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        if use_cookies:
            # Try Chrome cookies
            ydl_opts['cookiesfrombrowser'] = ('chrome', )

        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                if not info_dict:
                    raise ExtractionFailedException("Failed to extract info", url, 1)
                
                # The actual file path might have changed after merging
                expected_filename = ydl.prepare_filename(info_dict)
                # yt-dlp appends .mp4 if merge_output_format is set and it merged
                if not expected_filename.endswith('.mp4') and os.path.exists(expected_filename.rsplit('.', 1)[0] + '.mp4'):
                     return expected_filename.rsplit('.', 1)[0] + '.mp4'
                
                return expected_filename
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            self.logger.warning(f"yt-dlp extraction failed for {url}: {error_msg}")
            if 'http error 429' in error_msg:
                raise RateLimitException(f"Rate limit hit for {url}")
            elif 'sign in' in error_msg or 'login' in error_msg or 'private' in error_msg:
                raise LoginRequiredException(f"Login required for {url}")
            else:
                raise ExtractionFailedException(str(e), url, 1)

    async def analyze(self, url: str, use_cookies: bool = False) -> Dict[str, Any]:
        """Extracts metadata without downloading. Returns the info_dict."""
        ydl_opts = {
            'noplaylist': False, # Allow playlist/carousel extraction
            'quiet': True,
            'no_warnings': True,
        }
        
        if use_cookies:
            ydl_opts['cookiesfrombrowser'] = ('chrome', )
            
        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(None, _extract)
            return info
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            self.logger.error(f"yt-dlp analyze failed for {url}: {error_msg}")
            if 'http error 429' in error_msg:
                raise RateLimitException(f"Rate limit hit for {url}")
            elif 'sign in' in error_msg or 'login' in error_msg or 'private' in error_msg:
                raise LoginRequiredException(f"Login required for {url}")
            else:
                raise ExtractionFailedException(str(e), url, 1)
