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

    async def enhance(self, file_path: str, output_dir: str = None, color_boost: bool = False) -> str:
        """
        Runs Real-ESRGAN on the image file and creates an enhanced version.
        """
        if not os.path.exists(self.exe_path):
            self.logger.warning("Enhancer binary missing, skipping enhancement.")
            return file_path
            
        # Ensure it's an image we can upscale
        ext = file_path.lower().rsplit('.', 1)[-1]
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            self.logger.info(f"Skipping enhancement for non-image file: {file_path}")
            return file_path

        out_path = file_path.rsplit('.', 1)[0] + "_enhanced_tmp.png"
        
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
            
            # If successful, process with OpenCV
            if os.path.exists(result_path):
                try:
                    import cv2
                    import numpy as np
                    
                    self.logger.info("Applying GOD-TIER Pipeline: HDR CLAHE + Bilateral Smoothing + LAB Color Match + Texture Injector...")
                    
                    # Load AI Upscaled image (support Unicode paths on Windows)
                    ai_img = cv2.imdecode(np.fromfile(result_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    # Load Original image and upscale it to match AI using Lanczos
                    orig_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if ai_img is None or orig_img is None:
                        raise ValueError(f"Failed to load images for post-processing. Paths might be invalid: {file_path}")
                        
                    h, w = ai_img.shape[:2]
                    orig_up = cv2.resize(orig_img, (w, h), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Use the modular God-Tier Cosplay v1 preset
                    from infrastructure.presets.god_tier_cosplay_v1 import apply_preset
                    
                    self.logger.info("Applying GOD-TIER Pipeline Preset: God-Tier Cosplay Ultra-HD v1")
                    blended = apply_preset(ai_img, orig_img, color_boost=color_boost)
                    
                    # Generate 4K variant
                    max_4k = 3840
                    img_4k = blended
                    if max(h, w) > max_4k:
                        scale = max_4k / max(h, w)
                        img_4k = cv2.resize(blended, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                    
                    # Generate 2K variant
                    max_2k = 2560
                    img_2k = blended
                    if max(h, w) > max_2k:
                        scale = max_2k / max(h, w)
                        img_2k = cv2.resize(blended, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                        
                    # Generate 1080p variant
                    max_1080p = 1920
                    img_1080p = blended
                    if max(h, w) > max_1080p:
                        scale = max_1080p / max(h, w)
                        img_1080p = cv2.resize(blended, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                        
                    # Determine save path based on output_dir
                    file_name = os.path.basename(file_path).rsplit('.', 1)[0]
                    target_dir = output_dir if output_dir else os.path.dirname(file_path)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    path_4k = os.path.join(target_dir, file_name + "_Enhanced_4K.png")
                    path_2k = os.path.join(target_dir, file_name + "_Enhanced_2K.png")
                    
                    cv2.imencode('.png', img_4k)[1].tofile(path_4k)
                    cv2.imencode('.png', img_2k)[1].tofile(path_2k)
                    
                    # Cleanup the temporary AI upscaled image ONLY. We MUST KEEP the original file.
                    if os.path.exists(result_path):
                        os.remove(result_path)
                    
                    return path_4k
                    
                except ImportError:
                    self.logger.warning("OpenCV not installed. Skipping Frequency Separation.")
                except Exception as ex:
                    self.logger.error(f"Post-processing failed: {ex}")
                    
                # Fallback cleanup if OpenCV fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                final_path = file_path.rsplit('.', 1)[0] + ".png"
                if os.path.exists(result_path):
                    os.replace(result_path, final_path)
                return final_path
                
        except Exception as e:
            self.logger.error(f"Image enhancement failed: {e}")
            
        return file_path
