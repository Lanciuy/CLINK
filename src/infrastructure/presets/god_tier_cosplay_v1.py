import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def apply_preset(ai_img: np.ndarray, orig_img: np.ndarray, color_boost: bool = False) -> np.ndarray:
    """
    Applies the "God-Tier Cosplay Ultra-HD v1" preset.
    This preset is characterized by:
    - High dynamic range pop (CLAHE)
    - Pores preservation (Low Sigma Bilateral Filter)
    - Face-Aware Identity Anchor (Haar Cascades + 35% Face Anchor)
    - Aggressive Unsharp Masking for clothes/body (95% AI HDR)
    
    Args:
        ai_img: The BGR image upscaled by Real-ESRGAN
        orig_img: The original BGR low-res image
        color_boost: Whether to apply a 25% vibrance boost in LAB color space
        
    Returns:
        np.ndarray: The post-processed BGR image.
    """
    h, w = ai_img.shape[:2]
    orig_up = cv2.resize(orig_img, (w, h), interpolation=cv2.INTER_LANCZOS4)
    
    # 1. HDR Pop (CLAHE on L-channel of AI Image for maximum dynamic range)
    ai_lab_8u = cv2.cvtColor(ai_img, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    ai_lab_8u[:, :, 0] = clahe.apply(ai_lab_8u[:, :, 0])
    ai_img_hdr = cv2.cvtColor(ai_lab_8u, cv2.COLOR_LAB2BGR)
    
    # 2. Skin / Surface Smoothing (Edge-preserving Bilateral Filter)
    ai_img_smooth = cv2.bilateralFilter(ai_img_hdr, d=9, sigmaColor=25, sigmaSpace=25)
    
    # 3. PERFECT Color Preservation (Luminance Mapping)
    # We take the high-res texture (Luminance) from AI, but keep the exact colors (A & B) from the original
    orig_lab = cv2.cvtColor(orig_up, cv2.COLOR_BGR2LAB).astype(np.float32)
    ai_lab_float = cv2.cvtColor(ai_img_smooth, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    # Directly map original color channels (A, B) to the AI image
    ai_lab_float[:, :, 1] = orig_lab[:, :, 1]
    ai_lab_float[:, :, 2] = orig_lab[:, :, 2]
            
    # Optional: Color Boost / Vibrance
    if color_boost:
        for i in range(1, 3):
            ai_lab_float[:, :, i] = cv2.addWeighted(
                ai_lab_float[:, :, i], 1.25,
                np.full(ai_lab_float[:, :, i].shape, 128, dtype=np.float32), -0.25, 0.0
            )
            
    ai_lab_float = np.clip(ai_lab_float, 0, 255).astype(np.uint8)
    ai_matched = cv2.cvtColor(ai_lab_float, cv2.COLOR_LAB2BGR)
    
    # 4. Identity Preservation Anchor & Frequency Separation (FACE-AWARE)
    ai_f = cv2.addWeighted(ai_matched, 1.0, ai_matched, 0.0, 0.0, dtype=cv2.CV_32F)
    orig_f = cv2.addWeighted(orig_up, 1.0, orig_up, 0.0, 0.0, dtype=cv2.CV_32F)
    
    # a) AGGRESSIVE UNSHARP MASKING (AI HD BOOST) FOR CLOTHES/BODY
    ai_blur = cv2.GaussianBlur(ai_matched, (0, 0), 3.0)
    ai_blur_f = cv2.addWeighted(ai_blur, 1.0, ai_blur, 0.0, 0.0, dtype=cv2.CV_32F)
    ai_hd_f = cv2.addWeighted(ai_f, 2.2, ai_blur_f, -1.2, 0.0, dtype=cv2.CV_32F)
    
    # b) SKIN DETECTION & MASKING (Fallback for OpenCV 5 missing CascadeClassifier)
    # Convert original upscaled image to YCrCb color space for robust skin detection
    ycrcb = cv2.cvtColor(orig_up, cv2.COLOR_BGR2YCrCb)
    
    # Define generic human skin color bounds in YCrCb
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
    
    # Create binary mask of skin regions
    skin_mask_binary = cv2.inRange(ycrcb, lower_skin, upper_skin)
    
    # Clean up the mask (remove noise, fill holes)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask_binary = cv2.morphologyEx(skin_mask_binary, cv2.MORPH_OPEN, kernel, iterations=2)
    skin_mask_binary = cv2.morphologyEx(skin_mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Convert mask to float32 (0.0 to 1.0)
    mask = skin_mask_binary.astype(np.float32) / 255.0
    
    # Blur the mask heavily so the transition between skin and clothes is seamless
    blur_radius = int(max(w, h) * 0.05)
    if blur_radius % 2 == 0:
        blur_radius += 1
    mask = cv2.GaussianBlur(mask, (blur_radius, blur_radius), 0)
    
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    
    # c) SELECTIVE BLENDING
    # Base anchor for the whole image (clothes/bg get 95% HD AI)
    base_anchor_f = cv2.addWeighted(ai_hd_f, 0.95, orig_f, 0.05, 0.0)
    
    # Strong anchor for skin/faces (35%) to prevent hallucination of facial features
    face_anchor_f = cv2.addWeighted(ai_hd_f, 0.65, orig_f, 0.35, 0.0)
    
    blended_f = (base_anchor_f * (1.0 - mask_3ch)) + (face_anchor_f * mask_3ch)
    
    # Micro-contrast macro pop
    blurred_blended = cv2.GaussianBlur(blended_f, (0, 0), 10.0)
    overpower_final_f = cv2.addWeighted(blended_f, 1.2, blurred_blended, -0.2, 0.0)
    
    blended = np.clip(overpower_final_f, 0, 255).astype(np.uint8)
    return blended
