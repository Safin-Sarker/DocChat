"""Neo4j graph store wrapper."""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from app.core.config import settings


class GraphStore:
    """Wrapper for Neo4j operations."""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        """Close Neo4j driver."""
        self.driver.close()

    def ensure_constraints(self):
        """Ensure basic constraints/indexes exist."""
        query = "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
        with self.driver.session() as session:
            session.run(query)

    def upsert_entities(self, entities: List[str], doc_id: str):
        """Upsert entity nodes for a document."""
        if not entities:
            return
        query = (
            "UNWIND $entities AS name "
            "MERGE (e:Entity {name: name}) "
            "ON CREATE SET e.created_at = timestamp() "
            "SET e.doc_ids = coalesce(e.doc_ids, []) + $doc_id"
        )
        with self.driver.session() as session:
            session.run(query, entities=entities, doc_id=doc_id)

    def create_relationship(self, source: str, target: str, rel_type: str, doc_id: str):
        """Create a relationship between two entities."""
        query = (
            "MERGE (a:Entity {name: $source}) "
            "MERGE (b:Entity {name: $target}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r.doc_id = $doc_id"
        )
        with self.driver.session() as session:
            session.run(query, source=source, target=target, doc_id=doc_id)

    def query_related_entities(
        self,
        seed_entities: List[str],
        max_depth: int = 2,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query related entities using graph traversal."""
        if not seed_entities:
            return []
        query = (
            "MATCH (seed:Entity) WHERE seed.name IN $seeds "
            "CALL apoc.path.subgraphAll(seed, {maxLevel: $depth}) YIELD nodes, relationships "
            "UNWIND nodes AS n "
            "RETURN DISTINCT n.name AS name "
            "LIMIT $limit"
        )
        with self.driver.session() as session:
            result = session.run(query, seeds=seed_entities, depth=max_depth, limit=limit)
            return [{"name": record["name"]} for record in result]
