"""Tests for app.services.cache_utils — TTLCache."""

import time

from app.services.cache_utils import TTLCache


def test_set_and_get():
    """Basic store and retrieve."""
    cache: TTLCache[str, int] = TTLCache(max_size=10, ttl_seconds=60)
    cache.set("a", 1)
    assert cache.get("a") == 1


def test_get_missing_key():
    """Missing key returns None."""
    cache: TTLCache[str, int] = TTLCache(max_size=10, ttl_seconds=60)
    assert cache.get("nope") is None


def test_ttl_expiry(monkeypatch):
    """Item expires after TTL elapses."""
    cache: TTLCache[str, str] = TTLCache(max_size=10, ttl_seconds=5)
    cache.set("k", "v")
    assert cache.get("k") == "v"

    # Fast-forward time past TTL
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 10)
    assert cache.get("k") is None


def test_lru_eviction():
    """Oldest entry evicted when max_size exceeded."""
    cache: TTLCache[str, int] = TTLCache(max_size=2, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # should evict "a"
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_update_existing_key():
    """Overwriting a key updates its value and position."""
    cache: TTLCache[str, int] = TTLCache(max_size=2, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 10)  # update "a", moves to end
    cache.set("c", 3)   # should evict "b" (now oldest)
    assert cache.get("a") == 10
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_clear():
    """Clear empties the cache."""
    cache: TTLCache[str, int] = TTLCache(max_size=10, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_access_refreshes_position():
    """Accessing an item moves it to the end so it survives eviction."""
    cache: TTLCache[str, int] = TTLCache(max_size=2, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    # Access "a" to refresh its position
    cache.get("a")
    cache.set("c", 3)  # should evict "b" (now oldest)
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3
