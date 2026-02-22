"""Shared test fixtures for backend tests."""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Provide test-safe environment variables BEFORE any app imports so that
# ``Settings()`` (which reads env vars at import time) never fails due to
# missing required secrets.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone-key")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_PASSWORD", "test-neo4j-password")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

# Light imports only — avoid importing app.main at module level because it
# transitively imports heavy ML libraries (torch, transformers, etc.) which
# makes test collection extremely slow.
from app.models.database import init_db  # noqa: E402
from app.models.user import User  # noqa: E402
from app.core.security import create_access_token  # noqa: E402


@pytest.fixture()
def tmp_db(monkeypatch, tmp_path):
    """Redirect the database to a temporary SQLite file and initialise it."""
    db_file = tmp_path / "test.db"
    import app.models.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)
    init_db()
    yield db_file


@pytest.fixture()
def test_user(tmp_db):
    """Create and return a test user dict."""
    return User.create(
        email="test@example.com",
        username="testuser",
        password="password123",
    )


@pytest.fixture()
def auth_token(test_user):
    """Return a valid JWT token for the test user."""
    return create_access_token(test_user["user_id"])


@pytest.fixture()
def auth_headers(auth_token):
    """Return Authorization headers dict."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
def client(tmp_db):
    """Provide a Starlette TestClient for the FastAPI app.

    Imported lazily to avoid loading heavy ML dependencies during collection.
    """
    from starlette.testclient import TestClient
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture()
def auth_client(client, tmp_db):
    """Provide an authenticated TestClient.

    Creates a user, generates a token, and attaches the Authorization header.
    """
    user = User.create(
        email="authclient@example.com",
        username="authclientuser",
        password="password123",
    )
    token = create_access_token(user["user_id"])
    client.headers.update({"Authorization": f"Bearer {token}"})
    # Attach user info for tests that need it
    client._test_user = user  # type: ignore[attr-defined]
    return client


# ---------------------------------------------------------------------------
# Mock factories for integration tests
# ---------------------------------------------------------------------------


def mock_llm_response(content: str) -> MagicMock:
    """Return a mock LangChain chat response with ``.content``."""
    resp = MagicMock()
    resp.content = content
    return resp


def mock_pinecone_matches(items: list[dict]) -> list[dict]:
    """Build Pinecone-style query results.

    Each *item* should have at minimum ``id``, ``score``, and ``text``.
    """
    results = []
    for item in items:
        results.append({
            "id": item.get("id", "chunk-0"),
            "score": item.get("score", 0.9),
            "metadata": {
                "text": item.get("text", ""),
                "parent_text": item.get("parent_text", ""),
                "doc_id": item.get("doc_id", "doc-1"),
                "page": item.get("page", 1),
                **item.get("extra_metadata", {}),
            },
        })
    return results


def mock_retrieval_results(n: int = 3) -> list[dict]:
    """Return a list of chunk dicts as produced by ``HybridRetrieval.retrieve``."""
    return [
        {
            "id": f"chunk-{i}",
            "score": round(0.95 - i * 0.05, 2),
            "text": f"Chunk {i} text content that is long enough to pass filter.",
            "parent_text": f"Parent text for chunk {i}",
            "metadata": {
                "text": f"Chunk {i} text content that is long enough to pass filter.",
                "parent_text": f"Parent text for chunk {i}",
                "doc_id": f"doc-{i % 2 + 1}",
                "page": i + 1,
            },
        }
        for i in range(n)
    ]
