"""Simple in-memory TTL + LRU cache utility."""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """Thread-safe in-memory cache with TTL and LRU eviction."""

    def __init__(self, max_size: int, ttl_seconds: int):
        self.max_size = max(1, max_size)
        self.ttl_seconds = max(1, ttl_seconds)
        self._store: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = Lock()

    def _is_expired(self, expires_at: float) -> bool:
        return time.time() >= expires_at

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            expires_at, value = item
            if self._is_expired(expires_at):
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            expires_at = time.time() + self.ttl_seconds
            if key in self._store:
                self._store.pop(key, None)
            self._store[key] = (expires_at, value)
            self._store.move_to_end(key)

            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
