import cv2
import numpy as np
import urllib.request
import os

# Download a sample face image if not exists
if not os.path.exists("test_face.png"):
    # Generate a dummy image if we can't download
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.circle(img, (250, 250), 100, (255, 200, 200), -1)
    cv2.imwrite("test_face.png", img)

orig_up = cv2.imread("test_face.png")
ai_matched = np.zeros_like(orig_up) # Fake AI image

# 1. Load Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 2. Detect Faces
gray = cv2.cvtColor(orig_up, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)

# 3. Create Face Mask
face_mask = np.zeros((orig_up.shape[0], orig_up.shape[1]), dtype=np.float32)

for (x, y, w, h) in faces:
    # Calculate center and axes for a soft elliptical mask
    center = (x + w//2, y + h//2)
    axes = (w//2, int(h//1.5)) # Slightly taller mask for full face
    
    # Draw solid ellipse on a temporary mask
    temp_mask = np.zeros_like(face_mask)
    cv2.ellipse(temp_mask, center, axes, 0, 0, 360, 1.0, -1)
    
    # Blur the ellipse to create a soft feathered transition
    blur_amount = max(w, h) // 4
    if blur_amount % 2 == 0:
        blur_amount += 1
    temp_mask = cv2.GaussianBlur(temp_mask, (blur_amount, blur_amount), 0)
    
    # Add to main mask (clip to 1.0)
    face_mask = np.clip(face_mask + temp_mask, 0.0, 1.0)

# Expand mask to 3 channels
face_mask_3c = cv2.merge([face_mask, face_mask, face_mask])

# 4. Blend: Face regions get orig_up, non-face regions get ai_matched
# This forces the face to be 100% original, bypassing AI hallucinations!
face_preserved_ai = (orig_up.astype(np.float32) * face_mask_3c) + (ai_matched.astype(np.float32) * (1.0 - face_mask_3c))
face_preserved_ai = np.clip(face_preserved_ai, 0, 255).astype(np.uint8)

print("Face preservation successful. Faces detected:", len(faces))
