"""API v1 router."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, query, graph


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
