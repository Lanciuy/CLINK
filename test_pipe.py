import cv2
import numpy as np

file_path = "test_orig.png"
result_path = "test_ai.png"

try:
    ai_img = cv2.imdecode(np.fromfile(result_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    orig_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    
    h, w = ai_img.shape[:2]
    orig_up = cv2.resize(orig_img, (w, h), interpolation=cv2.INTER_LANCZOS4)
    
    # 1. HDR Pop
    ai_lab_8u = cv2.cvtColor(ai_img, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    ai_lab_8u[:, :, 0] = clahe.apply(ai_lab_8u[:, :, 0])
    ai_img_hdr = cv2.cvtColor(ai_lab_8u, cv2.COLOR_LAB2BGR)
    
    # 2. Skin / Surface Smoothing
    ai_img_smooth = cv2.bilateralFilter(ai_img_hdr, d=9, sigmaColor=50, sigmaSpace=50)
    
    # 3. LAB Color Match
    orig_lab = cv2.cvtColor(orig_up, cv2.COLOR_BGR2LAB).astype(np.float32)
    ai_lab_float = cv2.cvtColor(ai_img_smooth, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    # NumPy mean/std is already C-optimized and extremely fast
    for i in range(1, 3):
        orig_mean, orig_std = orig_lab[:, :, i].mean(), orig_lab[:, :, i].std()
        ai_mean, ai_std = ai_lab_float[:, :, i].mean(), ai_lab_float[:, :, i].std()
        if ai_std > 0:
            # We can use cv2.subtract / cv2.multiply to avoid intermediate temp arrays in Python memory
            ai_lab_float[:, :, i] = cv2.addWeighted(
                cv2.subtract(ai_lab_float[:, :, i], ai_mean),
                orig_std / ai_std,
                ai_lab_float[:, :, i],
                0.0,
                orig_mean
            )
            
    ai_lab_float = np.clip(ai_lab_float, 0, 255).astype(np.uint8)
    ai_matched = cv2.cvtColor(ai_lab_float, cv2.COLOR_LAB2BGR)
    
    # 4. Advanced Frequency Separation
    blurred_orig = cv2.GaussianBlur(orig_up, (7, 7), 5.0)
    
    # Instead of casting to float32 and subtracting which takes 3x memory
    # We can use cv2.subtract with 16-bit signed integer to prevent clipping
    # But wait, ai_matched is 8-bit. We want to do: blended = ai_matched + (orig_up - blurred_orig) * 1.5
    # Let's do it with cv2.addWeighted directly if we can!
    # ai_matched + 1.5 * orig_up - 1.5 * blurred_orig
    # Because intermediate might go above 255 or below 0, we must do it in float32 or int16.
    
    # Convert to float32 for high precision blending (zero-copy from cv2)
    ai_f = cv2.addWeighted(ai_matched, 1.0, ai_matched, 0.0, 0.0, dtype=cv2.CV_32F)
    orig_f = cv2.addWeighted(orig_up, 1.0, orig_up, 0.0, 0.0, dtype=cv2.CV_32F)
    blur_f = cv2.addWeighted(blurred_orig, 1.0, blurred_orig, 0.0, 0.0, dtype=cv2.CV_32F)
    
    high_pass = cv2.subtract(orig_f, blur_f)
    
    blended_f = cv2.addWeighted(ai_f, 1.0, high_pass, 1.5, 0.0)
    blended = cv2.convertScaleAbs(blended_f) # Efficiently clips to 0-255 and converts to uint8
    
    # 6. Ultimate Micro-Contrast / Unsharp Mask
    blurred_blended = cv2.GaussianBlur(blended, (0, 0), 2.0)
    overpower_final = cv2.addWeighted(blended, 1.8, blurred_blended, -0.8, 0.0)
    
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
