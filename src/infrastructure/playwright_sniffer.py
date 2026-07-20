import asyncio
from playwright.async_api import async_playwright
from domain.exceptions import ExtractionFailedException

class PlaywrightSniffer:
    """Tier 2: Stealth Network Interceptor (GraphQL/REST API sniffer)."""
    
    async def sniff_media_url(self, url: str) -> str:
        """
        Launches headless Chromium, navigates to URL, and intercepts network requests
        to find the underlying media CDN URL.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                media_url = None
                
                async def handle_response(response):
                    nonlocal media_url
                    if media_url:
                        return
                    
                    if response.request.resource_type == "media":
                        media_url = response.url

                page.on("response", handle_response)
                
                # Navigate and wait for network idle
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait a bit more for dynamic content
                await page.wait_for_timeout(3000)
                
                await browser.close()
                
                if media_url:
                    return media_url
                else:
                    raise ExtractionFailedException("Could not sniff media URL", url, 2)
                    
        except Exception as e:
             raise ExtractionFailedException(f"Playwright sniffer failed: {str(e)}", url, 2)
