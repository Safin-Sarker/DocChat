"""Tests for app.services.txt_extractor — TxtExtractor."""

import os

from app.services.txt_extractor import TxtExtractor


def test_extract_pages_basic(tmp_path):
    """Returns page dicts with text."""
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Section one content.\n\nSection two content.", encoding="utf-8")

    extractor = TxtExtractor()
    pages = extractor.extract_pages(str(txt_file))
    assert len(pages) >= 1
    assert all("page_num" in p and "text" in p for p in pages)
    full_text = " ".join(p["text"] for p in pages)
    assert "Section one" in full_text


def test_extract_pages_empty_file(tmp_path):
    """Empty file returns empty list."""
    txt_file = tmp_path / "empty.txt"
    txt_file.write_text("", encoding="utf-8")

    extractor = TxtExtractor()
    pages = extractor.extract_pages(str(txt_file))
    assert pages == []


def test_split_respects_max_section_chars(tmp_path):
    """Sections don't exceed the configured max character limit."""
    from app.services.txt_extractor import MAX_SECTION_CHARS

    # Create text with many paragraphs that exceed MAX_SECTION_CHARS
    paragraph = "A" * 500 + "\n\n"
    text = paragraph * 20  # 10000+ chars total
    txt_file = tmp_path / "long.txt"
    txt_file.write_text(text, encoding="utf-8")

    extractor = TxtExtractor()
    pages = extractor.extract_pages(str(txt_file))
    assert len(pages) >= 2
    for page in pages:
        # Each section should not greatly exceed the max (allowing for paragraph boundaries)
        assert len(page["text"]) <= MAX_SECTION_CHARS + 600
