import asyncio
from typing import Callable, Optional
from domain.exceptions import ExtractionFailedException, RateLimitException, LoginRequiredException
from infrastructure.ytdlp_engine import YTDLPEngine
from infrastructure.playwright_sniffer import PlaywrightSniffer
from infrastructure.local_cookie_manager import LocalCookieManager

class DownloadMediaUseCase:
    """Orchestrates the 4-Tier Fallback Cascade execution logic."""
    
    def __init__(self, output_dir: str):
        self.ytdlp = YTDLPEngine(output_dir)
        self.sniffer = PlaywrightSniffer()
        self.cookie_manager = LocalCookieManager()
        
    async def execute(self, url: str, progress_hook: Optional[Callable] = None) -> str:
        """
        Executes the 4-tier download strategy.
        Returns the path to the downloaded file.
        """
        last_error = None
        # Tier 1: Fast-Path `yt-dlp`
        try:
            return self.ytdlp.extract(url, progress_hook=progress_hook)
        except (ExtractionFailedException, RateLimitException, LoginRequiredException) as e:
            last_error = e

        # Check if login is required (Tier 3)
        if isinstance(last_error, LoginRequiredException):
            try:
                # Tier 3: Local Cookie Bridge
                return self.ytdlp.extract(url, progress_hook=progress_hook, use_cookies=True)
            except Exception as e:
                pass
                
        # Tier 2: Stealth Network Interceptor `Playwright`
        try:
            sniffed_url = await self.sniffer.sniff_media_url(url)
            # Use Tier 1 to download the raw CDN URL
            return self.ytdlp.extract(sniffed_url, progress_hook=progress_hook)
        except Exception as e:
            # If all tiers fail, raise the original error or a generic one
            raise ExtractionFailedException(f"All extraction tiers failed for {url}. Last error: {str(e)}", url, 4)
