"""Plain text file extraction utilities."""

from typing import Any, Dict, List
from app.core.config import settings

MAX_SECTION_CHARS = settings.TEXT_MAX_SECTION_CHARS


class TxtExtractor:
    """Extract text from plain text files."""

    def extract_pages(self, txt_path: str) -> List[Dict[str, Any]]:
        """Read text file and split into page-like sections."""
        text = self._read_file(txt_path)
        if not text.strip():
            return []

        sections = self._split_into_sections(text)
        return [
            {"page_num": i + 1, "text": section}
            for i, section in enumerate(sections)
            if section.strip()
        ]

    def _read_file(self, txt_path: str) -> str:
        """Read file contents with UTF-8 and fallback encoding."""
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(txt_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, ValueError):
                continue
        return ""

    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into sections by double newlines or fixed character count."""
        # First try splitting by double newlines (paragraph boundaries)
        parts = text.split("\n\n")
        sections: List[str] = []
        current: List[str] = []
        current_len = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue
            if current_len + len(part) > MAX_SECTION_CHARS and current:
                sections.append("\n\n".join(current))
                current = [part]
                current_len = len(part)
            else:
                current.append(part)
                current_len += len(part)

        if current:
            sections.append("\n\n".join(current))

        return sections
