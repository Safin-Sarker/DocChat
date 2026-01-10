"""Graph endpoints."""

from fastapi import APIRouter, HTTPException
from app.schemas.graph import GraphQueryRequest, GraphQueryResponse
from app.models.graph_store import GraphStore


router = APIRouter()


@router.post("/related", response_model=GraphQueryResponse)
async def related_entities(payload: GraphQueryRequest):
    """Return related entities using graph traversal."""
    entities = [e.strip() for e in payload.entities if e.strip()]
    if not entities:
        raise HTTPException(status_code=400, detail="Entities cannot be empty")

    store = GraphStore()
    try:
        nodes = store.query_related_entities(
            seed_entities=entities,
            max_depth=payload.max_depth,
            limit=payload.limit
        )
    finally:
        store.close()

    return GraphQueryResponse(nodes=nodes)
