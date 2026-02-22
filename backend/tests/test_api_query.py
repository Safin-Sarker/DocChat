"""Integration tests for query API endpoints."""

import pytest


def test_query_unauthorized(client, tmp_db):
    """Returns 403 without auth token."""
    resp = client.post("/api/v1/query/", json={"query": "What is this?"})
    assert resp.status_code == 403


def test_query_empty_body(auth_client):
    """Returns 400 for empty query string."""
    resp = auth_client.post("/api/v1/query/", json={"query": "   "})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()
