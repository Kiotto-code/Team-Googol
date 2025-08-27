import cv2
import numpy as np

def is_lighting_good(image_path, min_brightness=50, max_brightness=1000, min_contrast=20):
    # Read image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Calculate brightness (mean pixel value)
    brightness = np.mean(gray)

    # Calculate contrast (standard deviation of pixel values)
    contrast = np.std(gray)

    # Check thresholds
    good_brightness = min_brightness <= brightness <= max_brightness
    good_contrast = contrast >= min_contrast

    return good_brightness and good_contrast, brightness, contrast

# Usage
good, brightness, contrast = is_lighting_good("uploads/images.jpg")
if not good:
    print("Lighting is not good enough, please re-upload.")
else:
    print("Lighting is fine.")
