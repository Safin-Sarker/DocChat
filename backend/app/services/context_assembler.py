"""Context assembly for RAG responses."""

from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings


class ContextAssembler:
    """Assemble final context from retrieved chunks."""

    def _process_doc(self, doc: Dict[str, Any], doc_names: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Extract text and metadata from a single doc chunk. Returns None if empty/duplicate."""
        parent_text = doc.get("parent_text") or ""
        child_text = doc.get("text") or ""
        text = parent_text or child_text
        if not text.strip():
            return None

        if (parent_text and child_text
                and child_text.strip() != parent_text.strip()
                and len(parent_text) > len(child_text) * 2):
            combined = f"{parent_text}\n\n[Relevant excerpt]\n{child_text}"
        else:
            combined = text

        metadata = doc.get("metadata", {})
        doc_id = metadata.get("doc_id", "")
        page = metadata.get("page", "")

        source_parts = []
        doc_name = ""
        if doc_id and doc_names and doc_id in doc_names:
            doc_name = doc_names[doc_id]
            source_parts.append(f"Document: {doc_name}")
        if page:
            source_parts.append(f"Page {page}")

        label = f"[{', '.join(source_parts)}]" if source_parts else ""

        return {
            "text": text,
            "combined": combined,
            "label": label,
            "doc_name": doc_name,
            "page": page,
        }

    def assemble(self, docs: List[Dict[str, Any]], doc_names: Optional[Dict[str, str]] = None) -> List[str]:
        """Return a list of context strings with document source labels.

        Args:
            docs: List of retrieved document chunks
            doc_names: Optional mapping of doc_id -> filename for labeling
        """
        contexts = []
        seen = set()
        for doc in docs[:settings.RERANK_TOP_K]:
            processed = self._process_doc(doc, doc_names)
            if not processed or processed["text"] in seen:
                continue
            seen.add(processed["text"])

            if processed["label"]:
                contexts.append(f"{processed['label']}\n{processed['combined']}")
            else:
                contexts.append(processed["combined"])
        return contexts

    def assemble_with_citations(
        self, docs: List[Dict[str, Any]], doc_names: Optional[Dict[str, str]] = None
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Return numbered contexts and a source map for citation linking.

        Each context is prefixed with [1], [2], etc.
        source_map[i] = {"index": i+1, "doc_name": ..., "page": ..., "text": snippet}

        Returns:
            Tuple of (contexts, source_map)
        """
        contexts = []
        source_map: List[Dict[str, Any]] = []
        seen = set()
        index = 0

        for doc in docs[:settings.RERANK_TOP_K]:
            processed = self._process_doc(doc, doc_names)
            if not processed or processed["text"] in seen:
                continue
            seen.add(processed["text"])
            index += 1

            if processed["label"]:
                contexts.append(f"[{index}] {processed['label']}\n{processed['combined']}")
            else:
                contexts.append(f"[{index}]\n{processed['combined']}")

            # Build a short snippet for the source map
            snippet = processed["combined"][:settings.CONTEXT_SNIPPET_LENGTH]
            if len(processed["combined"]) > settings.CONTEXT_SNIPPET_LENGTH:
                snippet += "..."

            source_map.append({
                "index": index,
                "doc_name": processed["doc_name"],
                "page": processed["page"],
                "text": snippet,
            })

        return contexts, source_map
