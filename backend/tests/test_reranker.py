"""Tests for app.services.reranker — Reranker static helpers."""

from app.services.reranker import Reranker


def test_cosine_similarity_identical():
    """Same vector returns 1.0."""
    vec = [1.0, 2.0, 3.0]
    assert abs(Reranker._cosine_similarity(vec, vec) - 1.0) < 1e-6


def test_cosine_similarity_orthogonal():
    """Orthogonal vectors return 0.0."""
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert abs(Reranker._cosine_similarity(a, b)) < 1e-6


def test_cosine_similarity_zero_vector():
    """Zero vector returns 0.0."""
    zero = [0.0, 0.0, 0.0]
    other = [1.0, 2.0, 3.0]
    assert Reranker._cosine_similarity(zero, other) == 0.0
    assert Reranker._cosine_similarity(other, zero) == 0.0


def test_balanced_select_single_doc():
    """Returns top_k from single document."""
    docs = [
        {"text": f"chunk {i}", "metadata": {"doc_id": "doc1"}}
        for i in range(5)
    ]
    result = Reranker._balanced_select(docs, top_k=3)
    assert len(result) == 3
    assert all(d["metadata"]["doc_id"] == "doc1" for d in result)


def test_balanced_select_multi_doc():
    """Each doc gets at least minimum representation."""
    docs = [
        {"text": "chunk A1", "metadata": {"doc_id": "A"}},
        {"text": "chunk A2", "metadata": {"doc_id": "A"}},
        {"text": "chunk A3", "metadata": {"doc_id": "A"}},
        {"text": "chunk B1", "metadata": {"doc_id": "B"}},
        {"text": "chunk B2", "metadata": {"doc_id": "B"}},
        {"text": "chunk B3", "metadata": {"doc_id": "B"}},
    ]
    result = Reranker._balanced_select(docs, top_k=4)
    assert len(result) == 4
    doc_ids = [d["metadata"]["doc_id"] for d in result]
    # Each doc should appear at least once
    assert "A" in doc_ids
    assert "B" in doc_ids
