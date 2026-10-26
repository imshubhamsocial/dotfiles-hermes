"""High-throughput token bucket rate limiter with sliding refill."""

from typing import Optional


class TokenBucketRateLimiter:
    """Token bucket rate limiter.
    
    capacity: Maximum bucket depth (tokens).
    refill_rate: Tokens added per second.
    """
    def __init__(self, capacity: float, refill_rate: float, initial_time: float = 0.0):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill = float(initial_time)

    def allow_request(self, cost: float = 1.0, current_time: Optional[float] = None) -> bool:
        now = float(current_time if current_time is not None else 0.0)
        elapsed = max(0.0, now - self.last_refill)
        
        # Calculate refill
        refill = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + refill)
        self.last_refill = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def get_available_tokens(self) -> float:
        return self.tokens
