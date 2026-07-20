class LocalCookieManager:
    """Tier 3: Browser cookie bridge for private/restricted posts."""
    
    @staticmethod
    def get_preferred_browser() -> str:
        """
        Returns the preferred browser to extract cookies from.
        """
        return "chrome"
