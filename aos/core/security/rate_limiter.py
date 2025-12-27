from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RateLimitStatus:
    allowed: bool
    remaining: int
    reset_at: float


class TokenBucketLimiter:
    """
    Simple Token Bucket rate limiter.
    Efficient for edge nodes with low memory.
    """

    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate  # tokens per second
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_update)

    def check(self, key: str) -> RateLimitStatus:
        now = time.time()
        tokens, last_update = self._buckets.get(key, (float(self.capacity), now))

        # Fill bucket
        elapsed = now - last_update
        tokens = min(self.capacity, tokens + (elapsed * self.fill_rate))
        
        if tokens >= 1:
            tokens -= 1
            allowed = True
        else:
            allowed = False

        self._buckets[key] = (tokens, now)
        
        return RateLimitStatus(
            allowed=allowed,
            remaining=int(tokens),
            reset_at=now + ((1.0 - tokens) / self.fill_rate) if tokens < 1 else now
        )

    def cleanup(self, max_idle: int = 3600):
        """Remove buckets that haven't been touched in a while."""
        now = time.time()
        expired = [k for k, v in self._buckets.items() if now - v[1] > max_idle]
        for k in expired:
            del self._buckets[k]
