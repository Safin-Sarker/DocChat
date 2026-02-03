"""Multimodal document processing orchestrator."""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import uuid
import pdfplumber

logger = logging.getLogger(__name__)
from app.services.chunking_service import ChunkingService
from app.services.ocr_service import OCRService
from app.services.image_extractor import ImageExtractor
from app.services.table_extractor import TableExtractor
from app.services.graph_builder import GraphBuilder
from app.services.storage_service import StorageService
from app.models.pinecone_store import PineconeStore


class MultimodalProcessor:
    """Process PDFs into text, tables, and images for RAG indexing."""

    def __init__(
        self,
        chunking_service: Optional[ChunkingService] = None,
        pinecone_store: Optional[PineconeStore] = None,
        storage_service: Optional[StorageService] = None,
        image_extractor: Optional[ImageExtractor] = None,
        table_extractor: Optional[TableExtractor] = None,
        ocr_service: Optional[OCRService] = None,
        graph_builder: Optional[GraphBuilder] = None,
    ):
        self.chunking_service = chunking_service or ChunkingService()
        self.pinecone_store = pinecone_store or PineconeStore()
        self.storage_service = storage_service or StorageService()
        self.image_extractor = image_extractor or ImageExtractor(self.storage_service)
        self.table_extractor = table_extractor or TableExtractor()
        self.ocr_service = ocr_service or OCRService()
        self.graph_builder = graph_builder or GraphBuilder()

    async def process_document(
        self,
        file_path: str,
        filename: str,
        doc_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a PDF document and index extracted content.

        Args:
            file_path: Path to the file to process
            filename: Original filename
            doc_id: Optional document ID
            user_id: User ID for multi-tenant isolation

        Returns:
            Summary of processing results
        """
        document_id = doc_id or str(uuid.uuid4())
        logger.info(f"[{document_id}] Uploading file to storage...")
        storage_path = await self.storage_service.upload_file(
            file_path=file_path,
            filename=filename,
            doc_id=document_id,
            user_id=user_id
        )

        # Run blocking PDF operations in a thread to avoid blocking the event loop
        logger.info(f"[{document_id}] Extracting text from pages...")
        pages = await asyncio.to_thread(self._extract_text_pages, file_path)
        logger.info(f"[{document_id}] Extracted {len(pages)} pages, chunking...")

        parent_chunks, child_chunks = await asyncio.to_thread(
            self.chunking_service.process_document_pages, pages
        )
        logger.info(f"[{document_id}] Created {len(parent_chunks)} parent, {len(child_chunks)} child chunks")

        if parent_chunks:
            try:
                logger.info(f"[{document_id}] Building knowledge graph...")
                await asyncio.to_thread(
                    self.graph_builder.build_from_texts,
                    [chunk.text for chunk in parent_chunks],
                    document_id,
                    user_id
                )
                logger.info(f"[{document_id}] Graph build complete")
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

        logger.info(f"[{document_id}] Indexing {len(pinecone_payload['child_data'])} text chunks to Pinecone...")
        upserted = await self._index_text_chunks(pinecone_payload["child_data"], user_id=user_id)
        logger.info(f"[{document_id}] Upserted {upserted} text vectors")

        logger.info(f"[{document_id}] Extracting tables...")
        table_entries = await asyncio.to_thread(self.table_extractor.extract_tables, file_path)
        table_upserted = await self._index_tables(table_entries, document_id, user_id=user_id)
        logger.info(f"[{document_id}] Upserted {table_upserted} table vectors")

        logger.info(f"[{document_id}] Extracting page images...")
        images = await self.image_extractor.extract_page_images(file_path, document_id, user_id=user_id)
        logger.info(f"[{document_id}] Extracted {len(images)} images")

        return {
            "doc_id": document_id,
            "storage_path": storage_path,
            "pages": len(pages),
            "parent_chunks": len(parent_chunks),
            "child_chunks": len(child_chunks),
            "table_chunks": table_upserted,
            "images": len(images),
            "upserted_vectors": upserted + table_upserted,
        }

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
            if user_id:
                metadata["user_id"] = user_id
            vectors.append({
                "id": table_id,
                "values": embedding,
                "metadata": metadata
            })

        result = await self.pinecone_store.upsert_vectors(vectors)
        return result.get("upserted", 0)
