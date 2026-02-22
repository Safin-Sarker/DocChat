"""Tests for app.core.retry — is_retryable, retry_sync."""

import pytest

from app.core.retry import is_retryable, retry_sync


def test_is_retryable_connection_error():
    """ConnectionError is retryable."""
    assert is_retryable(ConnectionError("refused")) is True


def test_is_retryable_timeout_error():
    """TimeoutError is retryable."""
    assert is_retryable(TimeoutError("timed out")) is True


def test_is_retryable_value_error():
    """ValueError is NOT retryable."""
    assert is_retryable(ValueError("bad value")) is False


def test_retry_sync_succeeds_after_failure():
    """Retries and eventually succeeds."""
    call_count = 0

    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("transient")
        return "ok"

    result = retry_sync(flaky, max_attempts=3, base_delay=0.01, operation_name="test")
    assert result == "ok"
    assert call_count == 3


def test_retry_sync_non_retryable_raises_immediately():
    """Non-retryable error raises on first attempt without retry."""
    call_count = 0

    def bad():
        nonlocal call_count
        call_count += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError, match="not retryable"):
        retry_sync(bad, max_attempts=3, base_delay=0.01, operation_name="test")

    assert call_count == 1
