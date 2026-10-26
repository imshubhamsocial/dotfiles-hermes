"""Unit test suite for TokenBucketRateLimiter (Phase 27)."""

import pytest
from scenario.rate_limiter import TokenBucketRateLimiter


def test_initial_capacity():
    limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=2.0, initial_time=0.0)
    # Drain full capacity
    assert limiter.allow_request(cost=10.0, current_time=0.0) is True
    # Next request immediately rejected
    assert limiter.allow_request(cost=1.0, current_time=0.0) is False


def test_monotonic_refill():
    limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=2.0, initial_time=0.0)
    assert limiter.allow_request(cost=10.0, current_time=0.0) is True

    # 1.0 second later, 2.0 tokens added
    assert limiter.allow_request(cost=2.0, current_time=1.0) is True
    assert limiter.allow_request(cost=1.0, current_time=1.0) is False


def test_refill_staleness_under_rejected_polling():
    """Stresses the bug: Repeated rejected polls must update last_refill or advance time cleanly."""
    limiter = TokenBucketRateLimiter(capacity=10.0, refill_rate=2.0, initial_time=0.0)
    assert limiter.allow_request(cost=10.0, current_time=0.0) is True

    # At 0.5s: 1.0 token refilled, but request needs 5.0 tokens (rejected)
    assert limiter.allow_request(cost=5.0, current_time=0.5) is False
    
    # At 0.6s: another rejected poll
    assert limiter.allow_request(cost=5.0, current_time=0.6) is False

    # At 1.0s: Total elapsed since 0.0 is 1.0s -> exactly 2.0 tokens should exist.
    # A request for 3.0 tokens MUST be rejected (only 2.0 tokens generated in total 1s)
    assert limiter.allow_request(cost=3.0, current_time=1.0) is False

    # A request for 2.0 tokens MUST succeed
    assert limiter.allow_request(cost=2.0, current_time=1.0) is True
    
    # Check that tokens do not jump above remaining
    assert limiter.allow_request(cost=1.0, current_time=1.0) is False
