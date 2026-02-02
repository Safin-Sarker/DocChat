"""Document model for tracking uploaded documents."""

from typing import List, Optional
from .database import get_db


class Document:
    """Document model for database operations."""

    @staticmethod
    def create(doc_id: str, user_id: str, filename: str, pages: int = 0) -> dict:
        """Create a new document record."""
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO documents (doc_id, user_id, filename, pages) VALUES (?, ?, ?, ?)",
                (doc_id, user_id, filename, pages)
            )
            conn.commit()
            return {
                "doc_id": doc_id,
                "user_id": user_id,
                "filename": filename,
                "pages": pages
            }
        finally:
            conn.close()

    @staticmethod
    def get_by_user(user_id: str) -> List[dict]:
        """Get all documents for a user."""
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT doc_id, filename, pages, uploaded_at FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
                (user_id,)
            ).fetchall()
            return [
                {
                    "doc_id": row["doc_id"],
                    "filename": row["filename"],
                    "pages": row["pages"],
                    "uploadedAt": row["uploaded_at"]
                }
                for row in rows
            ]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(doc_id: str, user_id: str) -> Optional[dict]:
        """Get a document by ID for a specific user."""
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT doc_id, filename, pages, uploaded_at FROM documents WHERE doc_id = ? AND user_id = ?",
                (doc_id, user_id)
            ).fetchone()
            if row:
                return {
                    "doc_id": row["doc_id"],
                    "filename": row["filename"],
                    "pages": row["pages"],
                    "uploadedAt": row["uploaded_at"]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def delete(doc_id: str, user_id: str) -> bool:
        """Delete a document record."""
        conn = get_db()
        try:
            cursor = conn.execute(
                "DELETE FROM documents WHERE doc_id = ? AND user_id = ?",
                (doc_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
