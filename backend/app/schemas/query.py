"""Pydantic schemas for querying."""

from typing import List, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """User query payload."""

    query: str


class QueryResponse(BaseModel):
    """Query response payload."""

    answer: str
    contexts: List[str]
    sources: List[Dict[str, Any]]
