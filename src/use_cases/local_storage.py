import os

class LocalStorage:
    """Handles output file naming, folder creation, and OS pathing."""
    
    def __init__(self, base_dir: str = "downloads"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        
    def get_download_path(self) -> str:
        return self.base_dir
        
    def ensure_exists(self):
        os.makedirs(self.base_dir, exist_ok=True)
