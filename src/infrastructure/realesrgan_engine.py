import os
import asyncio
import urllib.request
import zipfile
import logging
import subprocess
from domain.interfaces import IEnhancer

class RealESRGANEngine(IEnhancer):
    """Tiered AI Upscaler using Real-ESRGAN NCNN Vulkan."""
    
    def __init__(self, base_dir: str):
        self.logger = logging.getLogger(__name__)
        self.tools_dir = os.path.join(base_dir, "tools", "realesrgan")
        self.exe_path = os.path.join(self.tools_dir, "realesrgan-ncnn-vulkan.exe")
        self.download_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
        
        self._ensure_installed()

    def _ensure_installed(self):
        if os.path.exists(self.exe_path):
            return
            
        self.logger.info("Real-ESRGAN not found. Downloading...")
        os.makedirs(self.tools_dir, exist_ok=True)
        zip_path = os.path.join(self.tools_dir, "realesrgan.zip")
        
        try:
            urllib.request.urlretrieve(self.download_url, zip_path)
            self.logger.info("Extracting Real-ESRGAN...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.tools_dir)
            os.remove(zip_path)
            self.logger.info("Real-ESRGAN installed successfully.")
        except Exception as e:
            self.logger.error(f"Failed to install Real-ESRGAN: {e}")

    async def enhance(self, file_path: str) -> str:
        """
        Runs Real-ESRGAN on the image file and replaces it.
        """
        if not os.path.exists(self.exe_path):
            self.logger.warning("Enhancer binary missing, skipping enhancement.")
            return file_path
            
        # Ensure it's an image we can upscale
        ext = file_path.lower().rsplit('.', 1)[-1]
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            self.logger.info(f"Skipping enhancement for non-image file: {file_path}")
            return file_path

        out_path = file_path.rsplit('.', 1)[0] + "_enhanced.png"
        
        # Build command
        # -i input, -o output, -n model (realesrgan-x4plus is default), -s scale (4)
        cmd = [
            self.exe_path,
            "-i", file_path,
            "-o", out_path,
            "-n", "realesrgan-x4plus",
            "-s", "4",
            "-f", "png"
        ]
        
        self.logger.info(f"Enhancing image: {file_path}")
        
        def _run():
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(f"Real-ESRGAN failed: {stderr.decode('utf-8', errors='ignore')}")
            return out_path

        loop = asyncio.get_running_loop()
        try:
            result_path = await loop.run_in_executor(None, _run)
            
            # If successful, replace original with enhanced
            if os.path.exists(result_path):
                os.remove(file_path)
                final_path = file_path.rsplit('.', 1)[0] + ".png"
                os.rename(result_path, final_path)
                return final_path
                
        except Exception as e:
            self.logger.error(f"Image enhancement failed: {e}")
            
        return file_path
