"""Image preprocessing utilities for damage analysis."""
import os
from PIL import Image
import io
import base64


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
MAX_IMAGE_SIZE = (1024, 1024)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path):
    """
    Preprocess image for damage detection.
    - Resizes to a max dimension of 1024px
    - Converts to RGB
    - Returns PIL Image object
    """
    img = Image.open(image_path)
    img = img.convert('RGB')
    img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
    return img


def image_to_base64(image_path):
    """Convert image file to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def pil_to_base64(pil_image, format='JPEG'):
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def get_image_metadata(image_path):
    """Extract metadata from image."""
    img = Image.open(image_path)
    file_size = os.path.getsize(image_path)
    return {
        'width': img.width,
        'height': img.height,
        'format': img.format,
        'mode': img.mode,
        'file_size_kb': round(file_size / 1024, 2)
    }


def ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return UPLOAD_FOLDER
