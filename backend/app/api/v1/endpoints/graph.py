"""Graph endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.graph import GraphQueryRequest, GraphQueryResponse
from app.models.graph_store import GraphStore
from app.core.auth import get_current_user


router = APIRouter()


@router.post("/related", response_model=GraphQueryResponse)
async def related_entities(
    payload: GraphQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Return related entities using graph traversal."""
    entities = [e.strip() for e in payload.entities if e.strip()]
    if not entities:
        raise HTTPException(status_code=400, detail="Entities cannot be empty")

    user_id = current_user["user_id"]
    store = GraphStore()
    try:
        nodes = store.query_related_entities(
            seed_entities=entities,
            max_depth=payload.max_depth,
            limit=payload.limit,
            user_id=user_id
        )
    finally:
        store.close()

    return GraphQueryResponse(nodes=nodes)
