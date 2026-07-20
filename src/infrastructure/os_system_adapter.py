import os
import subprocess
import platform

class OSSystemAdapter:
    """Adapter for interacting with the native OS."""
    
    @staticmethod
    def open_folder(path: str):
        """
        Opens the native OS File Explorer at the specified path.
        """
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin": # macOS
            subprocess.Popen(["open", path])
        else: # Linux
            subprocess.Popen(["xdg-open", path])
