"""Tests for usage limits: document count, page count, daily queries, owner bypass."""

import os
from unittest.mock import patch, MagicMock

import pytest

from app.core.auth import is_owner
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.user import User
from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# is_owner() tests
# ---------------------------------------------------------------------------


def test_is_owner_matches_email():
    """is_owner returns True when email matches OWNER_EMAIL (case-insensitive)."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.OWNER_EMAIL = "Admin@Example.COM"
        assert is_owner({"email": "admin@example.com"}) is True


def test_is_owner_no_match():
    """is_owner returns False when email doesn't match."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.OWNER_EMAIL = "owner@example.com"
        assert is_owner({"email": "other@example.com"}) is False


def test_is_owner_empty_config():
    """is_owner returns False when OWNER_EMAIL is blank."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.OWNER_EMAIL = ""
        assert is_owner({"email": "anyone@example.com"}) is False


def test_is_owner_missing_email_key():
    """is_owner returns False when user dict has no email key."""
    with patch("app.core.auth.settings") as mock_settings:
        mock_settings.OWNER_EMAIL = "owner@example.com"
        assert is_owner({}) is False


# ---------------------------------------------------------------------------
# AuditLog.count_today() tests
# ---------------------------------------------------------------------------


def test_count_today_returns_zero_when_empty(tmp_db):
    """count_today returns 0 when there are no matching entries."""
    count = AuditLog.count_today("nonexistent-user", ["QUERY_EXECUTED"])
    assert count == 0


def test_count_today_counts_matching_actions(tmp_db):
    """count_today counts only the specified actions for the user."""
    user_id = "user-count-test"
    AuditLog.log(action="QUERY_EXECUTED", resource_type="query", user_id=user_id)
    AuditLog.log(action="QUERY_STREAM_EXECUTED", resource_type="query", user_id=user_id)
    AuditLog.log(action="DOCUMENT_UPLOADED", resource_type="document", user_id=user_id)

    count = AuditLog.count_today(user_id, ["QUERY_EXECUTED", "QUERY_STREAM_EXECUTED"])
    assert count == 2


# ---------------------------------------------------------------------------
# Document upload limit tests (via API)
# ---------------------------------------------------------------------------


def test_upload_blocked_at_doc_limit(auth_client, monkeypatch):
    """User with MAX_DOCUMENTS_PER_USER docs gets 403 on next upload."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "MAX_DOCUMENTS_PER_USER", 3)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", "")

    user_id = auth_client._test_user["user_id"]
    # Insert 3 existing documents directly
    for i in range(3):
        Document.create(doc_id=f"doc-{i}", user_id=user_id, filename=f"file{i}.txt", pages=1)

    resp = auth_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 403
    assert "Document limit reached" in resp.json()["detail"]


def test_upload_allowed_under_limit(auth_client, monkeypatch):
    """User under the document limit can proceed (may fail at processing, but not at limit check)."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "MAX_DOCUMENTS_PER_USER", 3)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", "")

    user_id = auth_client._test_user["user_id"]
    # Insert only 2 documents
    for i in range(2):
        Document.create(doc_id=f"doc-{i}", user_id=user_id, filename=f"file{i}.txt", pages=1)

    resp = auth_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    # Should NOT be 403 — might be 500 from processing, but the limit check passed
    assert resp.status_code != 403


def test_owner_bypasses_doc_limit(auth_client, monkeypatch):
    """Owner with MAX docs can still upload (limit is bypassed)."""
    from app.core import config as config_mod

    owner_email = auth_client._test_user["email"]
    monkeypatch.setattr(config_mod.settings, "MAX_DOCUMENTS_PER_USER", 3)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", owner_email)

    user_id = auth_client._test_user["user_id"]
    for i in range(3):
        Document.create(doc_id=f"doc-{i}", user_id=user_id, filename=f"file{i}.txt", pages=1)

    resp = auth_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    # Should NOT be 403 — owner bypasses limit
    assert resp.status_code != 403


def test_upload_blocked_over_page_limit(auth_client, monkeypatch):
    """A file exceeding MAX_PAGES_PER_DOCUMENT gets 403."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "MAX_PAGES_PER_DOCUMENT", 5)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", "")

    # Mock count_pages to return a value over the limit
    with patch("app.api.v1.endpoints.documents.count_pages", return_value=10):
        resp = auth_client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
    assert resp.status_code == 403
    assert "page limit" in resp.json()["detail"].lower()


def test_upload_allowed_under_page_limit(auth_client, monkeypatch):
    """A file within MAX_PAGES_PER_DOCUMENT passes the page check."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "MAX_PAGES_PER_DOCUMENT", 20)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", "")

    with patch("app.api.v1.endpoints.documents.count_pages", return_value=5):
        resp = auth_client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
    # Should NOT be 403 — may be 500 from processing, but limit check passed
    assert resp.status_code != 403


# ---------------------------------------------------------------------------
# Daily query limit tests (via API)
# ---------------------------------------------------------------------------


def test_query_blocked_at_daily_limit(auth_client, monkeypatch):
    """User with MAX_QUERIES_PER_DAY queries today gets 429."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "MAX_QUERIES_PER_DAY", 15)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", "")

    user_id = auth_client._test_user["user_id"]
    # Insert 15 query audit logs for today
    for _ in range(15):
        AuditLog.log(action="QUERY_EXECUTED", resource_type="query", user_id=user_id)

    resp = auth_client.post("/api/v1/query/", json={"query": "test question"})
    assert resp.status_code == 429
    assert "Daily query limit" in resp.json()["detail"]


def test_query_allowed_under_limit(auth_client, monkeypatch):
    """User under the daily limit can query (may fail at processing, but not at limit)."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "MAX_QUERIES_PER_DAY", 15)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", "")

    user_id = auth_client._test_user["user_id"]
    # Insert only 14 queries
    for _ in range(14):
        AuditLog.log(action="QUERY_EXECUTED", resource_type="query", user_id=user_id)

    resp = auth_client.post("/api/v1/query/", json={"query": "test question"})
    # Should NOT be 429
    assert resp.status_code != 429


def test_owner_bypasses_query_limit(auth_client, monkeypatch):
    """Owner with MAX queries can still query (limit bypassed)."""
    from app.core import config as config_mod

    owner_email = auth_client._test_user["email"]
    monkeypatch.setattr(config_mod.settings, "MAX_QUERIES_PER_DAY", 15)
    monkeypatch.setattr(config_mod.settings, "OWNER_EMAIL", owner_email)

    user_id = auth_client._test_user["user_id"]
    for _ in range(15):
        AuditLog.log(action="QUERY_EXECUTED", resource_type="query", user_id=user_id)

    resp = auth_client.post("/api/v1/query/", json={"query": "test question"})
    # Should NOT be 429 — owner bypasses limit
    assert resp.status_code != 429
