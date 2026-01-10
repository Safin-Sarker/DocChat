"""Context assembly for RAG responses."""

from typing import List, Dict, Any
from app.core.config import settings


class ContextAssembler:
    """Assemble final context from retrieved chunks."""

    def assemble(self, docs: List[Dict[str, Any]]) -> List[str]:
        """Return a list of context strings."""
        contexts = []
        seen = set()
        for doc in docs[:settings.RERANK_TOP_K]:
            text = doc.get("parent_text") or doc.get("text") or ""
            if not text.strip():
                continue
            if text in seen:
                continue
            seen.add(text)
            contexts.append(text)
        return contexts
