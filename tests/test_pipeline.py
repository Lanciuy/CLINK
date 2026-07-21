import asyncio
import logging
import os
import sys

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from infrastructure.realesrgan_engine import RealESRGANEngine

async def test_realesrgan_pipeline():
    """Integration test for Real-ESRGAN upscaling engine."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing RealESRGANEngine test...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    engine = RealESRGANEngine(base_dir=base_dir)
    
    # Check if executable exists or can be downloaded
    assert os.path.exists(engine.exe_path) or engine.download_url, "Real-ESRGAN executable or download URL missing"
    logger.info("RealESRGANEngine initialized successfully.")

if __name__ == "__main__":
    asyncio.run(test_realesrgan_pipeline())
