"""Pydantic schemas for documents."""

from typing import List, Optional, Literal
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Response for document upload and processing."""

    doc_id: str
    storage_path: str
    pages: int
    parent_chunks: int
    child_chunks: int
    table_chunks: int
    images: int
    upserted_vectors: int


class DeleteDocumentResponse(BaseModel):
    """Response for document deletion."""

    status: Literal["deleted", "partial"]
    doc_id: str
    errors: Optional[List[str]] = None
