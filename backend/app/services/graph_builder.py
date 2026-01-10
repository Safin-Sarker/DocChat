"""Build Neo4j graph from document content."""

from typing import List
from app.models.graph_store import GraphStore
from app.services.entity_extractor import EntityExtractor


class GraphBuilder:
    """Service to build a knowledge graph from text chunks."""

    def __init__(
        self,
        graph_store: GraphStore | None = None,
        entity_extractor: EntityExtractor | None = None,
    ):
        self.graph_store = graph_store or GraphStore()
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.graph_store.ensure_constraints()

    def build_from_texts(self, texts: List[str], doc_id: str):
        """Extract entities and build co-occurrence relationships."""
        for text in texts:
            entities = self.entity_extractor.extract_entities(text)
            if not entities:
                continue
            self.graph_store.upsert_entities(entities, doc_id)
            for i, source in enumerate(entities):
                for target in entities[i + 1:]:
                    self.graph_store.create_relationship(source, target, "RELATED_TO", doc_id)

    def close(self):
        """Close underlying resources."""
        self.graph_store.close()
