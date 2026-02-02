"""Query endpoint for RAG responses."""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.query import QueryRequest, QueryResponse
from app.services.advanced_rag import AdvancedRAGService
from app.core.auth import get_current_user


router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Answer a user query using the RAG pipeline (requires authentication)."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_id = current_user["user_id"]
    service = AdvancedRAGService()
    result = await service.answer(payload.query, user_id=user_id)
    return QueryResponse(**result)
