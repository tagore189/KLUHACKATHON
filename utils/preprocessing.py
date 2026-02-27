"""Image preprocessing utilities for damage analysis."""
import os
import cv2
import base64
import numpy as np

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
MAX_DIM = 1024
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path):
    """
    Preprocess image for damage detection using OpenCV.
    - Resizes to a max dimension of 1024px while maintaining aspect ratio
    - Saves the preprocessed image back to disk
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    # Get original dimensions
    h, w = img.shape[:2]

    # Calculate scale factor
    if max(h, w) > MAX_DIM:
        scale = MAX_DIM / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Overwrite original image with preprocessed version
    cv2.imwrite(image_path, img)
    return img


def image_to_base64(image_path):
    """Convert image file to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def mat_to_base64(img_mat, format='.jpg'):
    """Convert OpenCV Mat to base64 string."""
    _, buffer = cv2.imencode(format, img_mat)
    return base64.b64encode(buffer).decode('utf-8')


def get_image_metadata(image_path):
    """Extract metadata from image using OpenCV."""
    img = cv2.imread(image_path)
    if img is None:
        return {}

    h, w = img.shape[:2]
    file_size = os.path.getsize(image_path)
    ext = image_path.rsplit('.', 1)[-1].lower()

    return {
        'width': w,
        'height': h,
        'format': ext.upper(),
        'channels': img.shape[2] if len(img.shape) > 2 else 1,
        'file_size_kb': round(file_size / 1024, 2)
    }


def ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return UPLOAD_FOLDER
