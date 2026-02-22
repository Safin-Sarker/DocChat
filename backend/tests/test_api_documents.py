"""Integration tests for documents API endpoints."""

import pytest


def test_list_documents_empty(auth_client):
    """Returns empty list for new user."""
    resp = auth_client.get("/api/v1/documents/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_documents_unauthorized(client, tmp_db):
    """Returns 403 without auth token."""
    resp = client.get("/api/v1/documents/")
    assert resp.status_code == 403


def test_delete_nonexistent(auth_client):
    """Returns 404 for non-existent document."""
    resp = auth_client.delete("/api/v1/documents/nonexistent-doc-id")
    assert resp.status_code == 404


def test_upload_no_file(auth_client):
    """Returns 422 when no file is provided."""
    resp = auth_client.post("/api/v1/documents/upload")
    assert resp.status_code == 422
