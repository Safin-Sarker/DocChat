"""Tests for app.services.context_assembler — ContextAssembler."""

from app.services.context_assembler import ContextAssembler
from app.core.config import settings


def _make_doc(text, doc_id="doc1", page=1, parent_text=None):
    """Helper to create a document chunk dict."""
    d = {
        "text": text,
        "metadata": {"doc_id": doc_id, "page": page},
    }
    if parent_text:
        d["parent_text"] = parent_text
    return d


def test_assemble_basic():
    """Produces labeled context strings."""
    asm = ContextAssembler()
    docs = [_make_doc("Hello world", doc_id="d1", page=1)]
    doc_names = {"d1": "report.pdf"}
    contexts = asm.assemble(docs, doc_names)
    assert len(contexts) == 1
    assert "[Document: report.pdf, Page 1]" in contexts[0]
    assert "Hello world" in contexts[0]


def test_assemble_deduplicates():
    """Duplicate text appears only once."""
    asm = ContextAssembler()
    docs = [
        _make_doc("Same text here", doc_id="d1", page=1),
        _make_doc("Same text here", doc_id="d1", page=2),
    ]
    contexts = asm.assemble(docs)
    assert len(contexts) == 1


def test_assemble_with_citations():
    """Returns numbered contexts and a source_map."""
    asm = ContextAssembler()
    docs = [
        _make_doc("First chunk", doc_id="d1", page=1),
        _make_doc("Second chunk", doc_id="d2", page=3),
    ]
    doc_names = {"d1": "a.pdf", "d2": "b.pdf"}
    contexts, source_map = asm.assemble_with_citations(docs, doc_names)
    assert len(contexts) == 2
    assert contexts[0].startswith("[1]")
    assert contexts[1].startswith("[2]")
    assert len(source_map) == 2
    assert source_map[0]["index"] == 1
    assert source_map[0]["doc_name"] == "a.pdf"
    assert source_map[1]["index"] == 2
    assert source_map[1]["doc_name"] == "b.pdf"


def test_snippet_length():
    """Snippets in source_map respect CONTEXT_SNIPPET_LENGTH."""
    asm = ContextAssembler()
    long_text = "x" * (settings.CONTEXT_SNIPPET_LENGTH + 100)
    docs = [_make_doc(long_text, doc_id="d1", page=1)]
    _, source_map = asm.assemble_with_citations(docs)
    snippet = source_map[0]["text"]
    assert snippet.endswith("...")
    # Snippet length = CONTEXT_SNIPPET_LENGTH + len("...")
    assert len(snippet) == settings.CONTEXT_SNIPPET_LENGTH + 3
