"""Query endpoint for RAG responses."""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from starlette.requests import Request
from app.schemas.query import QueryRequest, QueryResponse
from app.services.advanced_rag import AdvancedRAGService
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.limiter import limiter
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=QueryResponse)
@limiter.limit(settings.RATE_LIMIT_QUERY)
async def query_documents(
    request: Request,
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
        result = await service.answer(payload.query, user_id=user_id, chat_history=payload.chat_history, doc_ids=payload.doc_ids or None)
        logger.info(f"Query answered: {len(result.get('contexts', []))} contexts, {len(result.get('entities', []))} entities")
        AuditLog.log(
            action="QUERY_EXECUTED",
            resource_type="query",
            user_id=user_id,
            details={"query": payload.query[:200], "doc_ids": payload.doc_ids},
            ip_address=request.client.host if request.client else None,
        )
        return QueryResponse(**result)
    except Exception as exc:
        logger.error(f"Query failed: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/stream")
@limiter.limit(settings.RATE_LIMIT_QUERY_STREAM)
async def query_documents_stream(
    request: Request,
    payload: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Stream an answer using Server-Sent Events (requires authentication)."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_id = current_user["user_id"]
    logger.info(f"Stream query from user {user_id}: {payload.query[:100]}")
    AuditLog.log(
        action="QUERY_STREAM_EXECUTED",
        resource_type="query",
        user_id=user_id,
        details={"query": payload.query[:200], "doc_ids": payload.doc_ids},
        ip_address=request.client.host if request.client else None,
    )

    async def event_generator():
        try:
            service = AdvancedRAGService()
            async for event_type, data in service.answer_stream(
                payload.query,
                user_id=user_id,
                chat_history=payload.chat_history,
                doc_ids=payload.doc_ids or None
            ):
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        except Exception as exc:
            logger.error(f"Streaming query failed: {exc}")
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
