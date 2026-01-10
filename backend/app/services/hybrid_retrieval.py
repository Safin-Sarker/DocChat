"""Hybrid retrieval combining Pinecone semantic and Neo4j graph."""

from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.pinecone_store import PineconeStore
from app.models.graph_store import GraphStore
from app.services.query_expander import QueryExpander
from app.services.entity_extractor import EntityExtractor


class HybridRetrieval:
    """Retrieve candidate contexts from vector and graph stores."""

    def __init__(
        self,
        pinecone_store: Optional[PineconeStore] = None,
        graph_store: Optional[GraphStore] = None,
        query_expander: Optional[QueryExpander] = None,
        entity_extractor: Optional[EntityExtractor] = None,
    ):
        self.pinecone_store = pinecone_store or PineconeStore()
        self.graph_store = graph_store or GraphStore()
        self.query_expander = query_expander or QueryExpander()
        self.entity_extractor = entity_extractor or EntityExtractor()

    async def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve candidate chunks."""
        expanded_queries = self.query_expander.expand(query)
        results: List[Dict[str, Any]] = []
        seen_ids = set()

        for q in expanded_queries:
            matches = await self.pinecone_store.query_by_text(
                q,
                top_k=settings.SEMANTIC_TOP_K
            )
            for match in matches:
                if match["id"] in seen_ids:
                    continue
                seen_ids.add(match["id"])
                metadata = match.get("metadata", {})
                results.append({
                    "id": match["id"],
                    "score": match["score"],
                    "text": metadata.get("text", ""),
                    "parent_text": metadata.get("parent_text", ""),
                    "metadata": metadata,
                })

        entities = self.entity_extractor.extract_entities(query)
        graph_nodes = self.graph_store.query_related_entities(
            entities,
            max_depth=settings.GRAPH_MAX_DEPTH,
            limit=settings.GRAPH_MAX_DEPTH * 5
        )
        for node in graph_nodes:
            results.append({
                "id": f"graph:{node['name']}",
                "score": 0.0,
                "text": node["name"],
                "metadata": {"type": "graph_entity"}
            })

        return results
