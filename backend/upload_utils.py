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

def check_framing(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, "No object detected"

    # Largest contour (assume it's the object)
    c = max(contours, key=cv2.contourArea)
    x,y,w,h = cv2.boundingRect(c)
    obj_area = w * h
    img_area = img.shape[0] * img.shape[1]

    coverage = obj_area / img_area
    cx, cy = x + w/2, y + h/2
    img_cx, img_cy = img.shape[1]/2, img.shape[0]/2

    # Check coverage
    if coverage < 0.2:
        return False, "Object too small"
    if coverage > 0.9:
        return False, "Object too cropped"

    # Check centering
    if abs(cx - img_cx) > img.shape[1]*0.25 or abs(cy - img_cy) > img.shape[0]*0.25:
        return False, "Object off-center"

    return True, "Framing OK"
