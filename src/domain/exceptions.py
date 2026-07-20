class DownloaderException(Exception):
    """Base exception for all domain exceptions."""
    pass

class ExtractionFailedException(DownloaderException):
    """Raised when an extraction tier fails to retrieve the media."""
    def __init__(self, message: str, url: str, tier: int):
        self.message = message
        self.url = url
        self.tier = tier
        super().__init__(self.message)

class RateLimitException(DownloaderException):
    """Raised when a 429 or similar rate limit is hit."""
    pass

class LoginRequiredException(DownloaderException):
    """Raised when a private post requires login credentials or cookies."""
    pass

class RemuxingException(DownloaderException):
    """Raised when FFmpeg fails to merge audio and video streams."""
    pass

class SnifferException(DownloaderException):
    """Raised when the sniffer fails to extract media."""
    pass

class ConcurrencyException(DownloaderException):
    """Raised when concurrency limits or tasks fail."""
    pass
