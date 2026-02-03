"""OCR service for scanned documents."""

import os
import sys
from PIL import Image
import pytesseract

# Configure Tesseract path for Windows
if sys.platform == 'win32':
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


class OCRService:
    """Service for extracting text from images using Tesseract."""

    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from a PIL image.

        Args:
            image: PIL Image to process

        Returns:
            Extracted text (may be empty)
        """
        try:
            return pytesseract.image_to_string(image) or ""
        except Exception as exc:
            print(f"OCR extraction failed: {exc}")
            return ""
