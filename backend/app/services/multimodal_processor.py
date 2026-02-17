"""Multimodal document processing orchestrator."""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import uuid
from pathlib import Path
import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)
from app.services.chunking_service import ChunkingService
from app.services.ocr_service import OCRService
from app.services.image_extractor import ImageExtractor
from app.services.table_extractor import TableExtractor
from app.services.docx_extractor import DocxExtractor
from app.services.excel_extractor import ExcelExtractor
from app.services.graph_builder import GraphBuilder
from app.services.storage_service import StorageService
from app.models.pinecone_store import PineconeStore


class MultimodalProcessor:
    """Process supported documents into indexable multimodal content."""

    def __init__(
        self,
        chunking_service: Optional[ChunkingService] = None,
        pinecone_store: Optional[PineconeStore] = None,
        storage_service: Optional[StorageService] = None,
        image_extractor: Optional[ImageExtractor] = None,
        table_extractor: Optional[TableExtractor] = None,
        docx_extractor: Optional[DocxExtractor] = None,
        excel_extractor: Optional[ExcelExtractor] = None,
        ocr_service: Optional[OCRService] = None,
        graph_builder: Optional[GraphBuilder] = None,
    ):
        self.chunking_service = chunking_service or ChunkingService()
        self.pinecone_store = pinecone_store or PineconeStore()
        self.storage_service = storage_service or StorageService()
        self.image_extractor = image_extractor or ImageExtractor(self.storage_service)
        self.table_extractor = table_extractor or TableExtractor()
        self.docx_extractor = docx_extractor or DocxExtractor()
        self.excel_extractor = excel_extractor or ExcelExtractor()
        self.ocr_service = ocr_service or OCRService()
        self.graph_builder = graph_builder or GraphBuilder()

    async def process_document(
        self,
        file_path: str,
        filename: str,
        file_type: Optional[str] = None,
        doc_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a document and index extracted content.

        Args:
            file_path: Path to the file to process
            filename: Original filename
            file_type: Optional normalized file type (pdf, docx, xlsx, image)
            doc_id: Optional document ID
            user_id: User ID for multi-tenant isolation

        Returns:
            Summary of processing results
        """
        document_id = doc_id or str(uuid.uuid4())
        normalized_file_type = (file_type or self._detect_file_type(filename)).lower()
        if normalized_file_type not in {"pdf", "docx", "xlsx", "image"}:
            raise ValueError(f"Unsupported file type: {normalized_file_type}")

        logger.info(f"[{document_id}] Uploading file to storage...")
        storage_path = await self.storage_service.upload_file(
            file_path=file_path,
            filename=filename,
            doc_id=document_id,
            user_id=user_id
        )

        if normalized_file_type == "pdf":
            return await self._process_pdf(document_id, file_path, storage_path, user_id=user_id)
        if normalized_file_type == "docx":
            return await self._process_docx(document_id, file_path, storage_path, user_id=user_id)
        if normalized_file_type == "xlsx":
            return await self._process_xlsx(document_id, file_path, storage_path, user_id=user_id)
        return await self._process_image(document_id, file_path, storage_path, user_id=user_id)

    async def _process_pdf(
        self,
        document_id: str,
        file_path: str,
        storage_path: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[{document_id}] Extracting PDF text from pages...")
        pages = await asyncio.to_thread(self._extract_text_pages, file_path)
        chunking_stats = await self._chunk_index_and_graph(pages, document_id, user_id=user_id)

        logger.info(f"[{document_id}] Extracting PDF tables...")
        table_entries = await asyncio.to_thread(self.table_extractor.extract_tables, file_path)
        table_upserted = await self._index_tables(table_entries, document_id, user_id=user_id)

        logger.info(f"[{document_id}] Extracting PDF page images...")
        images = await self.image_extractor.extract_page_images(file_path, document_id, user_id=user_id)

        return {
            "doc_id": document_id,
            "storage_path": storage_path,
            "pages": len(pages),
            "parent_chunks": chunking_stats["parent_chunks"],
            "child_chunks": chunking_stats["child_chunks"],
            "table_chunks": table_upserted,
            "images": len(images),
            "upserted_vectors": chunking_stats["text_upserted"] + table_upserted,
        }

    async def _process_docx(
        self,
        document_id: str,
        file_path: str,
        storage_path: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[{document_id}] Extracting DOCX text...")
        pages = await asyncio.to_thread(self.docx_extractor.extract_pages, file_path)
        chunking_stats = await self._chunk_index_and_graph(pages, document_id, user_id=user_id)

        logger.info(f"[{document_id}] Extracting DOCX tables...")
        table_entries = await asyncio.to_thread(self.docx_extractor.extract_tables, file_path)
        table_upserted = await self._index_tables(table_entries, document_id, user_id=user_id)

        return {
            "doc_id": document_id,
            "storage_path": storage_path,
            "pages": len(pages),
            "parent_chunks": chunking_stats["parent_chunks"],
            "child_chunks": chunking_stats["child_chunks"],
            "table_chunks": table_upserted,
            "images": 0,
            "upserted_vectors": chunking_stats["text_upserted"] + table_upserted,
        }

    async def _process_xlsx(
        self,
        document_id: str,
        file_path: str,
        storage_path: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[{document_id}] Extracting XLSX sheet content...")
        pages = await asyncio.to_thread(self.excel_extractor.extract_sheets, file_path)
        chunking_stats = await self._chunk_index_and_graph(pages, document_id, user_id=user_id)

        logger.info(f"[{document_id}] Extracting XLSX table representations...")
        table_entries = await asyncio.to_thread(self.excel_extractor.extract_tables, file_path)
        table_upserted = await self._index_tables(table_entries, document_id, user_id=user_id)

        return {
            "doc_id": document_id,
            "storage_path": storage_path,
            "pages": len(pages),
            "parent_chunks": chunking_stats["parent_chunks"],
            "child_chunks": chunking_stats["child_chunks"],
            "table_chunks": table_upserted,
            "images": 0,
            "upserted_vectors": chunking_stats["text_upserted"] + table_upserted,
        }

    async def _process_image(
        self,
        document_id: str,
        file_path: str,
        storage_path: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[{document_id}] Running OCR for image...")
        ocr_text = await asyncio.to_thread(self._extract_image_text, file_path)
        pages = [{"page_num": 1, "text": ocr_text}] if ocr_text.strip() else []
        chunking_stats = await self._chunk_index_and_graph(pages, document_id, user_id=user_id)

        image_entries = await self._upload_original_image(file_path, document_id, user_id=user_id)

        return {
            "doc_id": document_id,
            "storage_path": storage_path,
            "pages": 1,
            "parent_chunks": chunking_stats["parent_chunks"],
            "child_chunks": chunking_stats["child_chunks"],
            "table_chunks": 0,
            "images": len(image_entries),
            "upserted_vectors": chunking_stats["text_upserted"],
        }

    async def _chunk_index_and_graph(
        self,
        pages: List[Dict[str, Any]],
        document_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Create chunks, index text vectors, and optionally build graph."""
        if not pages:
            return {"parent_chunks": 0, "child_chunks": 0, "text_upserted": 0}

        parent_chunks, child_chunks = await asyncio.to_thread(
            self.chunking_service.process_document_pages, pages
        )
        logger.info(
            f"[{document_id}] Created {len(parent_chunks)} parent and {len(child_chunks)} child chunks"
        )

        if parent_chunks:
            try:
                logger.info(f"[{document_id}] Building knowledge graph...")
                await asyncio.to_thread(
                    self.graph_builder.build_from_texts,
                    [chunk.text for chunk in parent_chunks],
                    document_id,
                    user_id
                )
            except Exception as exc:
                logger.warning(f"[{document_id}] Graph build failed: {exc}")
            finally:
                self.graph_builder.close()

        pinecone_payload = self.chunking_service.prepare_for_pinecone(
            parent_chunks=parent_chunks,
            child_chunks=child_chunks,
            doc_id=document_id,
            user_id=user_id
        )
        upserted = await self._index_text_chunks(pinecone_payload["child_data"], user_id=user_id)
        logger.info(f"[{document_id}] Upserted {upserted} text vectors")

        return {
            "parent_chunks": len(parent_chunks),
            "child_chunks": len(child_chunks),
            "text_upserted": upserted,
        }

    def _extract_image_text(self, file_path: str) -> str:
        """Extract OCR text from an image file."""
        try:
            with Image.open(file_path) as image:
                return self.ocr_service.extract_text_from_image(image.convert("RGB"))
        except Exception as exc:
            print(f"Image OCR failed: {exc}")
            return ""

    async def _upload_original_image(
        self,
        file_path: str,
        doc_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Upload original image and return image metadata entry."""
        extension = Path(file_path).suffix.lower().replace(".", "") or "png"
        image_id = str(uuid.uuid4())
        try:
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()
            with Image.open(file_path) as image:
                width, height = image.size
            image_url = await self.storage_service.upload_image(
                image_data=image_data,
                doc_id=doc_id,
                image_id=image_id,
                extension=extension,
                user_id=user_id
            )
            return [{
                "page": 1,
                "image_id": image_id,
                "url": image_url,
                "width": width,
                "height": height,
            }]
        except Exception as exc:
            print(f"Image upload failed: {exc}")
            return []

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension as a fallback."""
        extension = Path(filename).suffix.lower()
        if extension == ".pdf":
            return "pdf"
        if extension == ".docx":
            return "docx"
        if extension == ".xlsx":
            return "xlsx"
        if extension in {".png", ".jpg", ".jpeg", ".gif"}:
            return "image"
        return ""

    def _extract_text_pages(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from each PDF page with OCR fallback."""
        pages: List[Dict[str, Any]] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_index, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if not text.strip():
                        text = self._ocr_page(page)
                    pages.append({
                        "page_num": page_index + 1,
                        "text": text
                    })
        except Exception as exc:
            print(f"Text extraction failed: {exc}")

        return pages

    def _ocr_page(self, page) -> str:
        """Run OCR on a pdfplumber page."""
        try:
            page_image = page.to_image(resolution=200)
            pil_image = page_image.original
            return self.ocr_service.extract_text_from_image(pil_image)
        except Exception as exc:
            print(f"OCR page render failed: {exc}")
            return ""

    async def _index_text_chunks(self, child_data: List[Dict[str, Any]], user_id: Optional[str] = None) -> int:
        """Index child chunks in Pinecone using batch embeddings."""
        if not child_data:
            return 0

        # Batch embed all texts at once instead of one-by-one
        texts = [item["child"].text for item in child_data]
        embeddings = await self.pinecone_store.get_embeddings_batch(texts)

        vectors = []
        for item, embedding in zip(child_data, embeddings):
            child = item["child"]
            metadata = {
                "doc_id": item["doc_id"],
                "parent_id": item["parent_id"],
                "page": child.page,
                "type": "text",
                "text": child.text,
                "parent_text": item["parent_text"],
            }
            if user_id:
                metadata["user_id"] = user_id
            vectors.append({
                "id": child.id,
                "values": embedding,
                "metadata": metadata
            })

        result = await self.pinecone_store.upsert_vectors(vectors)
        return result.get("upserted", 0)

    async def _index_tables(self, tables: List[Dict[str, Any]], doc_id: str, user_id: Optional[str] = None) -> int:
        """Index extracted tables as text chunks using batch embeddings."""
        if not tables:
            return 0

        # Batch embed all table texts at once
        texts = [table["markdown"] for table in tables]
        embeddings = await self.pinecone_store.get_embeddings_batch(texts)

        vectors = []
        for table, embedding in zip(tables, embeddings):
            table_id = str(uuid.uuid4())
            metadata = {
                "doc_id": doc_id,
                "page": table["page"],
                "type": "table",
                "text": table["markdown"],
                "table_index": table["table_index"],
            }
            for key, value in table.items():
                if key in {"markdown", "raw", "page", "table_index"}:
                    continue
                metadata[key] = value
            if user_id:
                metadata["user_id"] = user_id
            vectors.append({
                "id": table_id,
                "values": embedding,
                "metadata": metadata
            })

        result = await self.pinecone_store.upsert_vectors(vectors)
        return result.get("upserted", 0)
