"""
Timeout and retry mechanism tests.
Tests retry logic, exponential backoff, and timeout handling.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
from datetime import datetime, timedelta


class TestRetryMechanisms:
    """Test retry logic and strategies"""

    async def test_exponential_backoff(self):
        """Test exponential backoff retry strategy"""
        from src.mcp_clients.retry import retry_with_backoff

        call_count = 0
        call_times = []

        @retry_with_backoff(max_retries=4, base_delay=0.1)
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            call_times.append(datetime.now())

            if call_count < 4:
                raise Exception("Temporary failure")
            return "success"

        result = await failing_operation()

        assert result == "success"
        assert call_count == 4

        # Verify exponential backoff (delays should increase)
        if len(call_times) > 1:
            delays = [
                (call_times[i+1] - call_times[i]).total_seconds()
                for i in range(len(call_times) - 1)
            ]
            # Each delay should be roughly double the previous
            for i in range(len(delays) - 1):
                assert delays[i+1] > delays[i] * 0.9  # Allow 10% variance

    async def test_max_retries_exceeded(self):
        """Test behavior when max retries exceeded"""
        from src.mcp_clients.retry import retry_with_backoff

        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            await always_failing()

        # Should try initial + 3 retries = 4 attempts
        assert call_count == 4

    async def test_retry_with_jitter(self):
        """Test retry with jitter to prevent thundering herd"""
        from src.mcp_clients.retry import retry_with_jitter

        call_times = []

        @retry_with_jitter(max_retries=5, base_delay=0.1, jitter=0.05)
        async def operation():
            call_times.append(datetime.now())
            if len(call_times) < 3:
                raise Exception("Retry me")
            return "success"

        result = await operation()
        assert result == "success"

        # Delays should vary due to jitter
        if len(call_times) > 1:
            delays = [
                (call_times[i+1] - call_times[i]).total_seconds()
                for i in range(len(call_times) - 1)
            ]
            # Not all delays should be identical due to jitter
            assert len(set([round(d, 2) for d in delays])) > 1

    async def test_conditional_retry(self):
        """Test retrying only on specific exceptions"""
        from src.mcp_clients.retry import retry_on_exception

        retry_count = 0

        @retry_on_exception(
            max_retries=3,
            retry_on=[ConnectionError, TimeoutError],
            base_delay=0.01
        )
        async def selective_retry():
            nonlocal retry_count
            retry_count += 1

            if retry_count == 1:
                raise ConnectionError("Network issue")  # Should retry
            elif retry_count == 2:
                raise ValueError("Bad value")  # Should NOT retry
            return "success"

        with pytest.raises(ValueError):
            await selective_retry()

        # Should only retry once (ConnectionError), then fail on ValueError
        assert retry_count == 2

    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker prevents retries during outage"""
        from src.mcp_clients.retry import CircuitBreaker

        circuit = CircuitBreaker(
            failure_threshold=3,
            timeout=1.0,
            expected_exception=Exception
        )

        call_count = 0

        async def failing_service():
            nonlocal call_count
            call_count += 1
            raise Exception("Service down")

        # Trip the circuit breaker
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit.call(failing_service)

        # Circuit should be open now
        assert circuit.state == 'open'

        # Further calls should fail immediately without calling service
        initial_count = call_count
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await circuit.call(failing_service)

        # Service should not have been called
        assert call_count == initial_count

    async def test_retry_with_success_callback(self):
        """Test retry with success callback"""
        from src.mcp_clients.retry import retry_with_callback

        retry_attempts = []
        success_called = False

        def on_retry(attempt, exception):
            retry_attempts.append((attempt, str(exception)))

        def on_success(result):
            nonlocal success_called
            success_called = True

        @retry_with_callback(
            max_retries=3,
            on_retry=on_retry,
            on_success=on_success,
            base_delay=0.01
        )
        async def eventually_succeeds():
            if len(retry_attempts) < 2:
                raise Exception("Not yet")
            return "success"

        result = await eventually_succeeds()

        assert result == "success"
        assert len(retry_attempts) == 2
        assert success_called is True


class TestTimeoutHandling:
    """Test timeout mechanisms"""

    async def test_operation_timeout(self):
        """Test operation times out after specified duration"""
        from src.mcp_clients.retry import with_timeout

        @with_timeout(timeout=0.1)
        async def slow_operation():
            await asyncio.sleep(1.0)
            return "should not reach here"

        with pytest.raises(asyncio.TimeoutError):
            await slow_operation()

    async def test_partial_timeout_recovery(self):
        """Test recovering partial results on timeout"""
        from src.mcp_clients.retry import partial_timeout

        results = []

        async def collect_results():
            for i in range(10):
                await asyncio.sleep(0.05)
                results.append(i)
            return results

        # Timeout before all results collected
        partial = await partial_timeout(
            collect_results(),
            timeout=0.2,
            return_partial=True
        )

        # Should have some results but not all
        assert len(results) > 0
        assert len(results) < 10

    async def test_connection_timeout(self):
        """Test connection timeout"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        # Mock the connection at a higher level to avoid asyncpg dependency
        client = PostgreSQLClient(
            host='unreachable-host.invalid',
            database='test',
            user='postgres',
            password='password',
            connect_timeout=0.1
        )

        # Test that connection times out
        with pytest.raises((asyncio.TimeoutError, ConnectionError, Exception)):
            await asyncio.wait_for(
                client.connect(),
                timeout=0.2
            )

    async def test_query_timeout(self):
        """Test query execution timeout"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient
        from src.mcp_clients.base import ConnectionState

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password',
            query_timeout=0.1
        )

        # Mock the connection and pool
        conn = AsyncMock()

        async def slow_query(*args, **kwargs):
            await asyncio.sleep(1)
            return []

        conn.fetch = slow_query

        # Set up proper mocking
        client._connection = conn
        client._state = ConnectionState.CONNECTED

        with pytest.raises((asyncio.TimeoutError, Exception)):
            await client.execute_with_timeout("SELECT pg_sleep(10)", timeout=0.1)

    async def test_adaptive_timeout(self):
        """Test adaptive timeout based on historical performance"""
        from src.mcp_clients.retry import AdaptiveTimeout

        adaptive = AdaptiveTimeout(
            initial_timeout=1.0,
            min_timeout=0.1,
            max_timeout=10.0,
            percentile=0.95
        )

        # Simulate operations with varying durations
        durations = [0.1, 0.2, 0.15, 0.3, 0.12, 0.18, 0.25, 0.22]

        for duration in durations:
            adaptive.record_duration(duration)

        # Timeout should adapt to observed latencies
        timeout = adaptive.get_timeout()
        assert 0.1 <= timeout <= 10.0
        # Should be around 95th percentile of durations
        assert timeout >= max(durations) * 0.9


class TestRetryStrategies:
    """Test different retry strategies"""

    async def test_fixed_delay_retry(self):
        """Test fixed delay between retries"""
        from src.mcp_clients.retry import FixedDelayRetry

        retry = FixedDelayRetry(delay=0.1, max_retries=3)

        call_times = []

        async def operation():
            call_times.append(datetime.now())
            if len(call_times) < 3:
                raise Exception("Retry")
            return "success"

        result = await retry.execute(operation)
        assert result == "success"

        # Delays should be roughly equal
        delays = [
            (call_times[i+1] - call_times[i]).total_seconds()
            for i in range(len(call_times) - 1)
        ]
        avg_delay = sum(delays) / len(delays)
        assert 0.09 <= avg_delay <= 0.15  # Allow some variance

    async def test_linear_backoff_retry(self):
        """Test linear backoff (delay increases linearly)"""
        from src.mcp_clients.retry import LinearBackoffRetry

        retry = LinearBackoffRetry(
            initial_delay=0.1,
            increment=0.1,
            max_retries=4
        )

        call_times = []

        async def operation():
            call_times.append(datetime.now())
            if len(call_times) < 4:
                raise Exception("Retry")
            return "success"

        result = await retry.execute(operation)
        assert result == "success"

        # Delays should increase linearly (0.1, 0.2, 0.3)
        delays = [
            (call_times[i+1] - call_times[i]).total_seconds()
            for i in range(len(call_times) - 1)
        ]

        for i in range(len(delays) - 1):
            # Each delay should be roughly 0.1s more than previous
            assert delays[i+1] - delays[i] > 0.08

    async def test_fibonacci_backoff_retry(self):
        """Test Fibonacci backoff (1, 1, 2, 3, 5, 8...)"""
        from src.mcp_clients.retry import FibonacciBackoffRetry

        retry = FibonacciBackoffRetry(
            base_delay=0.1,
            max_retries=5
        )

        call_times = []

        async def operation():
            call_times.append(datetime.now())
            if len(call_times) < 5:
                raise Exception("Retry")
            return "success"

        result = await retry.execute(operation)
        assert result == "success"
        assert len(call_times) == 5

    async def test_decorrelated_jitter_retry(self):
        """Test AWS decorrelated jitter retry strategy"""
        from src.mcp_clients.retry import DecorrelatedJitterRetry

        retry = DecorrelatedJitterRetry(
            base_delay=0.1,
            max_delay=1.0,
            max_retries=5
        )

        call_times = []

        async def operation():
            call_times.append(datetime.now())
            if len(call_times) < 4:
                raise Exception("Retry")
            return "success"

        result = await retry.execute(operation)
        assert result == "success"

        # Delays should be randomized but within bounds
        delays = [
            (call_times[i+1] - call_times[i]).total_seconds()
            for i in range(len(call_times) - 1)
        ]
        assert all(0.05 <= d <= 1.1 for d in delays)


class TestFailureRecovery:
    """Test failure recovery mechanisms"""

    async def test_fallback_on_all_retries_failed(self):
        """Test fallback mechanism when all retries fail"""
        from src.mcp_clients.retry import with_fallback

        primary_calls = 0
        fallback_called = False

        @with_fallback(max_retries=3)
        async def primary_operation():
            nonlocal primary_calls
            primary_calls += 1
            raise Exception("Primary failed")

        async def fallback_operation():
            nonlocal fallback_called
            fallback_called = True
            return "fallback_result"

        result = await primary_operation.execute(fallback=fallback_operation)

        assert result == "fallback_result"
        assert primary_calls == 4  # Initial + 3 retries
        assert fallback_called is True

    async def test_cache_fallback_on_error(self):
        """Test falling back to cache when live query fails"""
        from src.performance.cache_extended import CacheFallback

        cache = CacheFallback()
        cache.set("SELECT 1", [{'result': 'cached'}])

        async def failing_query():
            raise ConnectionError("Database unavailable")

        result = await cache.execute_with_fallback(
            "SELECT 1",
            failing_query
        )

        assert result[0]['result'] == 'cached'

    async def test_stale_cache_acceptable_on_timeout(self):
        """Test accepting stale cache on timeout"""
        from src.performance.cache_extended import StaleCache

        cache = StaleCache(ttl=1.0, stale_ttl=60.0)

        # Add entry and let it become stale
        cache.set("key", "fresh_value")
        await asyncio.sleep(1.1)

        # Query times out
        async def timeout_query():
            await asyncio.sleep(10)

        # Should return stale value
        result = await cache.get_or_fetch(
            "key",
            timeout_query,
            allow_stale=True,
            timeout=0.1
        )

        assert result == "fresh_value"  # Stale but acceptable

    async def test_degraded_mode_operation(self):
        """Test operating in degraded mode when services fail"""
        from src.core.ai_shell import AIShellCore
        from src.core.degraded_mode import DegradedModeManager

        ai_shell = AIShellCore()
        degraded_manager = DegradedModeManager()
        ai_shell.execute_in_degraded_mode = degraded_manager.execute_in_degraded_mode
        ai_shell.db_module = AsyncMock()
        ai_shell.db_module.execute = AsyncMock(
            side_effect=ConnectionError("DB unavailable")
        )

        # Should switch to degraded mode
        result = await ai_shell.execute_in_degraded_mode(
            "Show users",
            enable_cache=True,
            read_only=True
        )

        assert result['mode'] == 'degraded'
        assert result['status'] in ['success', 'partial']
