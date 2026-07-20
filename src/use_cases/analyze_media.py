import uuid
import logging
from typing import List
from pydantic import HttpUrl
from domain.models import AnalyzeResponse, MediaItem, MediaType
from domain.interfaces import IExtractorEngine, ISniffer

class AnalyzeMediaUseCase:
    """
    Cascades through extraction tiers (yt-dlp -> Playwright) to extract all
    available media items (e.g. from an Instagram carousel) without downloading.
    """
    def __init__(self, extractor: IExtractorEngine, sniffer: ISniffer):
        self.extractor = extractor
        self.sniffer = sniffer
        self.logger = logging.getLogger(__name__)

    async def execute(self, url: HttpUrl) -> AnalyzeResponse:
        url_str = str(url)
        items: List[MediaItem] = []
        error_msg = None

        try:
            # Tier 1: yt-dlp
            self.logger.info(f"Analyzing {url_str} via Tier 1 (yt-dlp)")
            info = await self.extractor.analyze(url_str)
            
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
                    
        except Exception as e:
            self.logger.warning(f"Tier 1 analysis failed: {e}. Falling back to Tier 2 (Playwright).")
            # Tier 2: Playwright Sniffer
            try:
                media_list = await self.sniffer.sniff_all_media(url_str)
                for media in media_list:
                    items.append(MediaItem(
                        id=str(uuid.uuid4()),
                        url=media['url'],
                        thumbnail=media['url'],
                        type=MediaType.IMAGE if media['type'] == 'image' else MediaType.VIDEO,
                        source_url=url_str
                    ))
            except Exception as ex:
                self.logger.error(f"Tier 2 analysis failed: {ex}")
                error_msg = f"Failed to extract media: {str(ex)}"

        return AnalyzeResponse(source_url=url_str, items=items, error=error_msg)
