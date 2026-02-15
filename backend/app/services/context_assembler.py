"""Context assembly for RAG responses."""

from typing import List, Dict, Any, Optional
from app.core.config import settings


class ContextAssembler:
    """Assemble final context from retrieved chunks."""

    def assemble(self, docs: List[Dict[str, Any]], doc_names: Optional[Dict[str, str]] = None) -> List[str]:
        """Return a list of context strings with document source labels.

        Args:
            docs: List of retrieved document chunks
            doc_names: Optional mapping of doc_id -> filename for labeling
        """
        contexts = []
        seen = set()
        for doc in docs[:settings.RERANK_TOP_K]:
            parent_text = doc.get("parent_text") or ""
            child_text = doc.get("text") or ""
            text = parent_text or child_text
            if not text.strip():
                continue
            if text in seen:
                continue
            seen.add(text)

            # If parent is available and child differs, include child as
            # a focused excerpt so the LLM can locate the specific answer.
            if (parent_text and child_text
                    and child_text.strip() != parent_text.strip()
                    and len(parent_text) > len(child_text) * 2):
                combined = f"{parent_text}\n\n[Relevant excerpt]\n{child_text}"
            else:
                combined = text

            # Add document source label so the LLM knows which doc this is from
            metadata = doc.get("metadata", {})
            doc_id = metadata.get("doc_id", "")
            page = metadata.get("page", "")

            source_parts = []
            if doc_id and doc_names and doc_id in doc_names:
                source_parts.append(f"Document: {doc_names[doc_id]}")
            if page:
                source_parts.append(f"Page {page}")

            if source_parts:
                label = f"[{', '.join(source_parts)}]"
                contexts.append(f"{label}\n{combined}")
            else:
                contexts.append(combined)
        return contexts
