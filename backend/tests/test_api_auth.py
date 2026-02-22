"""Integration tests for auth API endpoints (FastAPI TestClient)."""

import pytest
from app.models.user import User


def test_register_success(client, tmp_db):
    """POST /api/v1/auth/register returns 200 with token."""
    resp = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["username"] == "newuser"


def test_register_duplicate_email(client, tmp_db):
    """Registering with existing email returns 400."""
    # Create the user directly to avoid consuming rate-limit quota
    User.create(email="dup@example.com", username="dupuser", password="password123")
    resp = client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "username": "dupuser2",
        "password": "password123",
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_login_success(client, tmp_db):
    """POST /api/v1/auth/login returns 200 with token."""
    # Create user directly via model to avoid rate-limited register endpoint
    User.create(email="login@example.com", username="loginuser", password="password123")
    resp = client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_wrong_password(client, tmp_db):
    """Wrong password returns 401."""
    User.create(email="wrongpw@example.com", username="wrongpwuser", password="password123")
    resp = client.post("/api/v1/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_me_authenticated(auth_client):
    """GET /api/v1/auth/me with valid token returns user info."""
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == auth_client._test_user["email"]


def test_me_no_token(client, tmp_db):
    """GET /api/v1/auth/me without token returns 403."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 403
