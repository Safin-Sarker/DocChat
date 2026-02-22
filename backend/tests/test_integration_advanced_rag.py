"""Integration tests for AdvancedRAGService — inject all dependencies."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import mock_retrieval_results
from app.services.advanced_rag import AdvancedRAGService


@pytest.fixture(autouse=True)
def disable_caches(monkeypatch):
    """Disable all caching so tests are deterministic."""
    monkeypatch.setattr("app.services.advanced_rag.settings.ENABLE_QUERY_RESPONSE_CACHE", False)
    monkeypatch.setattr("app.services.advanced_rag.settings.ENABLE_SEMANTIC_QUERY_CACHE", False)
    monkeypatch.setattr("app.services.advanced_rag.settings.JUDGE_ENABLED", False)


@pytest.fixture()
def mock_deps():
    retrieval = AsyncMock()
    reranker = AsyncMock()
    assembler = MagicMock()
    generator = MagicMock()
    entity_extractor = MagicMock()
    query_router = MagicMock()

    # Sensible defaults
    retrieval.retrieve.return_value = mock_retrieval_results(3)
    reranker.rerank.return_value = mock_retrieval_results(2)
    assembler.assemble_with_citations.return_value = (
        ["[1] Context chunk text", "[2] Another context chunk"],
        [{"index": 1, "doc_name": "doc.pdf", "page": 1, "text": "chunk"}],
    )
    generator.generate.return_value = "Generated answer from RAG pipeline."
    entity_extractor.extract_entities.return_value = ["Entity1"]
    query_router.classify.return_value = "document_query"

    return retrieval, reranker, assembler, generator, entity_extractor, query_router


@pytest.fixture()
def service(mock_deps):
    ret, rer, asm, gen, ee, qr = mock_deps
    return AdvancedRAGService(
        retrieval=ret,
        reranker=rer,
        assembler=asm,
        generator=gen,
        entity_extractor=ee,
        query_router=qr,
    )


@pytest.mark.asyncio
async def test_answer_document_query(service, mock_deps):
    result = await service.answer("What is X?", user_id="u1")
    assert "answer" in result
    assert "contexts" in result
    assert "sources" in result
    assert "entities" in result
    assert result["answer"] == "Generated answer from RAG pipeline."


@pytest.mark.asyncio
async def test_answer_greeting_skips_retrieval(service, mock_deps):
    ret, rer, asm, gen, ee, qr = mock_deps
    qr.classify.return_value = "greeting"
    qr.generate_casual_response.return_value = "Hello!"

    result = await service.answer("Hi", user_id="u1")
    assert result["answer"] == "Hello!"
    assert result["contexts"] == []
    ret.retrieve.assert_not_called()


@pytest.mark.asyncio
async def test_answer_with_judge_pass(service, mock_deps, monkeypatch):
    monkeypatch.setattr("app.services.advanced_rag.settings.JUDGE_ENABLED", True)
    mock_judge = MagicMock()
    verdict = MagicMock()
    verdict.verdict = "pass"
    verdict.overall = 0.9
    verdict.to_dict.return_value = {
        "faithfulness": 0.9, "relevance": 0.9, "completeness": 0.9,
        "coherence": 0.9, "conciseness": 0.9, "overall": 0.9,
        "verdict": "pass", "feedback": "", "was_regenerated": False,
    }
    mock_judge.evaluate.return_value = verdict
    service.answer_judge = mock_judge

    result = await service.answer("What is X?", user_id="u1")
    assert result["reflection"]["verdict"] == "pass"


@pytest.mark.asyncio
async def test_answer_with_judge_fail_regenerates(service, mock_deps, monkeypatch):
    monkeypatch.setattr("app.services.advanced_rag.settings.JUDGE_ENABLED", True)
    monkeypatch.setattr("app.services.advanced_rag.settings.JUDGE_MAX_RETRIES", 1)
    ret, rer, asm, gen, ee, qr = mock_deps

    mock_judge = MagicMock()
    fail_verdict = MagicMock()
    fail_verdict.verdict = "fail"
    fail_verdict.overall = 0.3
    fail_verdict.feedback = "Not detailed enough"

    pass_verdict = MagicMock()
    pass_verdict.verdict = "pass"
    pass_verdict.overall = 0.9
    pass_verdict.was_regenerated = False
    pass_verdict.to_dict.return_value = {
        "faithfulness": 0.9, "relevance": 0.9, "completeness": 0.9,
        "coherence": 0.9, "conciseness": 0.9, "overall": 0.9,
        "verdict": "pass", "feedback": "", "was_regenerated": True,
    }

    mock_judge.evaluate.side_effect = [fail_verdict, pass_verdict]
    service.answer_judge = mock_judge

    gen.generate_with_feedback.return_value = "Improved answer."
    result = await service.answer("What is X?", user_id="u1")
    gen.generate_with_feedback.assert_called_once()
    assert result["reflection"]["was_regenerated"] is True


def test_normalize_doc_ids():
    assert AdvancedRAGService._normalize_doc_ids(None) is None
    assert AdvancedRAGService._normalize_doc_ids([]) is None
    assert AdvancedRAGService._normalize_doc_ids(["b", "a", "b"]) == ["a", "b"]
    assert AdvancedRAGService._normalize_doc_ids(["", ""]) is None


def test_normalize_chat_history():
    # Dict-style input
    history = [{"role": "user", "content": "hello"}]
    result = AdvancedRAGService._normalize_chat_history(history)
    assert result == [{"role": "user", "content": "hello"}]

    # Object-style input
    history = [SimpleNamespace(role="assistant", content="hi")]
    result = AdvancedRAGService._normalize_chat_history(history)
    assert result == [{"role": "assistant", "content": "hi"}]

    # None input
    assert AdvancedRAGService._normalize_chat_history(None) == []

    # Missing fields
    history = [{"role": "user"}]
    result = AdvancedRAGService._normalize_chat_history(history)
    assert result == []


def test_diversify_by_doc():
    ranked = [
        {"id": "1", "metadata": {"doc_id": "A"}},
        {"id": "2", "metadata": {"doc_id": "A"}},
        {"id": "3", "metadata": {"doc_id": "B"}},
        {"id": "4", "metadata": {"doc_id": "B"}},
    ]
    result = AdvancedRAGService._diversify_by_doc(ranked, top_k=3, doc_ids=["A", "B"])
    doc_ids = [r["metadata"]["doc_id"] for r in result]
    assert "A" in doc_ids and "B" in doc_ids

    # Single doc: passthrough
    single = AdvancedRAGService._diversify_by_doc(ranked, top_k=2, doc_ids=["A"])
    assert len(single) == 2

    # Empty input
    assert AdvancedRAGService._diversify_by_doc([], top_k=5) == []


def test_build_doc_names():
    with patch("app.services.advanced_rag.Document") as MockDoc:
        MockDoc.get_by_user.return_value = [
            {"doc_id": "d1", "filename": "file1.pdf"},
            {"doc_id": "d2", "filename": "file2.pdf"},
        ]
        result = AdvancedRAGService._build_doc_names("user-1")
        assert result == {"d1": "file1.pdf", "d2": "file2.pdf"}

    # No user_id
    assert AdvancedRAGService._build_doc_names(None) == {}
