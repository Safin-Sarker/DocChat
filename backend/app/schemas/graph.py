"""Graph schemas for graph queries."""

from typing import List, Dict, Any
from pydantic import BaseModel


class GraphQueryRequest(BaseModel):
    """Request payload for graph queries."""

    entities: List[str]
    max_depth: int = 2
    limit: int = 10


class GraphQueryResponse(BaseModel):
    """Response payload for graph queries."""

    nodes: List[Dict[str, Any]]
