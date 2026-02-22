"""Tests for app.models.user — User model (uses in-memory SQLite)."""

import pytest

from app.models.user import User


def test_create_user(tmp_db):
    """Creates user and returns dict with user_id, email, username."""
    user = User.create(email="alice@example.com", username="alice", password="secret123")
    assert "user_id" in user
    assert user["email"] == "alice@example.com"
    assert user["username"] == "alice"


def test_authenticate_valid(tmp_db):
    """Correct password returns user dict."""
    User.create(email="bob@example.com", username="bob", password="mypassword")
    result = User.authenticate("bob@example.com", "mypassword")
    assert result is not None
    assert result["email"] == "bob@example.com"
    assert result["username"] == "bob"


def test_authenticate_invalid_password(tmp_db):
    """Wrong password returns None."""
    User.create(email="carol@example.com", username="carol", password="correct")
    assert User.authenticate("carol@example.com", "wrong") is None


def test_get_by_id(tmp_db):
    """Retrieves created user by ID."""
    user = User.create(email="dave@example.com", username="dave", password="pass")
    fetched = User.get_by_id(user["user_id"])
    assert fetched is not None
    assert fetched["email"] == "dave@example.com"


def test_get_by_email_case_insensitive(tmp_db):
    """Email lookup is case-insensitive."""
    User.create(email="Eve@Example.COM", username="eve", password="pass")
    result = User.get_by_email("eve@example.com")
    assert result is not None
    assert result["username"] == "eve"


def test_exists_by_email_and_username(tmp_db):
    """Checks existence correctly."""
    User.create(email="frank@example.com", username="frank", password="pass")
    assert User.exists(email="frank@example.com") is True
    assert User.exists(username="frank") is True
    assert User.exists(email="nobody@example.com") is False
    assert User.exists(username="nobody") is False
