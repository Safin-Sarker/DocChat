"""Pydantic schemas for documents."""

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
