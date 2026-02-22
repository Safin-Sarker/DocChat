"""Tests for app.core.security — JWT creation and verification."""

from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token, verify_token


def test_create_and_verify_token():
    """Round-trip: create token then verify returns same user_id."""
    user_id = "user-abc-123"
    token = create_access_token(user_id)
    assert verify_token(token) == user_id


def test_verify_invalid_token():
    """Garbage string returns None."""
    assert verify_token("not-a-real-token") is None


def test_verify_expired_token():
    """Token with a past expiry returns None."""
    payload = {
        "sub": "user-expired",
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    assert verify_token(token) is None


def test_verify_token_missing_sub():
    """Token without 'sub' claim returns None."""
    payload = {
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    assert verify_token(token) is None


def test_token_uses_correct_algorithm():
    """Token can be decoded with HS256."""
    token = create_access_token("alg-test")
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded["sub"] == "alg-test"
