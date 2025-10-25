"""
Rate Limiting for Command Execution

Provides rate limiting and throttling to prevent abuse and DOS attacks.
"""

import time
from typing import Dict, Optional, Tuple, Any, Callable
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_calls: int = 100  # Maximum calls
    period_seconds: int = 60  # Time period in seconds
    burst_limit: int = 10  # Maximum burst (consecutive calls)
    burst_period_seconds: int = 5  # Burst time window


@dataclass
class RateLimitState:
    """Rate limit state tracking"""
    call_times: "deque[float]" = field(default_factory=deque)
    burst_times: "deque[float]" = field(default_factory=deque)
    total_calls: int = 0
    blocked_calls: int = 0
    last_call_time: Optional[float] = None


class RateLimiter:
    """
    Rate limiter with both time-window and burst protection.

    Features:
    - Time-window rate limiting (e.g., 100 calls per minute)
    - Burst protection (e.g., max 10 calls per 5 seconds)
    - Per-user/per-command tracking
    - Exponential backoff support
    """

    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if None)
        """
        self.config = config or RateLimitConfig()
        self.states: Dict[str, RateLimitState] = {}

    def check_rate_limit(
        self,
        key: str,
        raise_on_limit: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if rate limit is exceeded.

        Args:
            key: Unique key for rate limiting (e.g., user_id, command_type)
            raise_on_limit: Raise exception if limit exceeded

        Returns:
            Tuple of (is_allowed, error_message)

        Raises:
            RateLimitExceeded: If rate limit exceeded and raise_on_limit=True
        """
        # Get or create state
        if key not in self.states:
            self.states[key] = RateLimitState()

        state = self.states[key]
        current_time = time.time()

        # Clean up old call times (outside time window)
        cutoff_time = current_time - self.config.period_seconds
        while state.call_times and state.call_times[0] < cutoff_time:
            state.call_times.popleft()

        # Clean up old burst times
        burst_cutoff = current_time - self.config.burst_period_seconds
        while state.burst_times and state.burst_times[0] < burst_cutoff:
            state.burst_times.popleft()

        # Check time-window limit
        if len(state.call_times) >= self.config.max_calls:
            state.blocked_calls += 1
            oldest_call = state.call_times[0]
            wait_time = oldest_call + self.config.period_seconds - current_time

            error_msg = (
                f"Rate limit exceeded: {self.config.max_calls} calls per "
                f"{self.config.period_seconds} seconds. "
                f"Please wait {wait_time:.1f} seconds."
            )

            if raise_on_limit:
                raise RateLimitExceeded(error_msg)
            return False, error_msg

        # Check burst limit
        if len(state.burst_times) >= self.config.burst_limit:
            state.blocked_calls += 1
            oldest_burst = state.burst_times[0]
            wait_time = oldest_burst + self.config.burst_period_seconds - current_time

            error_msg = (
                f"Burst limit exceeded: {self.config.burst_limit} calls per "
                f"{self.config.burst_period_seconds} seconds. "
                f"Please wait {wait_time:.1f} seconds."
            )

            if raise_on_limit:
                raise RateLimitExceeded(error_msg)
            return False, error_msg

        # Record this call
        state.call_times.append(current_time)
        state.burst_times.append(current_time)
        state.total_calls += 1
        state.last_call_time = current_time

        return True, None

    def record_call(self, key: str) -> None:
        """
        Record a call without checking limits.

        Args:
            key: Unique key for rate limiting
        """
        if key not in self.states:
            self.states[key] = RateLimitState()

        state = self.states[key]
        current_time = time.time()

        state.call_times.append(current_time)
        state.burst_times.append(current_time)
        state.total_calls += 1
        state.last_call_time = current_time

    def get_stats(self, key: str) -> Dict[str, Any]:
        """
        Get rate limit statistics for a key.

        Args:
            key: Unique key

        Returns:
            Dictionary with statistics
        """
        if key not in self.states:
            return {
                'total_calls': 0,
                'blocked_calls': 0,
                'current_window_calls': 0,
                'current_burst_calls': 0,
                'last_call_time': None,
            }

        state = self.states[key]
        current_time = time.time()

        # Count calls in current windows
        window_calls = sum(
            1 for t in state.call_times
            if t > current_time - self.config.period_seconds
        )

        burst_calls = sum(
            1 for t in state.burst_times
            if t > current_time - self.config.burst_period_seconds
        )

        return {
            'total_calls': state.total_calls,
            'blocked_calls': state.blocked_calls,
            'current_window_calls': window_calls,
            'current_burst_calls': burst_calls,
            'last_call_time': datetime.fromtimestamp(state.last_call_time).isoformat()
            if state.last_call_time else None,
            'window_limit': self.config.max_calls,
            'burst_limit': self.config.burst_limit,
        }

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset rate limit state.

        Args:
            key: Specific key to reset, or None to reset all
        """
        if key:
            self.states.pop(key, None)
        else:
            self.states.clear()

    def get_backoff_time(self, key: str, attempt: int) -> float:
        """
        Calculate exponential backoff time.

        Args:
            key: Unique key
            attempt: Attempt number (starts at 1)

        Returns:
            Backoff time in seconds
        """
        # Exponential backoff: 2^attempt seconds, max 60 seconds
        backoff = min(2 ** attempt, 60)
        return float(backoff)


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """
    Get global rate limiter instance.

    Args:
        config: Configuration (only used on first call)

    Returns:
        RateLimiter instance
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(config)
    return _global_rate_limiter


def rate_limited(
    key_func: Optional[Callable[..., str]] = None,
    config: Optional[RateLimitConfig] = None
) -> Callable[..., Any]:
    """
    Decorator for rate limiting functions.

    Args:
        key_func: Function to generate rate limit key from args
        config: Rate limit configuration

    Example:
        @rate_limited(key_func=lambda self, cmd: f"user_{self.user_id}")
        async def execute_command(self, cmd: str):
            pass
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = func.__name__

            # Check rate limit
            limiter = get_rate_limiter(config)
            limiter.check_rate_limit(key, raise_on_limit=True)

            # Execute function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
