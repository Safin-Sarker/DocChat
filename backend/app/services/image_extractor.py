"""Image extraction service for PDFs."""

from typing import List, Dict, Any, Optional
from pdf2image import convert_from_path
from PIL import Image
import io
import uuid
from app.services.storage_service import StorageService


class ImageExtractor:
    """Extract page images from PDFs and store them."""

    def __init__(self, storage_service: Optional[StorageService] = None):
        """Initialize with an optional storage service."""
        self.storage_service = storage_service or StorageService()

    async def extract_page_images(self, pdf_path: str, doc_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Render PDF pages to images and upload them.

        Args:
            pdf_path: Path to PDF file
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation

        Returns:
            List of image metadata dictionaries
        """
        images_out: List[Dict[str, Any]] = []
        try:
            page_images = convert_from_path(pdf_path)
            for page_index, image in enumerate(page_images):
                image_id = str(uuid.uuid4())
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                image_url = await self.storage_service.upload_image(
                    image_data=buffer.getvalue(),
                    doc_id=doc_id,
                    image_id=image_id,
                    extension="png",
                    user_id=user_id
                )
                images_out.append({
                    "page": page_index + 1,
                    "image_id": image_id,
                    "url": image_url,
                    "width": image.width,
                    "height": image.height
                })
        except Exception as exc:
            print(f"Image extraction failed: {exc}")

        return images_out
