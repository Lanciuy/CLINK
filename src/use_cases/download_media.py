import asyncio
import logging
import os
from typing import Callable, Optional, Dict
from domain.exceptions import ExtractionFailedException, RateLimitException, LoginRequiredException, SnifferException, RemuxingException
from domain.interfaces import IExtractorEngine, ISniffer, ICookieManager, IRemuxer, IEnhancer

class DownloadMediaUseCase:
    """Orchestrates the 4-Tier Fallback Cascade execution logic."""
    
    def __init__(self, extractor: IExtractorEngine, sniffer: ISniffer, cookie_manager: ICookieManager, remuxer: IRemuxer, enhancer: IEnhancer = None, enhanced_dir: str = None):
        self.extractor = extractor
        self.sniffer = sniffer
        self.cookie_manager = cookie_manager
        self.remuxer = remuxer
        self.enhancer = enhancer
        self.enhanced_dir = enhanced_dir
        self.logger = logging.getLogger(__name__)
        
    async def execute(self, url: str, progress_callback: Callable[[Dict], None], enhance_images: bool = False, color_boost: bool = False, format_type: str = "video", is_playlist: bool = False, platform: str = "auto", media_filter: str = "all") -> str:
        """
        Coordinates the multi-tier extraction process for a single item.
        Returns the path to the downloaded file.
        """
        last_error = None
        self.logger.info(f"Starting cascade extraction for {url}")
        
        file_path = None
        cookies_path = self.cookie_manager.get_cookies_path()
        
        # Tier 1: Fast-Path `yt-dlp`
        try:
            self.logger.info("Attempting Tier 1 (yt-dlp)")
            loop = asyncio.get_running_loop()
            file_path = await loop.run_in_executor(None, lambda: self.extractor.extract(url, progress_hook=progress_callback, format_type=format_type, is_playlist=is_playlist, platform=platform, media_filter=media_filter))
            last_error = None
        except (ExtractionFailedException, RateLimitException, LoginRequiredException) as e:
            self.logger.warning(f"Tier 1 failed: {e}")
            last_error = e

        # Tier 3: Local Cookie Bridge
        if not file_path and isinstance(last_error, (LoginRequiredException, ExtractionFailedException)):
            try:
                self.logger.info("Tier 1 failed. Attempting Tier 3 (Local Cookie Bridge)")
                loop = asyncio.get_running_loop()
                file_path = await loop.run_in_executor(None, lambda: self.extractor.extract(url, progress_hook=progress_callback, use_cookies=True, cookies_path=cookies_path, format_type=format_type, is_playlist=is_playlist, platform=platform, media_filter=media_filter))
                last_error = None
            except Exception as e:
                self.logger.warning(f"Tier 3 failed: {e}")
                last_error = e
                
        # Tier 2: Stealth Network Interceptor `Playwright`
        if not file_path:
            try:
                self.logger.info("Attempting Tier 2 (Playwright Sniffer)")
                sniffed_url = await self.sniffer.sniff_media_url(url)
                self.logger.info(f"Tier 2 found raw URL: {sniffed_url}. Passing to Tier 1.")
                
                # Use Tier 1 to download the raw CDN URL
                loop = asyncio.get_running_loop()
                file_path = await loop.run_in_executor(None, lambda: self.extractor.extract(sniffed_url, progress_hook=progress_callback, cookies_path=cookies_path, format_type=format_type, is_playlist=is_playlist, platform=platform, media_filter=media_filter))
            except Exception as e:
                self.logger.error(f"Tier 2 failed: {e}")
                raise ExtractionFailedException(f"All extraction tiers failed for {url}. Last error: {str(e)}", url, 4)

        if enhance_images and self.enhancer and file_path:
            self.logger.info(f"Enhancing downloaded image: {file_path}")
            raw_path = file_path
            file_path = await self.enhancer.enhance(file_path, output_dir=self.enhanced_dir, color_boost=color_boost)
            try:
                if file_path != raw_path and os.path.exists(raw_path):
                    os.remove(raw_path)
            except Exception as e:
                self.logger.warning(f"Failed to delete raw image after enhancement: {e}")
            
        return file_path
