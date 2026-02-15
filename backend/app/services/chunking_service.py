"""Parent-child chunking service for advanced RAG."""

import re
from typing import List, Dict, Tuple, Optional
import uuid
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class Chunk:
    """Represents a text chunk."""
    id: str
    text: str
    page: int
    start_char: int
    end_char: int


@dataclass
class ParentChildChunk:
    """Represents a parent chunk with its children."""
    parent: Chunk
    children: List[Chunk]


class ChunkingService:
    """Service for creating parent-child text chunks."""

    def __init__(
        self,
        parent_size: int = None,
        parent_overlap: int = None,
        child_size: int = None,
        child_overlap: int = None
    ):
        """Initialize chunking service with configurable parameters.

        Args:
            parent_size: Size of parent chunks in characters
            parent_overlap: Overlap between parent chunks
            child_size: Size of child chunks in characters
            child_overlap: Overlap between child chunks
        """
        self.parent_size = parent_size or settings.PARENT_CHUNK_SIZE
        self.parent_overlap = parent_overlap or settings.PARENT_CHUNK_OVERLAP
        self.child_size = child_size or settings.CHILD_CHUNK_SIZE
        self.child_overlap = child_overlap or settings.CHILD_CHUNK_OVERLAP

    def create_chunks(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        page: int = 0
    ) -> List[Chunk]:
        """Create chunks from text with specified size and overlap.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            page: Page number

        Returns:
            List of Chunk objects
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # Extract chunk text
            chunk_text = text[start:end].strip()

            if chunk_text:  # Only create non-empty chunks
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    text=chunk_text,
                    page=page,
                    start_char=start,
                    end_char=end
                )
                chunks.append(chunk)

            # Move to next chunk
            start += chunk_size - overlap

            # Break if we've reached the end
            if end >= text_length:
                break

        return chunks

    def create_parent_child_chunks(
        self,
        text: str,
        page: int = 0
    ) -> List[ParentChildChunk]:
        """Create parent-child chunk structure from text.

        Args:
            text: Text to chunk
            page: Page number

        Returns:
            List of ParentChildChunk objects
        """
        # Create parent chunks
        parent_chunks = self.create_chunks(
            text=text,
            chunk_size=self.parent_size,
            overlap=self.parent_overlap,
            page=page
        )

        parent_child_chunks = []

        for parent in parent_chunks:
            # Create child chunks from parent text
            children = self.create_chunks(
                text=parent.text,
                chunk_size=self.child_size,
                overlap=self.child_overlap,
                page=page
            )

            parent_child_chunks.append(
                ParentChildChunk(parent=parent, children=children)
            )

        return parent_child_chunks

    # Section header pattern: lines that are short, title-cased/ALL CAPS,
    # optionally ending with a colon — typical of CVs and structured docs.
    _HEADER_RE = re.compile(
        r"^(?:"
        r"[A-Z][A-Z /&\-]{2,40}$"        # ALL CAPS header (e.g. "LANGUAGES")
        r"|[A-Z][a-zA-Z /&\-]{2,40}:$"   # Title case ending with colon
        r"|[A-Z][a-zA-Z /&\-]{2,40}$"    # Title case standalone line
        r")",
        re.MULTILINE,
    )

    def detect_structured_document(self, text: str) -> bool:
        """Return True if the text has enough section-like headers (>=3)."""
        headers = self._HEADER_RE.findall(text)
        return len(headers) >= 3

    def create_section_aware_chunks(self, text: str, page: int = 0) -> List[ParentChildChunk]:
        """Split text on section boundaries instead of fixed character counts.

        Each detected section (header + body) becomes its own parent chunk.
        Sections exceeding parent_size fall back to character-based chunking.
        """
        lines = text.split("\n")
        sections: List[Tuple[str, int]] = []  # (section_text, start_char)
        current_section_lines: List[str] = []
        current_start = 0
        char_pos = 0

        for line in lines:
            is_header = bool(self._HEADER_RE.match(line.strip()))
            if is_header and current_section_lines:
                # Flush the previous section
                section_text = "\n".join(current_section_lines).strip()
                if section_text:
                    sections.append((section_text, current_start))
                current_section_lines = [line]
                current_start = char_pos
            else:
                current_section_lines.append(line)
            char_pos += len(line) + 1  # +1 for newline

        # Flush last section
        if current_section_lines:
            section_text = "\n".join(current_section_lines).strip()
            if section_text:
                sections.append((section_text, current_start))

        parent_child_chunks = []
        for section_text, start in sections:
            if len(section_text) > self.parent_size:
                # Section too large — fall back to character-based chunking
                pc_chunks = self.create_parent_child_chunks(section_text, page=page)
                parent_child_chunks.extend(pc_chunks)
            else:
                # Section fits in one parent chunk
                parent = Chunk(
                    id=str(uuid.uuid4()),
                    text=section_text,
                    page=page,
                    start_char=start,
                    end_char=start + len(section_text),
                )
                children = self.create_chunks(
                    text=section_text,
                    chunk_size=self.child_size,
                    overlap=self.child_overlap,
                    page=page,
                )
                parent_child_chunks.append(ParentChildChunk(parent=parent, children=children))

        return parent_child_chunks

    def process_document_pages(
        self,
        pages: List[Dict[str, any]]
    ) -> Tuple[List[Chunk], List[Chunk]]:
        """Process multiple pages and return parent and child chunks.

        Concatenates all pages first and uses section-aware chunking for
        structured documents (CVs, resumes, specs with clear headers).

        Args:
            pages: List of page dictionaries with 'text' and 'page_num' keys

        Returns:
            Tuple of (parent_chunks, child_chunks)
        """
        all_parents = []
        all_children = []

        # Concatenate all page texts to detect structure across the full document
        full_text = "\n\n".join(
            page_data.get("text", "")
            for page_data in pages
            if page_data.get("text", "").strip()
        )

        if not full_text.strip():
            return all_parents, all_children

        if self.detect_structured_document(full_text):
            # Section-aware chunking for structured docs
            pc_chunks = self.create_section_aware_chunks(full_text, page=0)
            for pc_chunk in pc_chunks:
                all_parents.append(pc_chunk.parent)
                all_children.extend(pc_chunk.children)
        else:
            # Standard per-page character-based chunking
            for page_data in pages:
                text = page_data.get("text", "")
                page_num = page_data.get("page_num", 0)

                if not text.strip():
                    continue

                pc_chunks = self.create_parent_child_chunks(text, page=page_num)

                for pc_chunk in pc_chunks:
                    all_parents.append(pc_chunk.parent)
                    all_children.extend(pc_chunk.children)

        return all_parents, all_children

    def prepare_for_pinecone(
        self,
        parent_chunks: List[Chunk],
        child_chunks: List[Chunk],
        doc_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """Prepare chunk data for Pinecone storage.

        Args:
            parent_chunks: List of parent chunks
            child_chunks: List of child chunks
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation

        Returns:
            Dictionary with parent_map and child_data for Pinecone
        """
        # Create parent lookup map
        parent_map = {p.id: p for p in parent_chunks}

        # Find parent for each child
        child_data = []
        for child in child_chunks:
            # Find parent containing this child
            parent = None
            for p in parent_chunks:
                if (child.page == p.page and
                    child.start_char >= p.start_char and
                    child.end_char <= p.end_char):
                    parent = p
                    break

            if parent:
                child_data.append({
                    "child": child,
                    "parent_id": parent.id,
                    "parent_text": parent.text,
                    "doc_id": doc_id
                })

        return {
            "parent_map": parent_map,
            "child_data": child_data
        }
