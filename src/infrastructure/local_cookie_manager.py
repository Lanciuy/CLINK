import os
from typing import Optional
from domain.interfaces import ICookieManager

class LocalCookieManager(ICookieManager):
    """Tier 3: Browser cookie bridge via cookies.txt."""
    
    def __init__(self, base_dir: str):
        self.cookies_path = os.path.join(base_dir, "cookies.txt")
    
    def get_cookies_for_domain(self, domain: str) -> str:
        # Legacy fallback if needed
        return "chrome"
        
    def get_cookies_path(self) -> Optional[str]:
        if os.path.exists(self.cookies_path) and os.path.getsize(self.cookies_path) > 0:
            return self.cookies_path
        return None
        
    def save_cookies(self, cookie_content: str) -> None:
        with open(self.cookies_path, "w", encoding="utf-8") as f:
            f.write(cookie_content)
