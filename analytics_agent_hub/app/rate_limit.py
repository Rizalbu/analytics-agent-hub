"""Per-IP token-bucket rate limiter (in-process). Mirrors the production
pattern of guarding an LLM-backed endpoint without an external dependency.
"""
from __future__ import annotations

import threading
import time

from .config import settings


class TokenBucket:
    def __init__(self, per_min: int):
        self.capacity = per_min
        self.refill_per_sec = per_min / 60.0
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, dict]:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)
            if tokens >= 1:
                self._buckets[key] = (tokens - 1, now)
                return True, {"remaining": int(tokens - 1), "limit": self.capacity}
            self._buckets[key] = (tokens, now)
            retry = (1 - tokens) / self.refill_per_sec
            return False, {"remaining": 0, "limit": self.capacity,
                           "retry_after": round(retry, 1)}


limiter = TokenBucket(settings.rate_limit_per_min)
