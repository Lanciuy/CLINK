import abc
from typing import Callable, Optional, Dict, List, Any

class IExtractorEngine(abc.ABC):
    """Tier 1 interface for fast-path media extraction."""
    @abc.abstractmethod
    def extract(self, url: str, progress_hook: Optional[Callable[[Dict], None]] = None, use_cookies: bool = False, cookies_path: Optional[str] = None, format_type: str = "video", is_playlist: bool = False, platform: str = "auto", media_filter: str = "all") -> str:
        pass
        
    @abc.abstractmethod
    async def analyze(self, url: str, use_cookies: bool = False, cookies_path: Optional[str] = None, is_playlist: bool = False, platform: str = "auto", media_filter: str = "all") -> Dict[str, Any]:
        pass

class ISniffer(abc.ABC):
    """Tier 2 interface for stealth network interception."""
    @abc.abstractmethod
    async def sniff_media_url(self, url: str, cookies_path: Optional[str] = None) -> str:
        pass
        
    @abc.abstractmethod
    async def sniff_all_media(self, url: str, cookies_path: Optional[str] = None) -> List[Dict[str, str]]:
        pass

class ICookieManager(abc.ABC):
    """Tier 3 interface for local cookie extraction."""
    @abc.abstractmethod
    def get_cookies_for_domain(self, domain: str) -> str:
        pass
        
    @abc.abstractmethod
    def get_cookies_path(self) -> Optional[str]:
        """Returns path to cookies.txt if exists and valid."""
        pass
        
    @abc.abstractmethod
    def save_cookies(self, cookie_content: str) -> None:
        """Saves Netscape format cookies to cookies.txt."""
        pass

class IRemuxer(abc.ABC):
    """Tier 4 interface for media stream remuxing."""
    @staticmethod
    @abc.abstractmethod
    def merge(video_path: str, audio_path: str, output_path: str) -> str:
        pass

class IStorage(abc.ABC):
    """Interface for local storage management."""
    @abc.abstractmethod
    def get_download_path(self) -> str:
        pass
        
    @abc.abstractmethod
    def ensure_exists(self) -> None:
        pass

class IEnhancer(abc.ABC):
    """Interface for AI image/video upscaling."""
    @abc.abstractmethod
    async def enhance(self, file_path: str) -> str:
        pass
