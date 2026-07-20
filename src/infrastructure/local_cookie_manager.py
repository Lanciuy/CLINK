from domain.interfaces import ICookieManager

class LocalCookieManager(ICookieManager):
    """Tier 3: Browser cookie bridge for private/restricted posts."""
    
    def get_cookies_for_domain(self, domain: str) -> str:
        """
        Returns cookies for a specific domain (stub for now, returns preferred browser).
        """
        return "chrome"
