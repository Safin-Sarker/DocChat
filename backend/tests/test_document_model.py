"""Tests for app.models.document — Document model (uses in-memory SQLite)."""

import uuid

from app.models.document import Document
from app.models.user import User


def _make_user(tmp_db):
    """Create a test user and return the dict."""
    return User.create(email=f"{uuid.uuid4().hex[:8]}@test.com", username=f"u{uuid.uuid4().hex[:6]}", password="pass")


def test_create_document(tmp_db):
    """Inserts and returns dict."""
    user = _make_user(tmp_db)
    doc_id = str(uuid.uuid4())
    doc = Document.create(doc_id=doc_id, user_id=user["user_id"], filename="test.pdf", pages=5)
    assert doc["doc_id"] == doc_id
    assert doc["filename"] == "test.pdf"
    assert doc["pages"] == 5


def test_get_by_user(tmp_db):
    """Lists user's documents."""
    user = _make_user(tmp_db)
    Document.create(doc_id=str(uuid.uuid4()), user_id=user["user_id"], filename="a.pdf", pages=1)
    Document.create(doc_id=str(uuid.uuid4()), user_id=user["user_id"], filename="b.pdf", pages=2)

    docs = Document.get_by_user(user["user_id"])
    assert len(docs) == 2
    filenames = {d["filename"] for d in docs}
    assert filenames == {"a.pdf", "b.pdf"}


def test_get_by_id(tmp_db):
    """Retrieves specific document."""
    user = _make_user(tmp_db)
    doc_id = str(uuid.uuid4())
    Document.create(doc_id=doc_id, user_id=user["user_id"], filename="c.pdf", pages=3)

    doc = Document.get_by_id(doc_id, user["user_id"])
    assert doc is not None
    assert doc["filename"] == "c.pdf"

    # Wrong user returns None
    assert Document.get_by_id(doc_id, "other-user") is None


def test_delete_document(tmp_db):
    """Removes document and returns True."""
    user = _make_user(tmp_db)
    doc_id = str(uuid.uuid4())
    Document.create(doc_id=doc_id, user_id=user["user_id"], filename="d.pdf", pages=1)

    assert Document.delete(doc_id, user["user_id"]) is True
    assert Document.get_by_id(doc_id, user["user_id"]) is None
    # Deleting again returns False
    assert Document.delete(doc_id, user["user_id"]) is False
