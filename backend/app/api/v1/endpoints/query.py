"""Query endpoint for RAG responses."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.query import QueryRequest, QueryResponse
from app.services.advanced_rag import AdvancedRAGService
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

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
    logger.info(f"Query received from user {user_id}: {payload.query[:100]}")

    try:
        service = AdvancedRAGService()
        result = await service.answer(payload.query, user_id=user_id, chat_history=payload.chat_history)
        logger.info(f"Query answered: {len(result.get('contexts', []))} contexts, {len(result.get('entities', []))} entities")
        return QueryResponse(**result)
    except Exception as exc:
        logger.error(f"Query failed: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
