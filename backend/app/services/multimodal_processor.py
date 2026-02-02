"""Multimodal document processing orchestrator."""

from typing import Dict, Any, List, Optional
import uuid
import pdfplumber
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
        storage_path = await self.storage_service.upload_file(
            file_path=file_path,
            filename=filename,
            doc_id=document_id,
            user_id=user_id
        )

        pages = self._extract_text_pages(file_path)
        parent_chunks, child_chunks = self.chunking_service.process_document_pages(pages)
        if parent_chunks:
            try:
                self.graph_builder.build_from_texts(
                    [chunk.text for chunk in parent_chunks],
                    document_id,
                    user_id=user_id
                )
            except Exception as exc:
                print(f"Graph build failed: {exc}")
            finally:
                self.graph_builder.close()

        pinecone_payload = self.chunking_service.prepare_for_pinecone(
            parent_chunks=parent_chunks,
            child_chunks=child_chunks,
            doc_id=document_id,
            user_id=user_id
        )

        upserted = await self._index_text_chunks(pinecone_payload["child_data"], user_id=user_id)
        table_entries = self.table_extractor.extract_tables(file_path)
        table_upserted = await self._index_tables(table_entries, document_id, user_id=user_id)
        images = await self.image_extractor.extract_page_images(file_path, document_id, user_id=user_id)

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
        """Index child chunks in Pinecone."""
        vectors = []
        for item in child_data:
            child = item["child"]
            embedding = await self.pinecone_store.get_embedding(child.text)
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
        """Index extracted tables as text chunks."""
        vectors = []
        for table in tables:
            table_id = str(uuid.uuid4())
            embedding = await self.pinecone_store.get_embedding(table["markdown"])
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

        if not vectors:
            return 0

        result = await self.pinecone_store.upsert_vectors(vectors)
        return result.get("upserted", 0)
