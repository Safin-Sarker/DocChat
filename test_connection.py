"""Test script to verify all connections are working."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core.config import settings
from app.models.pinecone_store import PineconeStore
import asyncio


async def test_pinecone():
    """Test Pinecone connection."""
    print("\n=== Testing Pinecone Connection ===")
    try:
        store = PineconeStore()
        stats = store.get_stats()
        print("[OK] Pinecone connected successfully!")
        print(f"   Index: {stats.get('index_name')}")
        print(f"   Total vectors: {stats.get('total_vectors', 0)}")
        print(f"   Dimension: {stats.get('dimension')}")
        return True
    except Exception as e:
        print(f"[FAIL] Pinecone connection failed: {e}")
        return False


async def test_openai():
    """Test OpenAI API."""
    print("\n=== Testing OpenAI API ===")
    try:
        import openai

        openai.api_key = settings.OPENAI_API_KEY

        # Test embedding
        response = openai.embeddings.create(model="text-embedding-ada-002", input="test")
        print("[OK] OpenAI API working!")
        print(f"   Embedding dimension: {len(response.data[0].embedding)}")
        return True
    except Exception as e:
        print(f"[FAIL] OpenAI API failed: {e}")
        return False


async def test_openai_reranker():
    """Test OpenAI reranker (embedding-based)."""
    print("\n=== Testing OpenAI Reranker ===")
    try:
        from app.services.reranker import Reranker

        reranker = Reranker()
        docs = [
            {"text": "alpha document about medical training", "metadata": {"id": "a"}},
            {"text": "beta document about emergency response", "metadata": {"id": "b"}},
        ]
        reranked = await reranker.rerank("medical training", docs, top_k=2)
        print("[OK] OpenAI reranker working!")
        print(f"   Reranked {len(reranked)} documents")
        return True
    except Exception as e:
        print(f"[FAIL] OpenAI reranker failed: {e}")
        return False


def test_neo4j():
    """Test Neo4j connection."""
    print("\n=== Testing Neo4j Connection ===")
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()

        driver.close()
        print("[OK] Neo4j connected successfully!")
        print(f"   URI: {settings.NEO4J_URI}")
        return True
    except Exception as e:
        print(f"[FAIL] Neo4j connection failed: {e}")
        print("   Make sure Neo4j is running: docker-compose up -d")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("DocChat System Connection Tests")
    print("=" * 50)

    results = {
        "pinecone": await test_pinecone(),
        "openai": await test_openai(),
        "openai_reranker": await test_openai_reranker(),
        "neo4j": test_neo4j(),
    }

    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    for service, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{service.upper():15} : {status}")

    print("\n")

    # Check critical services
    critical = ["pinecone", "openai", "neo4j"]
    all_critical_passed = all(results[s] for s in critical)

    if all_critical_passed:
        print("[OK] All critical services are working!")
        print("   Ready to start implementation!")
    else:
        print("[WARN] Some critical services failed.")
        print("   Please fix the issues above before continuing.")

    return all_critical_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
