import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
from domain.interfaces import ISniffer
from domain.exceptions import ExtractionFailedException, SnifferException

class PlaywrightSniffer(ISniffer):
    """Tier 2: Stealth Network Interceptor (GraphQL/REST API sniffer)."""
    
    async def sniff_media_url(self, url: str) -> str:
        """
        Extracts a single main media URL from the page.
        """
        items = await self.sniff_all_media(url)
        if not items:
            raise SnifferException(f"No media found on {url}")
        
        # Prefer video if available
        videos = [item for item in items if item.get('type') == 'video']
        if videos:
            return videos[0]['url']
        return items[0]['url']

    async def sniff_all_media(self, url: str) -> List[Dict[str, str]]:
        """
        Launches headless Chromium, navigates to URL, and finds all media elements.
        Returns a list of dicts: [{'url': str, 'type': 'image'|'video'}]
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate and wait for network idle
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(4000) # Give IG/JS time to render
                
                media_items = await page.evaluate('''() => {
                    let results = [];
                    // Helper to clean Instagram crop parameters
                    function cleanIGUrl(url) {
                        if (!url) return null;
                        return url.replace(/\\/[cps][0-9]+[0-9x\\.]+\\//g, '/').replace(/\\/e[0-9]+\\//g, '/');
                    }

                    // 1. Video tags
                    let videos = Array.from(document.querySelectorAll('video'));
                    for (let video of videos) {
                        if (video.src && !video.src.startsWith('blob:')) {
                            results.push({url: video.src, type: 'video'});
                        }
                    }
                    
                    // 2. Image tags
                    let imgs = Array.from(document.querySelectorAll('img'));
                    for (let img of imgs) {
                        if (img.src && img.src.startsWith('data:')) continue;
                        
                        let bestImg = null;
                        let maxWidth = 0;
                        
                        if (img.srcset) {
                            let sources = img.srcset.split(',').map(s => s.trim().split(' '));
                            for (let src of sources) {
                                if (src.length === 2 && src[1].endsWith('w')) {
                                    let width = parseInt(src[1].replace('w', ''));
                                    if (width > maxWidth) {
                                        maxWidth = width;
                                        bestImg = src[0];
                                    }
                                }
                            }
                        }
                        
                        if (maxWidth < 500) {
                            let area = img.clientWidth * img.clientHeight;
                            if (area > 40000 && img.clientWidth > 300) {
                                bestImg = img.src;
                            }
                        }
                        
                        if (bestImg) {
                            let clean = cleanIGUrl(bestImg);
                            if (!results.find(r => r.url === clean)) {
                                results.push({url: clean, type: 'image'});
                            }
                        }
                    }
                    
                    // 3. Fallback to OG Meta tags
                    if (results.length === 0) {
                        let ogVideo = document.querySelector('meta[property="og:video"]');
                        if (ogVideo && ogVideo.content) results.push({url: cleanIGUrl(ogVideo.content), type: 'video'});
                        
                        let ogImage = document.querySelector('meta[property="og:image"]');
                        if (ogImage && ogImage.content && !ogImage.content.includes('119098904_143875323910363')) {
                            results.push({url: cleanIGUrl(ogImage.content), type: 'image'});
                        }
                    }
                    
                    return results;
                }''')
                
                await browser.close()
                
                if media_items and len(media_items) > 0:
                    return media_items
                else:
                    raise ExtractionFailedException("Could not sniff media URL (Login wall or obscured DOM)", url, 2)
                    
        except Exception as e:
             raise ExtractionFailedException(f"Playwright sniffer failed: {str(e)}", url, 2)
