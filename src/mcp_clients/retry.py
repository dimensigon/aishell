"""
Retry and error handling mechanisms for MCP clients.

Provides comprehensive retry strategies, circuit breakers, and timeout handling.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, List, Optional, Type, Union
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Retry Decorators
# ============================================================================


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Decorator for exponential backoff retry.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff (typically 2)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Calculate exponential delay
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.debug(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Max retries ({max_retries}) exceeded")

            raise last_exception

        return wrapper
    return decorator


def retry_with_jitter(
    max_retries: int = 3,
    base_delay: float = 1.0,
    jitter: float = 0.5
):
    """
    Decorator for retry with jitter to prevent thundering herd.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        jitter: Maximum random jitter to add (±jitter)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Add random jitter - use exponential backoff with jitter
                        base_with_backoff = base_delay * (2 ** attempt)
                        jitter_amount = random.uniform(-jitter, jitter)
                        delay = base_with_backoff + jitter_amount
                        delay = max(0.01, delay)  # Ensure positive delay

                        logger.debug(f"Retry attempt {attempt + 1}/{max_retries} with jitter: {delay}s")
                        await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


def retry_on_exception(
    max_retries: int = 3,
    retry_on: List[Type[Exception]] = None,
    base_delay: float = 0.1
):
    """
    Decorator for conditional retry on specific exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        retry_on: List of exception types to retry on
        base_delay: Delay between retries in seconds
    """
    retry_exceptions = tuple(retry_on) if retry_on else (Exception,)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.debug(f"Retryable exception {type(e).__name__}, attempt {attempt + 1}")
                        await asyncio.sleep(base_delay)
                    else:
                        raise
                except Exception as e:
                    # Non-retryable exception, raise immediately
                    logger.debug(f"Non-retryable exception: {type(e).__name__}")
                    raise

            raise last_exception

        return wrapper
    return decorator


def retry_with_callback(
    max_retries: int = 3,
    on_retry: Optional[Callable] = None,
    on_success: Optional[Callable] = None,
    base_delay: float = 0.1
):
    """
    Decorator for retry with callbacks.

    Args:
        max_retries: Maximum number of retry attempts
        on_retry: Callback function called on retry (attempt, exception)
        on_success: Callback function called on success (result)
        base_delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)

                    if on_success:
                        on_success(result)

                    return result

                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)
                        await asyncio.sleep(base_delay)

            raise last_exception

        return wrapper
    return decorator


def with_fallback(max_retries: int = 3):
    """
    Decorator that enables fallback mechanism.

    Usage:
        @with_fallback(max_retries=3)
        async def primary_operation():
            ...

        result = await primary_operation.execute(fallback=fallback_func)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        async def execute(fallback: Optional[Callable] = None, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await wrapper(**kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt >= max_retries:
                        if fallback:
                            logger.info(f"All retries failed, using fallback")
                            return await fallback()
                        raise

        wrapper.execute = execute
        return wrapper

    return decorator


# ============================================================================
# Circuit Breaker
# ============================================================================


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures exceeded threshold
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by opening circuit after threshold failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before attempting to close circuit
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        """Get current circuit state"""
        return self._state.value

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or call fails
        """
        async with self._lock:
            # Check if should transition from OPEN to HALF_OPEN
            if self._state == CircuitBreakerState.OPEN:
                if self._last_failure_time:
                    time_since_failure = time.time() - self._last_failure_time
                    if time_since_failure >= self.timeout:
                        logger.info("Circuit breaker transitioning to HALF_OPEN")
                        self._state = CircuitBreakerState.HALF_OPEN
                    else:
                        raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)

            # Success - reset on HALF_OPEN or stay CLOSED
            async with self._lock:
                if self._state == CircuitBreakerState.HALF_OPEN:
                    logger.info("Circuit breaker closing after successful call")
                    self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0

            return result

        except self.expected_exception as e:
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.time()

                if self._failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit breaker opening after {self._failure_count} failures")
                    self._state = CircuitBreakerState.OPEN

            raise


# ============================================================================
# Timeout Handlers
# ============================================================================


def with_timeout(timeout: float):
    """
    Decorator to add timeout to async function.

    Args:
        timeout: Timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Operation timed out after {timeout}s")
                raise

        return wrapper
    return decorator


async def partial_timeout(
    coro,
    timeout: float,
    return_partial: bool = True
):
    """
    Execute coroutine with timeout, optionally returning partial results.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        return_partial: If True, return partial results on timeout

    Returns:
        Result or partial result
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        if return_partial:
            logger.warning(f"Timeout after {timeout}s, returning partial results")
            return None  # Caller should handle partial results
        raise


class AdaptiveTimeout:
    """
    Adaptive timeout based on historical performance.

    Adjusts timeout dynamically based on observed latencies.
    """

    def __init__(
        self,
        initial_timeout: float = 5.0,
        min_timeout: float = 0.1,
        max_timeout: float = 60.0,
        percentile: float = 0.95
    ):
        """
        Initialize adaptive timeout.

        Args:
            initial_timeout: Initial timeout value
            min_timeout: Minimum allowed timeout
            max_timeout: Maximum allowed timeout
            percentile: Percentile to use for timeout calculation
        """
        self.initial_timeout = initial_timeout
        self.min_timeout = min_timeout
        self.max_timeout = max_timeout
        self.percentile = percentile

        self._durations: List[float] = []
        self._current_timeout = initial_timeout

    def record_duration(self, duration: float):
        """Record operation duration"""
        self._durations.append(duration)

        # Keep last 100 measurements
        if len(self._durations) > 100:
            self._durations = self._durations[-100:]

        # Update timeout
        self._update_timeout()

    def _update_timeout(self):
        """Update timeout based on recorded durations"""
        if not self._durations:
            return

        sorted_durations = sorted(self._durations)
        index = int(len(sorted_durations) * self.percentile)
        percentile_value = sorted_durations[min(index, len(sorted_durations) - 1)]

        # Add 20% buffer
        self._current_timeout = percentile_value * 1.2

        # Clamp to min/max
        self._current_timeout = max(self.min_timeout, min(self._current_timeout, self.max_timeout))

    def get_timeout(self) -> float:
        """Get current timeout value"""
        return self._current_timeout


# ============================================================================
# Retry Strategies
# ============================================================================


class RetryStrategy(ABC):
    """Abstract base class for retry strategies"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay for given attempt number"""
        pass

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry strategy"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    logger.debug(f"Retry attempt {attempt + 1}/{self.max_retries}, delay: {delay}s")
                    await asyncio.sleep(delay)

        raise last_exception


class FixedDelayRetry(RetryStrategy):
    """Fixed delay between retries"""

    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        super().__init__(max_retries)
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        return self.delay


class LinearBackoffRetry(RetryStrategy):
    """Linear backoff (delay increases linearly)"""

    def __init__(self, initial_delay: float = 1.0, increment: float = 1.0, max_retries: int = 3):
        super().__init__(max_retries)
        self.initial_delay = initial_delay
        self.increment = increment

    def get_delay(self, attempt: int) -> float:
        return self.initial_delay + (attempt * self.increment)


class FibonacciBackoffRetry(RetryStrategy):
    """Fibonacci backoff (1, 1, 2, 3, 5, 8, ...)"""

    def __init__(self, base_delay: float = 1.0, max_retries: int = 5):
        super().__init__(max_retries)
        self.base_delay = base_delay
        self._fib_cache = [1, 1]

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number"""
        while len(self._fib_cache) <= n:
            self._fib_cache.append(
                self._fib_cache[-1] + self._fib_cache[-2]
            )
        return self._fib_cache[n]

    def get_delay(self, attempt: int) -> float:
        return self.base_delay * self._fibonacci(attempt)


class DecorrelatedJitterRetry(RetryStrategy):
    """AWS decorrelated jitter retry strategy"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5
    ):
        super().__init__(max_retries)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._last_delay = base_delay

    def get_delay(self, attempt: int) -> float:
        # sleep = min(max_delay, random_between(base, last_delay * 3))
        delay = random.uniform(self.base_delay, self._last_delay * 3)
        delay = min(delay, self.max_delay)
        self._last_delay = delay
        return delay
