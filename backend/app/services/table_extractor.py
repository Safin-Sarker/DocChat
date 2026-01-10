"""Table extraction utilities for PDFs."""

from typing import List, Dict, Any
import pdfplumber


def _table_to_markdown(table: List[List[str]]) -> str:
    """Convert a table (list of rows) to markdown."""
    if not table or not any(table):
        return ""

    header = table[0]
    rows = table[1:] if len(table) > 1 else []
    header_line = "| " + " | ".join(cell or "" for cell in header) + " |"
    sep_line = "| " + " | ".join("---" for _ in header) + " |"
    body_lines = [
        "| " + " | ".join(cell or "" for cell in row) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep_line] + body_lines)


class TableExtractor:
    """Extract tables from PDF pages and return markdown."""

    def extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of table dictionaries
        """
        tables_out: List[Dict[str, Any]] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_index, page in enumerate(pdf.pages):
                    tables = page.extract_tables() or []
                    for table_index, table in enumerate(tables):
                        markdown = _table_to_markdown(table)
                        if not markdown:
                            continue
                        tables_out.append({
                            "page": page_index + 1,
                            "table_index": table_index,
                            "markdown": markdown,
                            "raw": table
                        })
        except Exception as exc:
            print(f"Table extraction failed: {exc}")

        return tables_out
