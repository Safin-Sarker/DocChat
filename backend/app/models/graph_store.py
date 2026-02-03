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
        with self.driver.session() as session:
            # Create index on user_id and name for faster lookups
            session.run(
                "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.user_id, e.name)"
            )

    def upsert_entities(self, entities: List[str], doc_id: str, user_id: Optional[str] = None):
        """Upsert entity nodes for a document.

        Args:
            entities: List of entity names
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation
        """
        if not entities:
            return

        if user_id:
            # Multi-tenant: entities are scoped to user
            query = (
                "UNWIND $entities AS name "
                "MERGE (e:Entity {name: name, user_id: $user_id}) "
                "ON CREATE SET e.created_at = timestamp() "
                "SET e.doc_ids = coalesce(e.doc_ids, []) + $doc_id"
            )
            with self.driver.session() as session:
                session.run(query, entities=entities, doc_id=doc_id, user_id=user_id)
        else:
            # Single-tenant fallback
            query = (
                "UNWIND $entities AS name "
                "MERGE (e:Entity {name: name}) "
                "ON CREATE SET e.created_at = timestamp() "
                "SET e.doc_ids = coalesce(e.doc_ids, []) + $doc_id"
            )
            with self.driver.session() as session:
                session.run(query, entities=entities, doc_id=doc_id)

    def create_relationship(self, source: str, target: str, rel_type: str, doc_id: str, user_id: Optional[str] = None):
        """Create a relationship between two entities.

        Args:
            source: Source entity name
            target: Target entity name
            rel_type: Relationship type
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation
        """
        if user_id:
            query = (
                "MERGE (a:Entity {name: $source, user_id: $user_id}) "
                "MERGE (b:Entity {name: $target, user_id: $user_id}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                "SET r.doc_id = $doc_id, r.user_id = $user_id"
            )
            with self.driver.session() as session:
                session.run(query, source=source, target=target, doc_id=doc_id, user_id=user_id)
        else:
            query = (
                "MERGE (a:Entity {name: $source}) "
                "MERGE (b:Entity {name: $target}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                "SET r.doc_id = $doc_id"
            )
            with self.driver.session() as session:
                session.run(query, source=source, target=target, doc_id=doc_id)

    def delete_by_doc_id(self, doc_id: str, user_id: Optional[str] = None):
        """Delete all document references from graph.

        Args:
            doc_id: Document ID to delete
            user_id: User ID for multi-tenant isolation
        """
        with self.driver.session() as session:
            if user_id:
                # Multi-tenant: only delete user's entities
                session.run("""
                    MATCH (e:Entity {user_id: $user_id})
                    WHERE $doc_id IN e.doc_ids
                    SET e.doc_ids = [id IN e.doc_ids WHERE id <> $doc_id]
                    WITH e
                    WHERE size(e.doc_ids) = 0
                    DETACH DELETE e
                """, doc_id=doc_id, user_id=user_id)

                session.run("""
                    MATCH ()-[r:RELATED_TO {doc_id: $doc_id, user_id: $user_id}]-()
                    DELETE r
                """, doc_id=doc_id, user_id=user_id)
            else:
                # Single-tenant fallback
                session.run("""
                    MATCH (e:Entity)
                    WHERE $doc_id IN e.doc_ids
                    SET e.doc_ids = [id IN e.doc_ids WHERE id <> $doc_id]
                    WITH e
                    WHERE size(e.doc_ids) = 0
                    DETACH DELETE e
                """, doc_id=doc_id)

                session.run("""
                    MATCH ()-[r:RELATED_TO {doc_id: $doc_id}]-()
                    DELETE r
                """, doc_id=doc_id)

    def query_related_entities(
        self,
        seed_entities: List[str],
        max_depth: int = 2,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query related entities using graph traversal.

        Args:
            seed_entities: List of seed entity names
            max_depth: Maximum traversal depth
            limit: Maximum number of results
            user_id: User ID for multi-tenant isolation
        """
        if not seed_entities:
            return []

        # Normalize seeds to uppercase for case-insensitive matching
        normalized_seeds = [s.upper() for s in seed_entities]

        try:
            if user_id:
                # Use native Cypher variable-length path instead of APOC
                query = (
                    "MATCH (seed:Entity) "
                    "WHERE toUpper(seed.name) IN $seeds AND seed.user_id = $user_id "
                    "OPTIONAL MATCH (seed)-[*1.." + str(max_depth) + "]-(related:Entity) "
                    "WHERE related.user_id = $user_id "
                    "WITH COLLECT(DISTINCT seed) + COLLECT(DISTINCT related) AS allNodes "
                    "UNWIND allNodes AS n "
                    "WITH n WHERE n IS NOT NULL "
                    "RETURN DISTINCT id(n) AS id, n.name AS name, labels(n)[0] AS type "
                    "LIMIT $limit"
                )
                with self.driver.session() as session:
                    result = session.run(query, seeds=normalized_seeds, limit=limit, user_id=user_id)
                    return [
                        {
                            "id": str(record["id"]),
                            "label": record["name"],
                            "type": record["type"] or "entity",
                            "properties": {}
                        }
                        for record in result
                    ]
            else:
                query = (
                    "MATCH (seed:Entity) WHERE toUpper(seed.name) IN $seeds "
                    "OPTIONAL MATCH (seed)-[*1.." + str(max_depth) + "]-(related:Entity) "
                    "WITH COLLECT(DISTINCT seed) + COLLECT(DISTINCT related) AS allNodes "
                    "UNWIND allNodes AS n "
                    "WITH n WHERE n IS NOT NULL "
                    "RETURN DISTINCT id(n) AS id, n.name AS name, labels(n)[0] AS type "
                    "LIMIT $limit"
                )
                with self.driver.session() as session:
                    result = session.run(query, seeds=normalized_seeds, limit=limit)
                    return [
                        {
                            "id": str(record["id"]),
                            "label": record["name"],
                            "type": record["type"] or "entity",
                            "properties": {}
                        }
                        for record in result
                    ]
        except Exception as e:
            print(f"Graph query error: {e}")
            return []
