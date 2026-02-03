"""Build Neo4j graph from document content."""

from typing import List, Optional
from app.models.graph_store import GraphStore
from app.services.entity_extractor import EntityExtractor


class GraphBuilder:
    """Service to build a knowledge graph from text chunks."""

    def __init__(
        self,
        graph_store: GraphStore | None = None,
        entity_extractor: EntityExtractor | None = None,
    ):
        self.available = False
        try:
            self.graph_store = graph_store or GraphStore()
            self.entity_extractor = entity_extractor or EntityExtractor()
            self.graph_store.ensure_constraints()
            self.available = True
        except Exception as exc:
            print(f"Neo4j unavailable, graph building disabled: {exc}")

    def build_from_texts(self, texts: List[str], doc_id: str, user_id: Optional[str] = None):
        """Extract entities and build co-occurrence relationships.

        Concatenates consecutive chunks into batches to reduce LLM calls.
        Skips silently if Neo4j is not available.
        """
        if not self.available:
            return

        MAX_BATCH_CHARS = 3000
        batches = []
        current_batch = ""

        for text in texts:
            if len(current_batch) + len(text) > MAX_BATCH_CHARS and current_batch:
                batches.append(current_batch)
                current_batch = ""
            current_batch += "\n" + text if current_batch else text

        if current_batch:
            batches.append(current_batch)

        for batch_text in batches:
            entities = self.entity_extractor.extract_entities(batch_text)
            if not entities:
                continue
            self.graph_store.upsert_entities(entities, doc_id, user_id=user_id)
            for i, source in enumerate(entities):
                for target in entities[i + 1:]:
                    self.graph_store.create_relationship(source, target, "RELATED_TO", doc_id, user_id=user_id)

    def close(self):
        """Close underlying resources."""
        if self.available:
            self.graph_store.close()
