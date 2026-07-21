import yt_dlp
import os
import logging
import asyncio
from typing import Callable, Optional, Dict, Any
from domain.interfaces import IExtractorEngine
from domain.exceptions import ExtractionFailedException, RateLimitException, LoginRequiredException
from infrastructure.stealth_utils import get_random_user_agent

class YTDLPEngine(IExtractorEngine):
    """Tier 1: Fast-Path non-rendered extractor using yt-dlp."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)

    def extract(self, url: str, progress_hook: Optional[Callable[[Dict], None]] = None, use_cookies: bool = False, cookies_path: Optional[str] = None, format_type: str = "video", is_playlist: bool = False, platform: str = "auto", media_filter: str = "all") -> str:
        """
        Extracts media from URL.
        Returns the path to the downloaded file.
        """
        is_audio = format_type == "audio"
        
        # Force playlist extraction for specific platforms to handle carousels/threads
        force_playlist = is_playlist
        if platform in ['instagram', 'tiktok', 'x', 'twitter']:
            force_playlist = True
            
        ydl_opts = {
            'format': 'bestaudio/best' if is_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'noplaylist': not force_playlist,
            'quiet': True,
            'no_warnings': True,
            # Stealth & Anti-Ban Options
            'http_headers': {'User-Agent': get_random_user_agent()},
            'extractor_args': {'youtube': ['player_client=android,web']},
            'geo_bypass': True,
            'sleep_interval_requests': 1,
            'sleep_interval': 2,
            'max_sleep_interval': 6,
        }
        
        if is_audio:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['merge_output_format'] = 'mp4'

        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        elif use_cookies:
            # Try Chrome cookies fallback
            ydl_opts['cookiesfrombrowser'] = ('chrome', )

        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]

        # Apply Platform Specific Filters
        if platform == "instagram":
            def ig_filter(info, *, incomplete):
                # info is the dict of the current media
                # Determine type based on extension or vcodec
                ext = info.get('ext', '')
                vcodec = info.get('vcodec')
                is_image = ext in ['jpg', 'jpeg', 'png', 'webp'] or vcodec == 'none'
                
                if media_filter == "reels" and is_image:
                    return "Skipping image (Reels/Videos only requested)"
                if media_filter == "images" and not is_image:
                    return "Skipping video (Images only requested)"
                return None # None means accept
            
            ydl_opts['match_filter'] = ig_filter

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                if not info_dict:
                    raise ExtractionFailedException("Failed to extract info", url, 1)
                
                # The actual file path might have changed after merging/postprocessing
                expected_filename = ydl.prepare_filename(info_dict)
                
                if is_audio:
                    base_name = expected_filename.rsplit('.', 1)[0]
                    if os.path.exists(base_name + '.mp3'):
                        return base_name + '.mp3'
                else:
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

    async def analyze(self, url: str, use_cookies: bool = False, cookies_path: Optional[str] = None, is_playlist: bool = False, platform: str = "auto", media_filter: str = "all") -> Dict[str, Any]:
        """Extracts metadata without downloading. Returns the info_dict."""
        # Force playlist extraction for specific platforms to handle carousels/threads
        force_playlist = is_playlist
        if platform in ['instagram', 'tiktok', 'x', 'twitter']:
            force_playlist = True
            
        ydl_opts = {
            'noplaylist': not force_playlist,
            'quiet': True,
            'no_warnings': True,
            # Stealth & Anti-Ban Options
            'http_headers': {'User-Agent': get_random_user_agent()},
            'extractor_args': {'youtube': ['player_client=android,web']},
            'geo_bypass': True,
            'sleep_interval_requests': 1,
            'sleep_interval': 2,
            'max_sleep_interval': 6,
        }
        
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        elif use_cookies:
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
