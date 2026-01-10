"""OCR service for scanned documents."""

from PIL import Image
import pytesseract


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
