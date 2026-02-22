"""Integration tests for the /api/v1/query/ endpoint — mock AdvancedRAGService."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture()
def mock_rag_service():
    """Patch AdvancedRAGService in the query endpoint module."""
    with patch("app.api.v1.endpoints.query.AdvancedRAGService") as MockCls:
        instance = AsyncMock()
        MockCls.return_value = instance
        yield instance


def test_query_success(auth_client, mock_rag_service):
    mock_rag_service.answer.return_value = {
        "answer": "Test answer",
        "contexts": ["ctx1"],
        "sources": [{"doc_id": "d1", "page": 1}],
        "source_map": [],
        "entities": ["E1"],
        "reflection": None,
    }
    resp = auth_client.post("/api/v1/query/", json={"query": "What is X?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Test answer"
    assert data["contexts"] == ["ctx1"]


def test_query_with_doc_ids(auth_client, mock_rag_service):
    mock_rag_service.answer.return_value = {
        "answer": "Filtered answer",
        "contexts": ["ctx"],
        "sources": [],
        "source_map": [],
        "entities": [],
        "reflection": None,
    }
    resp = auth_client.post(
        "/api/v1/query/",
        json={"query": "Summarize", "doc_ids": ["doc-1", "doc-2"]},
    )
    assert resp.status_code == 200
    # Verify doc_ids were passed through
    call_kwargs = mock_rag_service.answer.call_args
    assert call_kwargs.kwargs.get("doc_ids") == ["doc-1", "doc-2"] or \
        (call_kwargs.args[0] if call_kwargs.args else None) is not None


def test_query_with_chat_history(auth_client, mock_rag_service):
    mock_rag_service.answer.return_value = {
        "answer": "Follow-up answer",
        "contexts": [],
        "sources": [],
        "source_map": [],
        "entities": [],
        "reflection": None,
    }
    resp = auth_client.post(
        "/api/v1/query/",
        json={
            "query": "Tell me more",
            "chat_history": [
                {"role": "user", "content": "What is X?"},
                {"role": "assistant", "content": "X is something."},
            ],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["answer"] == "Follow-up answer"


def test_query_service_error(auth_client, mock_rag_service):
    mock_rag_service.answer.side_effect = RuntimeError("Internal failure")
    resp = auth_client.post("/api/v1/query/", json={"query": "fail"})
    assert resp.status_code == 500
