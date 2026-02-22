"""Tests for app.services.chunking_service — ChunkingService."""

from app.services.chunking_service import ChunkingService


def _make_service(**kwargs):
    """Create a ChunkingService with small, predictable sizes."""
    defaults = dict(parent_size=100, parent_overlap=20, child_size=30, child_overlap=5)
    defaults.update(kwargs)
    return ChunkingService(**defaults)


def test_create_chunks_basic():
    """Text splits into expected number of chunks."""
    svc = _make_service()
    text = "a" * 120
    chunks = svc.create_chunks(text, chunk_size=50, overlap=0)
    assert len(chunks) == 3
    assert all(c.text for c in chunks)


def test_create_chunks_overlap():
    """Chunks overlap by the expected characters."""
    svc = _make_service()
    text = "abcdefghijklmnopqrstuvwxyz" * 5  # 130 chars
    chunks = svc.create_chunks(text, chunk_size=50, overlap=10)
    # Verify overlapping characters
    if len(chunks) >= 2:
        end_of_first = chunks[0].text[-10:]
        start_of_second = chunks[1].text[:10]
        assert end_of_first == start_of_second


def test_create_chunks_empty_text():
    """Empty text returns empty list."""
    svc = _make_service()
    assert svc.create_chunks("", chunk_size=50, overlap=10) == []
    assert svc.create_chunks("   ", chunk_size=50, overlap=10) == []


def test_create_chunks_short_text():
    """Text shorter than chunk_size produces exactly 1 chunk."""
    svc = _make_service()
    chunks = svc.create_chunks("short text", chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "short text"


def test_parent_child_structure():
    """Each parent has children; children text is a subset of parent text."""
    svc = _make_service(parent_size=100, parent_overlap=20, child_size=30, child_overlap=5)
    text = "word " * 50  # 250 chars
    pc_chunks = svc.create_parent_child_chunks(text)
    assert len(pc_chunks) > 0
    for pc in pc_chunks:
        assert len(pc.children) > 0
        for child in pc.children:
            assert child.text in pc.parent.text


def test_detect_structured_document():
    """Recognizes docs with 3+ section headers."""
    svc = _make_service()
    structured = (
        "EDUCATION\nSome details here\n"
        "EXPERIENCE\nMore details\n"
        "SKILLS\nPython, JS\n"
        "LANGUAGES\nEnglish, French\n"
    )
    assert svc.detect_structured_document(structured) is True
    assert svc.detect_structured_document("Just a paragraph of text.") is False


def test_section_aware_chunking():
    """Splits on section boundaries when document is structured."""
    svc = _make_service(parent_size=500, parent_overlap=50, child_size=100, child_overlap=10)
    text = (
        "EDUCATION\nBSc Computer Science, 2020\nGPA 3.8\n\n"
        "EXPERIENCE\nSoftware Engineer at Acme Corp\nBuilt APIs\n\n"
        "SKILLS\nPython, JavaScript, Docker\n\n"
        "LANGUAGES\nEnglish, Norwegian\n"
    )
    pc_chunks = svc.create_section_aware_chunks(text)
    # Should have roughly one parent per section
    assert len(pc_chunks) >= 3
    # Each parent text should start with a section header or content
    parent_texts = [pc.parent.text for pc in pc_chunks]
    assert any("EDUCATION" in t for t in parent_texts)
    assert any("EXPERIENCE" in t for t in parent_texts)
