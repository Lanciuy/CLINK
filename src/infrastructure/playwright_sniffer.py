import asyncio
import random
import os
import re
import json
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from domain.interfaces import ISniffer
from domain.exceptions import ExtractionFailedException, SnifferException
from infrastructure.stealth_utils import get_random_user_agent, get_random_viewport

def parse_netscape_cookies(file_path: str) -> List[Dict]:
    cookies = []
    if not os.path.exists(file_path):
        return cookies
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip() or (line.startswith('#') and not line.startswith('#HttpOnly_')):
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    domain = parts[0]
                    if domain.startswith('#HttpOnly_'):
                        domain = domain[10:]
                    
                    cookies.append({
                        'domain': domain,
                        'path': parts[2],
                        'secure': parts[3] == 'TRUE',
                        'expires': float(parts[4]) if parts[4].isdigit() else -1,
                        'name': parts[5],
                        'value': parts[6]
                    })
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to parse cookies: {e}")
    return cookies

class PlaywrightSniffer(ISniffer):
    """Tier 2: Stealth Network Interceptor (GraphQL/REST API sniffer)."""
    
    async def sniff_media_url(self, url: str, cookies_path: Optional[str] = None) -> str:
        """
        Extracts a single main media URL from the page.
        """
        items = await self.sniff_all_media(url, cookies_path)
        if not items:
            raise SnifferException(f"No media found on {url}")
        
        # Prefer video if available
        videos = [item for item in items if item.get('type') == 'video']
        if videos:
            return videos[0]['url']
        return items[0]['url']

    async def sniff_all_media(self, url: str, cookies_path: Optional[str] = None) -> List[Dict[str, str]]:
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
                
                if cookies_path:
                    parsed_cookies = parse_netscape_cookies(cookies_path)
                    if parsed_cookies:
                        # Add a dummy URL if required or just inject directly
                        try:
                            await context.add_cookies(parsed_cookies)
                        except Exception as e:
                            logging.getLogger(__name__).warning(f"Playwright failed to inject cookies: {e}")
                            
                page = await context.new_page()
                await Stealth().apply_stealth_async(page)
                
                # Network Interception for MP4/Video streams (Reels/Stories)
                captured_videos = set()
                
                async def handle_response(response):
                    try:
                        url = response.url
                        content_type = response.headers.get("content-type", "")
                        
                        # 1. Direct Media URLs (Fallback if JSON fails)
                        if response.request.resource_type == "media" or ".mp4" in url or "video" in content_type:
                            if "segment" not in url and "m4s" not in url:
                                full_video_url = re.sub(r'&bytestart=[0-9]+', '', url)
                                full_video_url = re.sub(r'&byteend=[0-9]+', '', full_video_url)
                                full_video_url = re.sub(r'\?bytestart=[0-9]+', '?', full_video_url)
                                full_video_url = re.sub(r'\?byteend=[0-9]+', '?', full_video_url)
                                full_video_url = full_video_url.replace('?&', '?').rstrip('?').rstrip('&')
                                captured_videos.add(full_video_url)
                                
                        # 2. GraphQL / API JSON Responses (Bulletproof Progressive MP4 extraction)
                        if "graphql" in url or "api/v1" in url:
                            try:
                                json_data = await response.json()
                                def extract_urls(obj):
                                    if isinstance(obj, dict):
                                        if "video_versions" in obj and isinstance(obj["video_versions"], list):
                                            for v in obj["video_versions"]:
                                                if "url" in v and isinstance(v["url"], str):
                                                    captured_videos.add(v["url"])
                                        if "video_url" in obj and isinstance(obj["video_url"], str):
                                            captured_videos.add(obj["video_url"])
                                        for v in obj.values():
                                            extract_urls(v)
                                    elif isinstance(obj, list):
                                        for item in obj:
                                            extract_urls(item)
                                extract_urls(json_data)
                            except Exception:
                                pass
                    except Exception:
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
                except Exception:
                    pass
                
                original_url_base = page.url.split('?')[0].rstrip('/')
                
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
                                results.push({url: video.src, type: 'video', thumbnail: video.poster || null});
                            }
                        }
                        
                        // 2. Image tags
                        let imgs = Array.from(container.querySelectorAll('img'));
                        for (let img of imgs) {
                            if (img.src && img.src.startsWith('data:')) continue;
                            
                            let altText = (img.getAttribute('alt') || '').toLowerCase();
                            if (altText.includes('profile picture') || altText.includes('foto profil')) continue;
                            
                            // 100% BULLETPROOF FILTER: Ignore any image smaller than 320px wide
                            // Desktop main posts are > 400px. Grid thumbnails are ~293px. Profile pics are < 150px.
                            // The Playwright script clicks "Next" sequentially, making each main carousel image visible.
                            // Therefore, we do NOT need to guess if a 0px (hidden) image is valid. It will be validated when visible!
                            if (img.clientWidth < 320) {
                                continue;
                            }
                            
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
                            
                            if (!bestImg) {
                                bestImg = img.src;
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
                            
                    # Extract global thumbnail for network videos
                    global_thumb = None
                    try:
                        global_thumb = await page.evaluate('''() => {
                            // 1. Try video poster
                            let vids = Array.from(document.querySelectorAll('video'));
                            for (let v of vids) {
                                if (v.poster && !v.poster.includes('119098904_143875323910363')) return v.poster;
                            }
                            
                            // 2. Try og:image
                            let og = document.querySelector('meta[property="og:image"]');
                            if (og && og.content && !og.content.includes('119098904_143875323910363')) return og.content;
                            
                            // 3. Try largest image on page
                            let imgs = Array.from(document.querySelectorAll('img'));
                            let bestImg = null;
                            let maxW = 0;
                            for (let i of imgs) {
                                if (i.clientWidth > maxW && i.src && !i.src.startsWith('data:')) {
                                    maxW = i.clientWidth;
                                    bestImg = i.src;
                                }
                            }
                            if (maxW >= 320 && bestImg) return bestImg;
                            
                            return null;
                        }''')
                    except Exception:
                        pass
                        
                    # Inject captured network videos
                    for vid_url in list(captured_videos):
                        clean_url = vid_url.split('?')[0] if '?' in vid_url else vid_url
                        # Basic deduplication
                        if not any(clean_url in m['url'] for m in media_items if m['type'] == 'video'):
                            media_items.insert(0, {'url': vid_url, 'type': 'video', 'thumbnail': global_thumb})
                            
                    try:
                        # Prioritize clicking the carousel's next button (inside article) instead of the "Next Post" button
                        next_btn = await page.query_selector('article button[aria-label="Next"]')
                        if not next_btn:
                            next_btn = await page.query_selector('button[aria-label="Next"]')
                            
                        if next_btn:
                            await next_btn.click()
                            await page.wait_for_timeout(1000)
                            
                            # CRITICAL FIX: If the URL changed, we clicked "Next Post" instead of carousel next!
                            current_url_base = page.url.split('?')[0].rstrip('/')
                            if current_url_base != original_url_base:
                                break
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
