import asyncio
import random
from typing import List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from domain.interfaces import ISniffer
from domain.exceptions import ExtractionFailedException, SnifferException
from infrastructure.stealth_utils import get_random_user_agent, get_random_viewport

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
                browser = await p.chromium.launch(
                    headless=True, 
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--autoplay-policy=no-user-gesture-required",
                        "--mute-audio",
                        "--disable-web-security"
                    ]
                )
                
                vp = get_random_viewport()
                ua = get_random_user_agent()
                
                context = await browser.new_context(
                    user_agent=ua,
                    viewport={"width": vp["width"], "height": vp["height"]}
                )
                page = await context.new_page()
                await Stealth().apply_stealth_async(page)
                
                # Network Interception for MP4/Video streams (Reels/Stories)
                captured_videos = set()
                def handle_response(response):
                    try:
                        url = response.url
                        content_type = response.headers.get("content-type", "")
                        if response.request.resource_type == "media" or ".mp4" in url or "video" in content_type:
                            # Filter out small segments if possible, prefer full videos
                            if "byte-range" not in url and "segment" not in url:
                                captured_videos.add(url)
                    except:
                        pass
                page.on("response", handle_response)
                
                # Navigate and wait for network idle
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Random human-like delay between 2-4 seconds
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                # Simulate a click in the center of the viewport to trigger potential play-on-click
                try:
                    await page.mouse.click(vp["width"] // 2, vp["height"] // 2)
                    await page.wait_for_timeout(random.randint(1500, 2500)) # Give IG/JS time to render and buffer video
                except:
                    pass
                
                media_items = []
                for _ in range(15): # Max 15 carousel items
                    new_items = await page.evaluate('''() => {
                        let results = [];
                        // Helper to clean Instagram crop parameters
                        function cleanIGUrl(url) {
                            if (!url) return null;
                            return url.replace(/\\/[cps][0-9]+[0-9x\\.]+\\//g, '/').replace(/\\/e[0-9]+\\//g, '/');
                        }
    
                        let container = document.querySelector('article') || document.querySelector('main') || document;
                        
                        // 1. Video tags (fallback if network interception misses)
                        let videos = Array.from(container.querySelectorAll('video'));
                        for (let video of videos) {
                            if (video.src && !video.src.startsWith('blob:')) {
                                results.push({url: video.src, type: 'video'});
                            }
                        }
                        
                        // 2. Image tags
                        let imgs = Array.from(container.querySelectorAll('img'));
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
                    
                    for item in new_items:
                        if item not in media_items:
                            media_items.append(item)
                            
                    # Inject captured network videos
                    for vid_url in list(captured_videos):
                        clean_url = vid_url.split('?')[0] if '?' in vid_url else vid_url
                        # Basic deduplication
                        if not any(clean_url in m['url'] for m in media_items if m['type'] == 'video'):
                            media_items.insert(0, {'url': vid_url, 'type': 'video'})
                            
                    try:
                        next_btn = await page.query_selector('button[aria-label="Next"]')
                        if next_btn:
                            await next_btn.click()
                            await page.wait_for_timeout(1000)
                        else:
                            break
                    except Exception:
                        break
                
                await browser.close()
                
                if media_items and len(media_items) > 0:
                    return media_items
                else:
                    raise ExtractionFailedException("Could not sniff media URL (Login wall or obscured DOM)", url, 2)
                    
        except Exception as e:
             raise ExtractionFailedException(f"Playwright sniffer failed: {str(e)}", url, 2)
