"""Integration tests for auth API endpoints (FastAPI TestClient)."""

import pytest
from app.models.user import User


def test_register_success(client, tmp_db):
    """POST /api/v1/auth/register returns 200 with access and refresh tokens."""
    resp = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
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
    """POST /api/v1/auth/login returns 200 with access and refresh tokens."""
    # Create user directly via model to avoid rate-limited register endpoint
    User.create(email="login@example.com", username="loginuser", password="password123")
    resp = client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
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


# --- Refresh token tests ---


def test_refresh_token_success(client, tmp_db):
    """POST /api/v1/auth/refresh with valid refresh token returns new tokens."""
    User.create(email="refresh@example.com", username="refreshuser", password="password123")
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "refresh@example.com",
        "password": "password123",
    })
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Rotated: new token is different from the old one
    assert data["refresh_token"] != refresh_token


def test_refresh_token_reuse_revokes_family(client, tmp_db):
    """Reusing an already-rotated refresh token revokes the entire family."""
    User.create(email="reuse@example.com", username="reuseuser", password="password123")
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "reuse@example.com",
        "password": "password123",
    })
    old_refresh = login_resp.json()["refresh_token"]

    # First refresh -- succeeds
    resp1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp1.status_code == 200
    new_refresh = resp1.json()["refresh_token"]

    # Reuse old token -- should fail (theft detection) and revoke family
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 401

    # Even the new token should be revoked now (entire family revoked)
    resp3 = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert resp3.status_code == 401


def test_refresh_token_invalid(client, tmp_db):
    """Invalid refresh token returns 401."""
    resp = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "totally-fake-token",
    })
    assert resp.status_code == 401


def test_logout_revokes_refresh_tokens(client, tmp_db):
    """Logout revokes all refresh tokens for the user."""
    User.create(email="logouttest@example.com", username="logoutuser", password="password123")
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "logouttest@example.com",
        "password": "password123",
    })
    data = login_resp.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Logout with valid access token
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # Refresh should now fail because tokens were revoked
    client.headers.pop("Authorization", None)
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401
