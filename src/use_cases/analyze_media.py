import uuid
import logging
from typing import List
from pydantic import HttpUrl
from domain.models import AnalyzeResponse, MediaItem, MediaType
from domain.interfaces import IExtractorEngine, ISniffer, ICookieManager
from domain.exceptions import LoginRequiredException, ExtractionFailedException

class AnalyzeMediaUseCase:
    """
    Cascades through extraction tiers (yt-dlp -> Cookies -> Playwright) to extract all
    available media items (e.g. from an Instagram carousel) without downloading.
    """
    def __init__(self, extractor: IExtractorEngine, sniffer: ISniffer, cookie_manager: ICookieManager):
        self.extractor = extractor
        self.sniffer = sniffer
        self.cookie_manager = cookie_manager
        self.logger = logging.getLogger(__name__)

    async def execute(self, url: HttpUrl, format_type: str = "video", is_playlist: bool = False, platform: str = "auto", media_filter: str = "all") -> AnalyzeResponse:
        url_str = str(url)
        cookies_path = self.cookie_manager.get_cookies_path()
        items: List[MediaItem] = []
        error_msg = None
        last_error = None
        info = None

        try:
            # Tier 1: yt-dlp
            self.logger.info(f"Analyzing {url_str} via Tier 1 (yt-dlp)")
            info = await self.extractor.analyze(url_str, use_cookies=False, cookies_path=cookies_path, is_playlist=is_playlist, platform=platform, media_filter=media_filter)
        except Exception as e:
            last_error = e

        if isinstance(last_error, (LoginRequiredException, ExtractionFailedException)):
            try:
                self.logger.info("Tier 1 analysis failed. Falling back to Tier 3 (Cookies).")
                info = await self.extractor.analyze(url_str, use_cookies=True, cookies_path=cookies_path, is_playlist=is_playlist, platform=platform, media_filter=media_filter)
                last_error = None
            except Exception as e:
                self.logger.warning(f"Tier 3 analysis failed: {e}")
                last_error = e
                
        if info:
            
            entries = info.get('entries') if 'entries' in info else [info]
            for entry in entries:
                if not entry: continue
                
                item_url = entry.get('url')
                if not item_url:
                    formats = entry.get('formats', [])
                    if formats:
                        item_url = formats[-1].get('url')
                
                if item_url:
                    # Determine type
                    ext = entry.get('ext', '')
                    vcodec = entry.get('vcodec')
                    
                    item_type = MediaType.VIDEO
                    if ext in ['jpg', 'jpeg', 'png', 'webp'] or vcodec == 'none':
                        item_type = MediaType.IMAGE
                        
                    items.append(MediaItem(
                        id=str(uuid.uuid4()),
                        url=item_url,
                        thumbnail=entry.get('thumbnail', item_url),
                        type=item_type,
                        source_url=url_str
                    ))
                    
        else:
            self.logger.warning(f"Falling back to Tier 2 (Playwright). Last error: {last_error}")
            # Tier 2: Playwright Sniffer
            try:
                media_list = await self.sniffer.sniff_all_media(url_str, cookies_path=cookies_path)
                for media in media_list:
                    items.append(MediaItem(
                        id=str(uuid.uuid4()),
                        url=media['url'],
                        thumbnail=media.get('thumbnail') or media['url'],
                        type=MediaType.IMAGE if media['type'] == 'image' else MediaType.VIDEO,
                        source_url=url_str
                    ))
            except Exception as ex:
                self.logger.error(f"Tier 2 analysis failed: {ex}")
                error_msg = f"Failed to extract media: {str(ex)}"

        # Apply Platform Specific Filters
        if platform == "instagram":
            if media_filter == "reels":
                items = [item for item in items if item.type == MediaType.VIDEO]
            elif media_filter == "images":
                items = [item for item in items if item.type == MediaType.IMAGE]
        
        return AnalyzeResponse(source_url=url_str, items=items, error=error_msg)
