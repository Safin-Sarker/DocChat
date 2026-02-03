"""Image extraction service for PDFs."""

from typing import List, Dict, Any, Optional
from pdf2image import convert_from_path
from PIL import Image
import io
import uuid
import pdfplumber
from app.services.storage_service import StorageService


class ImageExtractor:
    """Extract page images from PDFs and store them."""

    def __init__(self, storage_service: Optional[StorageService] = None):
        """Initialize with an optional storage service."""
        self.storage_service = storage_service or StorageService()

    async def extract_page_images(self, pdf_path: str, doc_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Render PDF pages to images and upload them one at a time.

        Args:
            pdf_path: Path to PDF file
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation

        Returns:
            List of image metadata dictionaries
        """
        images_out: List[Dict[str, Any]] = []
        try:
            # Check poppler availability once before looping
            try:
                convert_from_path(pdf_path, first_page=1, last_page=1, dpi=72)
            except Exception as check_exc:
                if "poppler" in str(check_exc).lower():
                    print("Poppler not installed, skipping image extraction. Install poppler and add to PATH.")
                    return images_out
                raise

            # Get page count without loading images into memory
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)

            # Process one page at a time to avoid OOM on large PDFs
            for page_num in range(1, page_count + 1):
                try:
                    page_images = convert_from_path(
                        pdf_path,
                        first_page=page_num,
                        last_page=page_num,
                        dpi=150
                    )
                    if not page_images:
                        continue
                    image = page_images[0]
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
                        "page": page_num,
                        "image_id": image_id,
                        "url": image_url,
                        "width": image.width,
                        "height": image.height
                    })
                    # Free memory immediately
                    del image, page_images, buffer
                except Exception as page_exc:
                    print(f"Image extraction failed for page {page_num}: {page_exc}")
        except Exception as exc:
            print(f"Image extraction failed: {exc}")

        return images_out
