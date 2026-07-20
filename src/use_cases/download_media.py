import asyncio
import logging
from typing import Callable, Optional, Dict
from domain.exceptions import ExtractionFailedException, RateLimitException, LoginRequiredException, SnifferException, RemuxingException
from domain.interfaces import IExtractorEngine, ISniffer, ICookieManager, IRemuxer

class DownloadMediaUseCase:
    """Orchestrates the 4-Tier Fallback Cascade execution logic."""
    
    def __init__(self, extractor: IExtractorEngine, sniffer: ISniffer, cookie_manager: ICookieManager, remuxer: IRemuxer):
        self.extractor = extractor
        self.sniffer = sniffer
        self.cookie_manager = cookie_manager
        self.remuxer = remuxer
        self.logger = logging.getLogger(__name__)
        
    async def execute(self, url: str, progress_hook: Optional[Callable[[Dict], None]] = None) -> str:
        """
        Executes the 4-tier download strategy.
        Returns the path to the downloaded file.
        """
        last_error = None
        self.logger.info(f"Starting cascade extraction for {url}")
        
        # Tier 1: Fast-Path `yt-dlp`
        try:
            self.logger.info("Attempting Tier 1 (yt-dlp)")
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: self.extractor.extract(url, progress_hook=progress_hook))
        except (ExtractionFailedException, RateLimitException, LoginRequiredException) as e:
            self.logger.warning(f"Tier 1 failed: {e}")
            last_error = e

        # Tier 3: Local Cookie Bridge
        if isinstance(last_error, (LoginRequiredException, ExtractionFailedException)):
            try:
                self.logger.info("Tier 1 failed. Attempting Tier 3 (Local Cookie Bridge)")
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, lambda: self.extractor.extract(url, progress_hook=progress_hook, use_cookies=True))
            except Exception as e:
                self.logger.warning(f"Tier 3 failed: {e}")
                
        # Tier 2: Stealth Network Interceptor `Playwright`
        try:
            self.logger.info("Attempting Tier 2 (Playwright Sniffer)")
            sniffed_url = await self.sniffer.sniff_media_url(url)
            self.logger.info(f"Tier 2 found raw URL: {sniffed_url}. Passing to Tier 1.")
            
            # Use Tier 1 to download the raw CDN URL
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: self.extractor.extract(sniffed_url, progress_hook=progress_hook))
        except Exception as e:
            self.logger.error(f"Tier 2 failed: {e}")
            raise ExtractionFailedException(f"All extraction tiers failed for {url}. Last error: {str(e)}", url, 4)
