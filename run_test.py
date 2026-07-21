import asyncio
import cv2
import numpy as np
import os
import sys

# Add src to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from infrastructure.realesrgan_engine import RealESRGANEngine

async def main():
    engine = RealESRGANEngine(base_dir=".")
    
    # Create a noisy low-res image
    img = np.ones((200, 200, 3), dtype=np.uint8) * 128
    cv2.circle(img, (100, 100), 50, (200, 150, 150), -1)
    
    # Add gaussian noise to simulate camera grain
    noise = np.zeros_like(img)
    cv2.randn(noise, 0, 30)
    img = cv2.add(img, noise)
    
    cv2.imwrite("test_input.png", img)
    print("Created test_input.png")
    
    print("Starting AI Upscaling + GOD-TIER Pipeline...")
    res = await engine.enhance(os.path.abspath("test_input.png"))
    
    print(f"Finished! Final image saved at: {res}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
