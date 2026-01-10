"""Query endpoint for RAG responses."""

from fastapi import APIRouter, HTTPException
from app.schemas.query import QueryRequest, QueryResponse
from app.services.advanced_rag import AdvancedRAGService


router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query_documents(payload: QueryRequest):
    """Answer a user query using the RAG pipeline."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    service = AdvancedRAGService()
    result = await service.answer(payload.query)
    return QueryResponse(**result)
