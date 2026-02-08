"""Pydantic schemas for querying."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message for conversation history."""

    role: str
    content: str


class QueryRequest(BaseModel):
    """User query payload."""

    query: str
    chat_history: List[ChatMessage] = []


class ReflectionScore(BaseModel):
    """LLM-as-a-Judge quality evaluation scores."""

    faithfulness: float = 1.0
    relevance: float = 1.0
    completeness: float = 1.0
    coherence: float = 1.0
    conciseness: float = 1.0
    overall: float = 1.0
    verdict: str = "pass"
    feedback: str = ""
    was_regenerated: bool = False


class QueryResponse(BaseModel):
    """Query response payload."""

    answer: str
    contexts: List[str]
    sources: List[Dict[str, Any]]
    entities: List[str] = []
    reflection: Optional[ReflectionScore] = None
