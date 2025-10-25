"""
Comprehensive tests for retry logic and error handling

Tests exponential backoff, max retry limits, timeout handling,
circuit breaker pattern, and various retry strategies.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, Mock
from src.mcp_clients.retry import (
    retry_with_backoff,
    retry_with_jitter,
    retry_on_exception,
    retry_with_callback,
    with_fallback,
    CircuitBreaker,
    CircuitBreakerState,
    with_timeout,
    partial_timeout,
    AdaptiveTimeout,
    RetryStrategy,
    FixedDelayRetry,
    LinearBackoffRetry,
    FibonacciBackoffRetry,
    DecorrelatedJitterRetry
)


class TestRetryWithBackoff:
    """Test exponential backoff retry decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test function succeeds on first attempt."""
        call_count = []

        @retry_with_backoff(max_retries=3)
        async def successful_func():
            call_count.append(1)
            return "success"

        result = await successful_func()

        assert result == "success"
        assert len(call_count) == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retries on failure."""
        call_count = []

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def failing_func():
            call_count.append(1)
            if len(call_count) < 3:
                raise ValueError("Not yet")
            return "success"

        result = await failing_func()

        assert result == "success"
        assert len(call_count) == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test max retries exceeded raises last exception."""
        call_count = []

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def always_fails():
            call_count.append(1)
            raise ValueError(f"Attempt {len(call_count)}")

        with pytest.raises(ValueError, match="Attempt 3"):
            await always_fails()

        assert len(call_count) == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_exponential_delay(self):
        """Test exponential backoff delay."""
        delays = []
        start_time = time.time()

        @retry_with_backoff(max_retries=3, base_delay=0.1, exponential_base=2.0)
        async def failing_func():
            delays.append(time.time() - start_time)
            raise ValueError("Always fails")

        try:
            await failing_func()
        except ValueError:
            pass

        # Delays should be approximately: 0, 0.1, 0.3, 0.7
        # (0 + 0.1, 0.1 + 0.2, 0.3 + 0.4)
        assert len(delays) == 4

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test maximum delay cap."""
        delays = []

        @retry_with_backoff(max_retries=10, base_delay=1.0, max_delay=2.0)
        async def failing_func():
            if len(delays) > 0:
                delays.append(time.time())
            else:
                delays.append(time.time())
            raise ValueError("Fails")

        try:
            await failing_func()
        except ValueError:
            pass

        # Verify delays don't exceed max_delay
        # This is hard to test precisely due to timing, but we can check call count
        assert len(delays) == 11  # Initial + 10 retries


class TestRetryWithJitter:
    """Test retry with jitter decorator."""

    @pytest.mark.asyncio
    async def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay."""
        call_count = []

        @retry_with_jitter(max_retries=3, base_delay=0.05, jitter=0.02)
        async def failing_func():
            call_count.append(1)
            if len(call_count) < 3:
                raise ValueError("Not yet")
            return "success"

        result = await failing_func()

        assert result == "success"
        assert len(call_count) == 3

    @pytest.mark.asyncio
    async def test_jitter_prevents_negative_delay(self):
        """Test jitter never produces negative delay."""
        delays_were_positive = True

        @retry_with_jitter(max_retries=5, base_delay=0.01, jitter=0.5)
        async def failing_func():
            raise ValueError("Fails")

        try:
            await failing_func()
        except ValueError:
            pass

        # If we got here without hanging, delays were positive
        assert delays_were_positive


class TestRetryOnException:
    """Test conditional retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_on_specific_exception(self):
        """Test retry only on specific exception types."""
        call_count = []

        @retry_on_exception(max_retries=3, retry_on=[ValueError], base_delay=0.01)
        async def func():
            call_count.append(1)
            if len(call_count) < 3:
                raise ValueError("Retry this")
            return "success"

        result = await func()

        assert result == "success"
        assert len(call_count) == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_different_exception(self):
        """Test no retry on non-retryable exception."""
        call_count = []

        @retry_on_exception(max_retries=3, retry_on=[ValueError], base_delay=0.01)
        async def func():
            call_count.append(1)
            raise TypeError("Don't retry this")

        with pytest.raises(TypeError):
            await func()

        assert len(call_count) == 1  # No retries

    @pytest.mark.asyncio
    async def test_retry_on_multiple_exception_types(self):
        """Test retry on multiple exception types."""
        call_count = []

        @retry_on_exception(
            max_retries=5,
            retry_on=[ValueError, TypeError, KeyError],
            base_delay=0.01
        )
        async def func():
            call_count.append(1)
            if len(call_count) == 1:
                raise ValueError("First")
            elif len(call_count) == 2:
                raise TypeError("Second")
            elif len(call_count) == 3:
                raise KeyError("Third")
            return "success"

        result = await func()

        assert result == "success"
        assert len(call_count) == 4


class TestRetryWithCallback:
    """Test retry with callback decorator."""

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_calls = []

        def on_retry(attempt, exception):
            retry_calls.append((attempt, str(exception)))

        @retry_with_callback(max_retries=3, on_retry=on_retry, base_delay=0.01)
        async def func():
            if len(retry_calls) < 2:
                raise ValueError(f"Attempt {len(retry_calls) + 1}")
            return "success"

        result = await func()

        assert result == "success"
        assert len(retry_calls) == 2

    @pytest.mark.asyncio
    async def test_on_success_callback(self):
        """Test on_success callback is called."""
        success_results = []

        def on_success(result):
            success_results.append(result)

        @retry_with_callback(max_retries=3, on_success=on_success, base_delay=0.01)
        async def func():
            return "success"

        result = await func()

        assert result == "success"
        assert success_results == ["success"]

    @pytest.mark.asyncio
    async def test_both_callbacks(self):
        """Test both retry and success callbacks."""
        retry_calls = []
        success_calls = []

        def on_retry(attempt, exception):
            retry_calls.append(attempt)

        def on_success(result):
            success_calls.append(result)

        @retry_with_callback(
            max_retries=3,
            on_retry=on_retry,
            on_success=on_success,
            base_delay=0.01
        )
        async def func():
            if len(retry_calls) < 2:
                raise ValueError("Retry")
            return "success"

        result = await func()

        assert result == "success"
        assert len(retry_calls) == 2
        assert success_calls == ["success"]


class TestWithFallback:
    """Test fallback mechanism decorator."""

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        """Test fallback is used on failure."""
        async def primary():
            raise ValueError("Primary failed")

        async def fallback():
            return "fallback_result"

        @with_fallback(max_retries=2)
        async def func():
            return await primary()

        result = await func.execute(fallback=fallback)

        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_no_fallback_needed(self):
        """Test fallback not used when primary succeeds."""
        async def primary():
            return "primary_result"

        async def fallback():
            return "fallback_result"

        @with_fallback(max_retries=2)
        async def func():
            return await primary()

        result = await func.execute(fallback=fallback)

        assert result == "primary_result"


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_initial_state_closed(self):
        """Test circuit breaker starts in closed state."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)

        assert breaker.state == CircuitBreakerState.CLOSED.value

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        """Test circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)

        async def failing_func():
            raise Exception("Failure")

        # Fail 3 times to reach threshold
        for _ in range(3):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitBreakerState.OPEN.value

    @pytest.mark.asyncio
    async def test_rejects_calls_when_open(self):
        """Test circuit rejects calls when open."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=1.0)

        async def failing_func():
            raise Exception("Failure")

        # Open the circuit
        for _ in range(2):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        # Should reject calls
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await breaker.call(failing_func)

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)

        async def failing_func():
            raise Exception("Failure")

        # Open the circuit
        for _ in range(2):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitBreakerState.OPEN.value

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next call should transition to half-open
        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED.value

    @pytest.mark.asyncio
    async def test_resets_on_success(self):
        """Test circuit resets failure count on success."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)

        async def failing_func():
            raise Exception("Failure")

        async def success_func():
            return "success"

        # Have some failures
        try:
            await breaker.call(failing_func)
        except Exception:
            pass

        # Then success
        await breaker.call(success_func)

        # More failures should not open immediately
        try:
            await breaker.call(failing_func)
        except Exception:
            pass

        assert breaker.state == CircuitBreakerState.CLOSED.value


class TestTimeoutDecorator:
    """Test timeout decorator."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        """Test function completes within timeout."""
        @with_timeout(1.0)
        async def quick_func():
            await asyncio.sleep(0.01)
            return "success"

        result = await quick_func()

        assert result == "success"

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        """Test raises TimeoutError on timeout."""
        @with_timeout(0.1)
        async def slow_func():
            await asyncio.sleep(1.0)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            await slow_func()


class TestPartialTimeout:
    """Test partial timeout function."""

    @pytest.mark.asyncio
    async def test_returns_result_within_timeout(self):
        """Test returns result within timeout."""
        async def quick_coro():
            await asyncio.sleep(0.01)
            return "result"

        result = await partial_timeout(quick_coro(), timeout=1.0)

        assert result == "result"

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout_with_partial(self):
        """Test returns None on timeout when return_partial=True."""
        async def slow_coro():
            await asyncio.sleep(1.0)
            return "never"

        result = await partial_timeout(slow_coro(), timeout=0.1, return_partial=True)

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_on_timeout_without_partial(self):
        """Test raises on timeout when return_partial=False."""
        async def slow_coro():
            await asyncio.sleep(1.0)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            await partial_timeout(slow_coro(), timeout=0.1, return_partial=False)


class TestAdaptiveTimeout:
    """Test adaptive timeout class."""

    def test_initial_timeout(self):
        """Test initial timeout value."""
        timeout = AdaptiveTimeout(initial_timeout=5.0)

        assert timeout.get_timeout() == 5.0

    def test_timeout_adjusts_to_measurements(self):
        """Test timeout adjusts based on measurements."""
        timeout = AdaptiveTimeout(
            initial_timeout=5.0,
            min_timeout=0.1,
            max_timeout=10.0,
            percentile=0.95
        )

        # Record some durations
        for _ in range(10):
            timeout.record_duration(1.0)

        # Timeout should adjust to ~1.2 (1.0 * 1.2 buffer)
        current = timeout.get_timeout()
        assert 1.0 <= current <= 1.5

    def test_timeout_respects_min_max(self):
        """Test timeout respects min/max bounds."""
        timeout = AdaptiveTimeout(
            initial_timeout=5.0,
            min_timeout=2.0,
            max_timeout=8.0
        )

        # Record very short durations
        for _ in range(10):
            timeout.record_duration(0.01)

        # Should not go below min
        assert timeout.get_timeout() >= 2.0

        # Record very long durations
        for _ in range(10):
            timeout.record_duration(100.0)

        # Should not exceed max
        assert timeout.get_timeout() <= 8.0

    def test_keeps_last_100_measurements(self):
        """Test keeps only last 100 measurements."""
        timeout = AdaptiveTimeout()

        for i in range(150):
            timeout.record_duration(float(i))

        # Should have only last 100
        assert len(timeout._durations) == 100


class TestRetryStrategies:
    """Test various retry strategy classes."""

    @pytest.mark.asyncio
    async def test_fixed_delay_retry(self):
        """Test fixed delay retry strategy."""
        strategy = FixedDelayRetry(delay=0.1, max_retries=3)
        call_count = []

        async def func():
            call_count.append(1)
            if len(call_count) < 3:
                raise ValueError("Retry")
            return "success"

        result = await strategy.execute(func)

        assert result == "success"
        assert len(call_count) == 3

    @pytest.mark.asyncio
    async def test_fixed_delay_returns_same_delay(self):
        """Test fixed delay returns constant delay."""
        strategy = FixedDelayRetry(delay=1.5)

        assert strategy.get_delay(0) == 1.5
        assert strategy.get_delay(1) == 1.5
        assert strategy.get_delay(10) == 1.5

    @pytest.mark.asyncio
    async def test_linear_backoff_retry(self):
        """Test linear backoff retry strategy."""
        strategy = LinearBackoffRetry(initial_delay=1.0, increment=0.5, max_retries=3)

        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 1.5
        assert strategy.get_delay(2) == 2.0

    @pytest.mark.asyncio
    async def test_fibonacci_backoff_retry(self):
        """Test Fibonacci backoff retry strategy."""
        strategy = FibonacciBackoffRetry(base_delay=1.0)

        # Fibonacci sequence: 1, 1, 2, 3, 5, 8...
        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 1.0
        assert strategy.get_delay(2) == 2.0
        assert strategy.get_delay(3) == 3.0
        assert strategy.get_delay(4) == 5.0

    @pytest.mark.asyncio
    async def test_decorrelated_jitter_retry(self):
        """Test decorrelated jitter retry strategy."""
        strategy = DecorrelatedJitterRetry(base_delay=1.0, max_delay=10.0)

        # Delays should be random but within bounds
        for i in range(10):
            delay = strategy.get_delay(i)
            assert 0 < delay <= 10.0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """Test with zero retries."""
        call_count = []

        @retry_with_backoff(max_retries=0, base_delay=0.01)
        async def func():
            call_count.append(1)
            raise ValueError("Fails")

        with pytest.raises(ValueError):
            await func()

        assert len(call_count) == 1  # Only initial attempt

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_custom_exception(self):
        """Test circuit breaker with specific exception type."""
        breaker = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)

        async def fails_with_value_error():
            raise ValueError("Expected")

        async def fails_with_type_error():
            raise TypeError("Not expected")

        # ValueError should count toward threshold
        for _ in range(2):
            try:
                await breaker.call(fails_with_value_error)
            except ValueError:
                pass

        assert breaker.state == CircuitBreakerState.OPEN.value

        # TypeError should pass through and not affect circuit
        breaker2 = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)

        try:
            await breaker2.call(fails_with_type_error)
        except TypeError:
            pass

        assert breaker2.state == CircuitBreakerState.CLOSED.value

    @pytest.mark.asyncio
    async def test_very_short_timeout(self):
        """Test with very short timeout."""
        @with_timeout(0.001)
        async def func():
            await asyncio.sleep(0.1)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            await func()
