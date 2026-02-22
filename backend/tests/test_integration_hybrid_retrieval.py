"""Integration tests for HybridRetrieval — inject mock stores."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import mock_pinecone_matches
from app.services.hybrid_retrieval import HybridRetrieval


@pytest.fixture()
def mock_deps():
    pinecone_store = AsyncMock()
    graph_store = MagicMock()
    query_expander = MagicMock()
    entity_extractor = MagicMock()

    # Defaults: expander returns original query, entity extractor returns empty
    query_expander.expand.return_value = ["test query"]
    entity_extractor.extract_entities.return_value = []
    graph_store.query_related_entities.return_value = []

    return pinecone_store, graph_store, query_expander, entity_extractor


@pytest.fixture()
def retrieval(mock_deps):
    ps, gs, qe, ee = mock_deps
    return HybridRetrieval(
        pinecone_store=ps,
        graph_store=gs,
        query_expander=qe,
        entity_extractor=ee,
    )


@pytest.mark.asyncio
async def test_retrieve_single_doc(retrieval, mock_deps):
    ps, gs, qe, ee = mock_deps
    matches = mock_pinecone_matches([
        {"id": "c1", "score": 0.9, "text": "chunk one content here"},
        {"id": "c2", "score": 0.8, "text": "chunk two content here"},
    ])
    ps.query_by_text.return_value = matches

    results = await retrieval.retrieve("test query", doc_ids=["doc-1"])
    assert len(results) == 2
    assert results[0]["id"] == "c1"
    assert "text" in results[0]


@pytest.mark.asyncio
async def test_retrieve_multi_doc_balanced(retrieval, mock_deps):
    ps, gs, qe, ee = mock_deps

    async def per_doc_query(q, top_k, user_id=None, doc_ids=None):
        doc_id = doc_ids[0] if doc_ids else "unknown"
        return mock_pinecone_matches([
            {"id": f"{doc_id}-c1", "score": 0.9, "text": f"content from {doc_id}", "doc_id": doc_id}
        ])

    ps.query_by_text.side_effect = per_doc_query

    results = await retrieval.retrieve("test query", doc_ids=["doc-A", "doc-B"])
    ids = {r["id"] for r in results}
    assert "doc-A-c1" in ids
    assert "doc-B-c1" in ids


@pytest.mark.asyncio
async def test_retrieve_deduplicates(retrieval, mock_deps):
    ps, gs, qe, ee = mock_deps
    # Expander returns two queries that yield same chunk IDs
    qe.expand.return_value = ["q1", "q2"]
    matches = mock_pinecone_matches([
        {"id": "dup-1", "score": 0.9, "text": "duplicate content here"},
    ])
    ps.query_by_text.return_value = matches

    results = await retrieval.retrieve("q1")
    # Even though 2 queries yielded the same ID, only 1 result
    assert len(results) == 1


@pytest.mark.asyncio
async def test_retrieve_includes_graph_nodes(retrieval, mock_deps):
    ps, gs, qe, ee = mock_deps
    ps.query_by_text.return_value = []
    ee.extract_entities.return_value = ["Python"]
    gs.query_related_entities.return_value = [{"label": "Python"}]

    results = await retrieval.retrieve("tell me about Python")
    graph_results = [r for r in results if r["id"].startswith("graph:")]
    assert len(graph_results) == 1
    assert graph_results[0]["text"] == "Python"


@pytest.mark.asyncio
async def test_retrieve_empty_results(retrieval, mock_deps):
    ps, gs, qe, ee = mock_deps
    ps.query_by_text.return_value = []
    results = await retrieval.retrieve("nothing relevant")
    assert results == []
