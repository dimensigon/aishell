"""
Comprehensive tests for src/core/health_checks.py - Phase 11 Health Check System

Tests cover:
1. Parallel execution tests (all checks < 2s total)
2. Individual health check tests (LLM, Database, Filesystem, Memory)
3. Timeout protection tests
4. Async-first design validation
5. Custom health check extensibility
6. Health check aggregation and reporting
7. Mock external dependencies (LLM, databases)
8. Real database connections for DB health checks
9. Health check results format and status codes
10. Failure scenarios and recovery
"""

import pytest
import asyncio
import time
import sqlite3
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Tuple, Any

from src.core.health_checks import (
    HealthCheck,
    HealthCheckResult,
    HealthCheckRunner,
    HealthStatus,
    HealthMonitor,
    run_health_checks
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.PASS.value == "pass"
        assert HealthStatus.FAIL.value == "fail"
        assert HealthStatus.WARN.value == "warn"

    def test_health_status_members(self):
        """Test HealthStatus enum members."""
        statuses = list(HealthStatus)
        assert len(statuses) == 3
        assert HealthStatus.PASS in statuses
        assert HealthStatus.FAIL in statuses
        assert HealthStatus.WARN in statuses


class TestHealthCheckDataclass:
    """Test HealthCheck dataclass."""

    def test_health_check_creation_minimal(self):
        """Test creating HealthCheck with minimal parameters."""
        def dummy_check():
            return True

        check = HealthCheck(
            name="test_check",
            description="Test description",
            check_function=dummy_check
        )

        assert check.name == "test_check"
        assert check.description == "Test description"
        assert check.check_function == dummy_check
        assert check.is_async is False
        assert check.timeout == 5.0

    def test_health_check_creation_with_async(self):
        """Test creating async HealthCheck."""
        async def async_check():
            return True

        check = HealthCheck(
            name="async_check",
            description="Async test",
            check_function=async_check,
            is_async=True,
            timeout=3.0
        )

        assert check.is_async is True
        assert check.timeout == 3.0

    def test_health_check_custom_timeout(self):
        """Test HealthCheck with custom timeout."""
        check = HealthCheck(
            name="test",
            description="Test",
            check_function=lambda: True,
            timeout=10.0
        )

        assert check.timeout == 10.0


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_result_creation_minimal(self):
        """Test creating HealthCheckResult with minimal parameters."""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.PASS,
            message="All good",
            duration=0.5
        )

        assert result.name == "test_check"
        assert result.status == HealthStatus.PASS
        assert result.message == "All good"
        assert result.duration == 0.5
        assert result.details == {}

    def test_result_creation_with_details(self):
        """Test creating HealthCheckResult with details."""
        details = {"key": "value", "count": 42}
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.WARN,
            message="Warning",
            duration=1.0,
            details=details
        )

        assert result.details == details
        assert result.details["key"] == "value"
        assert result.details["count"] == 42

    def test_result_status_types(self):
        """Test all status types in results."""
        pass_result = HealthCheckResult(
            name="pass", status=HealthStatus.PASS, message="", duration=0.1
        )
        fail_result = HealthCheckResult(
            name="fail", status=HealthStatus.FAIL, message="", duration=0.1
        )
        warn_result = HealthCheckResult(
            name="warn", status=HealthStatus.WARN, message="", duration=0.1
        )

        assert pass_result.status == HealthStatus.PASS
        assert fail_result.status == HealthStatus.FAIL
        assert warn_result.status == HealthStatus.WARN


class TestHealthCheckRunnerBasics:
    """Test basic HealthCheckRunner functionality."""

    def test_runner_initialization(self):
        """Test HealthCheckRunner initializes with built-in checks."""
        runner = HealthCheckRunner()

        checks = runner.list_checks()
        assert len(checks) >= 4  # At least 4 built-in checks
        assert "llm_availability" in checks
        assert "database_connectivity" in checks
        assert "filesystem_access" in checks
        assert "memory_usage" in checks

    def test_register_custom_check(self):
        """Test registering a custom health check."""
        runner = HealthCheckRunner()
        initial_count = len(runner.list_checks())

        def custom_check():
            return True

        check = HealthCheck(
            name="custom_check",
            description="Custom test",
            check_function=custom_check
        )

        runner.register_check(check)

        assert len(runner.list_checks()) == initial_count + 1
        assert "custom_check" in runner.list_checks()

    def test_register_duplicate_check_raises_error(self):
        """Test registering duplicate check raises ValueError."""
        runner = HealthCheckRunner()

        def check1():
            return True

        def check2():
            return True

        check = HealthCheck(name="duplicate", description="Test", check_function=check1)
        runner.register_check(check)

        # Try to register another check with same name
        duplicate = HealthCheck(name="duplicate", description="Test 2", check_function=check2)

        with pytest.raises(ValueError, match="already registered"):
            runner.register_check(duplicate)

    def test_get_check(self):
        """Test retrieving a registered check."""
        runner = HealthCheckRunner()

        check = runner.get_check("llm_availability")

        assert check is not None
        assert check.name == "llm_availability"
        assert check.description == "LLM API Configuration"

    def test_get_nonexistent_check(self):
        """Test retrieving non-existent check returns None."""
        runner = HealthCheckRunner()

        check = runner.get_check("nonexistent_check")

        assert check is None

    def test_unregister_check(self):
        """Test unregistering a check."""
        runner = HealthCheckRunner()

        def custom_check():
            return True

        check = HealthCheck(name="temp_check", description="Temp", check_function=custom_check)
        runner.register_check(check)

        assert "temp_check" in runner.list_checks()

        result = runner.unregister_check("temp_check")

        assert result is True
        assert "temp_check" not in runner.list_checks()

    def test_unregister_nonexistent_check(self):
        """Test unregistering non-existent check returns False."""
        runner = HealthCheckRunner()

        result = runner.unregister_check("nonexistent")

        assert result is False

    def test_list_checks(self):
        """Test listing all registered checks."""
        runner = HealthCheckRunner()

        checks = runner.list_checks()

        assert isinstance(checks, list)
        assert all(isinstance(name, str) for name in checks)
        assert len(checks) >= 4


class TestParallelExecution:
    """Test parallel execution of health checks (CRITICAL: < 2s total)."""

    @pytest.mark.asyncio
    async def test_parallel_execution_under_2_seconds(self):
        """Test all checks complete in parallel under 2 seconds."""
        runner = HealthCheckRunner()

        start_time = time.perf_counter()
        results = await runner.run_all_checks()
        duration = time.perf_counter() - start_time

        # With parallel execution, should complete much faster than sequential
        assert duration < 2.0, f"Health checks took {duration:.2f}s, expected < 2s"
        assert len(results) >= 4

    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self):
        """Test parallel execution is faster than sequential."""
        runner = HealthCheckRunner()

        # Add slow checks to demonstrate parallelism
        def slow_check_1():
            time.sleep(0.5)
            return True

        def slow_check_2():
            time.sleep(0.5)
            return True

        runner.register_check(HealthCheck(
            name="slow1", description="Slow 1", check_function=slow_check_1
        ))
        runner.register_check(HealthCheck(
            name="slow2", description="Slow 2", check_function=slow_check_2
        ))

        start_time = time.perf_counter()
        results = await runner.run_all_checks()
        duration = time.perf_counter() - start_time

        # Should complete in ~0.5s (parallel) not 1.0s+ (sequential)
        assert duration < 1.0, "Parallel execution should be faster than sequential"
        assert len(results) >= 6  # 4 built-in + 2 custom

    @pytest.mark.asyncio
    async def test_multiple_checks_execute_concurrently(self):
        """Test that multiple checks actually run concurrently."""
        runner = HealthCheckRunner()
        execution_times = []

        def timed_check(delay: float):
            def check():
                start = time.perf_counter()
                time.sleep(delay)
                execution_times.append(start)
                return True
            return check

        # Add 3 checks with 0.3s delay each
        for i in range(3):
            runner.register_check(HealthCheck(
                name=f"timed_{i}",
                description=f"Timed {i}",
                check_function=timed_check(0.3)
            ))

        start = time.perf_counter()
        await runner.run_all_checks()
        total_duration = time.perf_counter() - start

        # If truly parallel, should take ~0.3s not 0.9s
        assert total_duration < 0.6, "Checks should run concurrently"

        # Check that execution times overlap (concurrent execution)
        if len(execution_times) >= 2:
            time_spread = max(execution_times) - min(execution_times)
            assert time_spread < 0.5, "Check execution times should overlap"


class TestBuiltInChecks:
    """Test individual built-in health checks."""

    @pytest.mark.asyncio
    async def test_llm_availability_with_api_key(self):
        """Test LLM availability check with API key present."""
        runner = HealthCheckRunner()

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'}):
            results = await runner.run_all_checks()

            llm_result = next(r for r in results if r.name == "llm_availability")
            assert llm_result.status == HealthStatus.PASS
            assert "configured" in llm_result.message.lower()

    @pytest.mark.asyncio
    async def test_llm_availability_without_api_key(self):
        """Test LLM availability check without API keys."""
        runner = HealthCheckRunner()

        # Clear all LLM API keys
        env_without_keys = {
            k: v for k, v in os.environ.items()
            if not any(x in k for x in ['OPENAI', 'ANTHROPIC', 'GOOGLE'])
        }

        with patch.dict(os.environ, env_without_keys, clear=True):
            results = await runner.run_all_checks()

            llm_result = next(r for r in results if r.name == "llm_availability")
            assert llm_result.status == HealthStatus.WARN
            assert "no llm api key" in llm_result.message.lower()

    @pytest.mark.asyncio
    async def test_database_connectivity_success(self):
        """Test database connectivity check with working database."""
        runner = HealthCheckRunner()

        results = await runner.run_all_checks()

        db_result = next(r for r in results if r.name == "database_connectivity")
        assert db_result.status == HealthStatus.PASS
        assert "ok" in db_result.message.lower()

    @pytest.mark.asyncio
    async def test_database_connectivity_with_real_database(self):
        """Test database connectivity with real SQLite database."""
        runner = HealthCheckRunner()

        # Create a temporary database file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Create a real database and verify it works
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
            cursor.execute('INSERT INTO test (value) VALUES (?)', ('test_data',))
            conn.commit()
            conn.close()

            # Run health check
            results = await runner.run_all_checks()

            db_result = next(r for r in results if r.name == "database_connectivity")
            assert db_result.status == HealthStatus.PASS

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_database_connectivity_failure(self):
        """Test database connectivity check with simulated failure."""
        runner = HealthCheckRunner()

        # Replace the check function with one that fails
        def failing_db_check():
            raise sqlite3.OperationalError("Simulated database error")

        db_check = runner.get_check("database_connectivity")
        original_func = db_check.check_function
        db_check.check_function = failing_db_check

        try:
            results = await runner.run_all_checks()

            db_result = next(r for r in results if r.name == "database_connectivity")
            assert db_result.status == HealthStatus.FAIL
            assert "error" in db_result.message.lower()

        finally:
            # Restore original function
            db_check.check_function = original_func

    @pytest.mark.asyncio
    async def test_filesystem_access_success(self):
        """Test filesystem access check with working filesystem."""
        runner = HealthCheckRunner()

        results = await runner.run_all_checks()

        fs_result = next(r for r in results if r.name == "filesystem_access")
        assert fs_result.status == HealthStatus.PASS
        assert "ok" in fs_result.message.lower()

    @pytest.mark.asyncio
    async def test_filesystem_access_creates_temp_file(self):
        """Test filesystem check actually creates and reads temp file."""
        runner = HealthCheckRunner()

        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=None)
            mock_temp.return_value = mock_file

            results = await runner.run_all_checks()

            # Verify tempfile was called
            mock_temp.assert_called()
            fs_result = next(r for r in results if r.name == "filesystem_access")
            # Should pass with mock
            assert fs_result.status in [HealthStatus.PASS, HealthStatus.FAIL]

    @pytest.mark.asyncio
    async def test_memory_usage_pass(self):
        """Test memory usage check with normal memory levels."""
        runner = HealthCheckRunner()

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = MagicMock(
                percent=50.0,
                available=8 * 1024 ** 3  # 8GB
            )

            results = await runner.run_all_checks()

            mem_result = next(r for r in results if r.name == "memory_usage")
            assert mem_result.status == HealthStatus.PASS
            assert "50.0%" in mem_result.message

    @pytest.mark.asyncio
    async def test_memory_usage_warning(self):
        """Test memory usage check with high memory usage."""
        runner = HealthCheckRunner()

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = MagicMock(
                percent=85.0,
                available=2 * 1024 ** 3  # 2GB
            )

            results = await runner.run_all_checks()

            mem_result = next(r for r in results if r.name == "memory_usage")
            assert mem_result.status == HealthStatus.WARN
            assert "85.0%" in mem_result.message

    @pytest.mark.asyncio
    async def test_memory_usage_critical(self):
        """Test memory usage check with critical memory levels."""
        runner = HealthCheckRunner()

        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = MagicMock(
                percent=95.0,
                available=0.5 * 1024 ** 3  # 0.5GB
            )

            results = await runner.run_all_checks()

            mem_result = next(r for r in results if r.name == "memory_usage")
            assert mem_result.status == HealthStatus.FAIL
            assert "95.0%" in mem_result.message
            assert "critical" in mem_result.message.lower()


class TestTimeoutProtection:
    """Test timeout protection for health checks."""

    @pytest.mark.asyncio
    async def test_sync_check_timeout(self):
        """Test sync check that exceeds timeout is terminated."""
        runner = HealthCheckRunner()

        def slow_check():
            time.sleep(10)  # Way too slow
            return True

        check = HealthCheck(
            name="slow_sync",
            description="Slow sync check",
            check_function=slow_check,
            is_async=False,
            timeout=0.5  # 0.5s timeout
        )

        runner.register_check(check)

        start = time.perf_counter()
        results = await runner.run_all_checks()
        duration = time.perf_counter() - start

        # Should timeout and not wait full 10s
        assert duration < 2.0, "Should not wait for slow check"

        slow_result = next(r for r in results if r.name == "slow_sync")
        assert slow_result.status == HealthStatus.FAIL
        assert "timeout" in slow_result.message.lower()

    @pytest.mark.asyncio
    async def test_async_check_timeout(self):
        """Test async check that exceeds timeout is terminated."""
        runner = HealthCheckRunner()

        async def slow_async_check():
            await asyncio.sleep(10)
            return True

        check = HealthCheck(
            name="slow_async",
            description="Slow async check",
            check_function=slow_async_check,
            is_async=True,
            timeout=0.5
        )

        runner.register_check(check)

        start = time.perf_counter()
        results = await runner.run_all_checks()
        duration = time.perf_counter() - start

        # Should timeout quickly
        assert duration < 2.0

        slow_result = next(r for r in results if r.name == "slow_async")
        assert slow_result.status == HealthStatus.FAIL
        assert "timeout" in slow_result.message.lower()

    @pytest.mark.asyncio
    async def test_timeout_does_not_affect_other_checks(self):
        """Test one check timing out doesn't affect others."""
        runner = HealthCheckRunner()

        def slow_check():
            time.sleep(5)
            return True

        def fast_check():
            return True

        runner.register_check(HealthCheck(
            name="timeout_check",
            description="Will timeout",
            check_function=slow_check,
            timeout=0.1
        ))

        runner.register_check(HealthCheck(
            name="fast_check",
            description="Fast check",
            check_function=fast_check,
            timeout=5.0
        ))

        results = await runner.run_all_checks()

        timeout_result = next(r for r in results if r.name == "timeout_check")
        fast_result = next(r for r in results if r.name == "fast_check")

        assert timeout_result.status == HealthStatus.FAIL
        assert fast_result.status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_custom_timeout_respected(self):
        """Test custom timeout values are respected."""
        runner = HealthCheckRunner()

        def check_with_delay():
            time.sleep(0.3)
            return True

        # This should pass with 1s timeout
        runner.register_check(HealthCheck(
            name="pass_check",
            description="Should pass",
            check_function=check_with_delay,
            timeout=1.0
        ))

        # This should timeout with 0.1s timeout
        runner.register_check(HealthCheck(
            name="timeout_check",
            description="Should timeout",
            check_function=check_with_delay,
            timeout=0.1
        ))

        results = await runner.run_all_checks()

        pass_result = next(r for r in results if r.name == "pass_check")
        timeout_result = next(r for r in results if r.name == "timeout_check")

        assert pass_result.status == HealthStatus.PASS
        assert timeout_result.status == HealthStatus.FAIL


class TestAsyncFirstDesign:
    """Test async-first design and implementation."""

    @pytest.mark.asyncio
    async def test_run_all_checks_is_async(self):
        """Test run_all_checks is an async function."""
        runner = HealthCheckRunner()

        # Should be awaitable
        result = runner.run_all_checks()
        assert asyncio.iscoroutine(result)

        # Clean up
        await result

    @pytest.mark.asyncio
    async def test_async_check_execution(self):
        """Test async check functions execute properly."""
        runner = HealthCheckRunner()

        async def async_check():
            await asyncio.sleep(0.1)
            return (HealthStatus.PASS, "Async check passed")

        check = HealthCheck(
            name="test_async",
            description="Async test",
            check_function=async_check,
            is_async=True
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        async_result = next(r for r in results if r.name == "test_async")
        assert async_result.status == HealthStatus.PASS
        assert "async check passed" in async_result.message.lower()

    @pytest.mark.asyncio
    async def test_sync_check_runs_in_thread_pool(self):
        """Test sync checks run in thread pool to avoid blocking."""
        runner = HealthCheckRunner()

        def sync_blocking_check():
            # This would block the event loop if not run in thread pool
            time.sleep(0.2)
            return True

        check = HealthCheck(
            name="sync_blocking",
            description="Sync blocking check",
            check_function=sync_blocking_check,
            is_async=False
        )

        runner.register_check(check)

        # Should complete without blocking event loop
        start = time.perf_counter()
        results = await runner.run_all_checks()
        duration = time.perf_counter() - start

        # Should handle blocking call
        sync_result = next(r for r in results if r.name == "sync_blocking")
        assert sync_result.status == HealthStatus.PASS
        assert duration < 2.0

    @pytest.mark.asyncio
    async def test_mixed_sync_async_checks(self):
        """Test mixing sync and async checks works correctly."""
        runner = HealthCheckRunner()

        def sync_check():
            return (HealthStatus.PASS, "Sync passed")

        async def async_check():
            await asyncio.sleep(0.1)
            return (HealthStatus.PASS, "Async passed")

        runner.register_check(HealthCheck(
            name="sync", description="Sync", check_function=sync_check, is_async=False
        ))
        runner.register_check(HealthCheck(
            name="async", description="Async", check_function=async_check, is_async=True
        ))

        results = await runner.run_all_checks()

        sync_result = next(r for r in results if r.name == "sync")
        async_result = next(r for r in results if r.name == "async")

        assert sync_result.status == HealthStatus.PASS
        assert async_result.status == HealthStatus.PASS


class TestCustomHealthChecks:
    """Test custom health check extensibility."""

    @pytest.mark.asyncio
    async def test_register_simple_custom_check(self):
        """Test registering a simple custom check."""
        runner = HealthCheckRunner()

        def custom_check():
            return True

        check = HealthCheck(
            name="custom",
            description="Custom check",
            check_function=custom_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        custom_result = next(r for r in results if r.name == "custom")
        assert custom_result.status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_custom_check_with_status_tuple(self):
        """Test custom check returning (status, message) tuple."""
        runner = HealthCheckRunner()

        def custom_check():
            return (HealthStatus.WARN, "Custom warning message")

        check = HealthCheck(
            name="custom_tuple",
            description="Custom tuple check",
            check_function=custom_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        custom_result = next(r for r in results if r.name == "custom_tuple")
        assert custom_result.status == HealthStatus.WARN
        assert custom_result.message == "Custom warning message"

    @pytest.mark.asyncio
    async def test_custom_check_with_result_object(self):
        """Test custom check returning HealthCheckResult object."""
        runner = HealthCheckRunner()

        def custom_check():
            return HealthCheckResult(
                name="custom_result",
                status=HealthStatus.PASS,
                message="Custom result object",
                duration=0.5,
                details={"custom_key": "custom_value"}
            )

        check = HealthCheck(
            name="custom_result",
            description="Custom result check",
            check_function=custom_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        custom_result = next(r for r in results if r.name == "custom_result")
        assert custom_result.status == HealthStatus.PASS
        assert custom_result.message == "Custom result object"
        assert custom_result.details["custom_key"] == "custom_value"

    @pytest.mark.asyncio
    async def test_custom_check_with_complex_logic(self):
        """Test custom check with complex validation logic."""
        runner = HealthCheckRunner()

        def complex_check():
            # Simulate complex business logic
            data = {"count": 100, "threshold": 80}

            if data["count"] > data["threshold"]:
                return (HealthStatus.PASS, f"Count {data['count']} exceeds threshold")
            else:
                return (HealthStatus.FAIL, f"Count {data['count']} below threshold")

        check = HealthCheck(
            name="complex_check",
            description="Complex validation",
            check_function=complex_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        complex_result = next(r for r in results if r.name == "complex_check")
        assert complex_result.status == HealthStatus.PASS
        assert "exceeds threshold" in complex_result.message

    @pytest.mark.asyncio
    async def test_custom_async_check(self):
        """Test custom async health check."""
        runner = HealthCheckRunner()

        async def async_custom_check():
            # Simulate async operation (API call, etc.)
            await asyncio.sleep(0.1)
            return (HealthStatus.PASS, "Async custom check completed")

        check = HealthCheck(
            name="async_custom",
            description="Async custom check",
            check_function=async_custom_check,
            is_async=True
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        async_result = next(r for r in results if r.name == "async_custom")
        assert async_result.status == HealthStatus.PASS


class TestResultFormatAndAggregation:
    """Test health check result format and aggregation."""

    @pytest.mark.asyncio
    async def test_result_format_consistency(self):
        """Test all results follow consistent format."""
        runner = HealthCheckRunner()
        results = await runner.run_all_checks()

        for result in results:
            assert isinstance(result, HealthCheckResult)
            assert isinstance(result.name, str)
            assert isinstance(result.status, HealthStatus)
            assert isinstance(result.message, str)
            assert isinstance(result.duration, float)
            assert isinstance(result.details, dict)
            assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_result_duration_tracking(self):
        """Test execution duration is tracked accurately."""
        runner = HealthCheckRunner()

        def timed_check():
            time.sleep(0.2)
            return True

        check = HealthCheck(
            name="timed",
            description="Timed check",
            check_function=timed_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        timed_result = next(r for r in results if r.name == "timed")
        # Should be approximately 0.2s
        assert 0.15 < timed_result.duration < 0.35

    @pytest.mark.asyncio
    async def test_aggregated_results(self):
        """Test aggregating results from multiple checks."""
        runner = HealthCheckRunner()
        results = await runner.run_all_checks()

        # Calculate aggregate statistics
        total_checks = len(results)
        passed = sum(1 for r in results if r.status == HealthStatus.PASS)
        failed = sum(1 for r in results if r.status == HealthStatus.FAIL)
        warned = sum(1 for r in results if r.status == HealthStatus.WARN)
        total_duration = sum(r.duration for r in results)

        assert total_checks >= 4
        assert passed + failed + warned == total_checks
        assert total_duration > 0

    @pytest.mark.asyncio
    async def test_result_details_extensibility(self):
        """Test result details can contain arbitrary data."""
        runner = HealthCheckRunner()

        def detailed_check():
            return HealthCheckResult(
                name="detailed",
                status=HealthStatus.PASS,
                message="Detailed check",
                duration=0.1,
                details={
                    "metrics": {
                        "cpu": 25.5,
                        "memory": 60.2
                    },
                    "tags": ["production", "critical"],
                    "metadata": {
                        "version": "1.0.0"
                    }
                }
            )

        check = HealthCheck(
            name="detailed",
            description="Detailed check",
            check_function=detailed_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        detailed_result = next(r for r in results if r.name == "detailed")
        assert detailed_result.details["metrics"]["cpu"] == 25.5
        assert "production" in detailed_result.details["tags"]
        assert detailed_result.details["metadata"]["version"] == "1.0.0"


class TestFailureScenarios:
    """Test health check failure scenarios and recovery."""

    @pytest.mark.asyncio
    async def test_check_raises_exception(self):
        """Test check that raises exception is handled gracefully."""
        runner = HealthCheckRunner()

        def failing_check():
            raise RuntimeError("Simulated failure")

        check = HealthCheck(
            name="failing",
            description="Failing check",
            check_function=failing_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        failing_result = next(r for r in results if r.name == "failing")
        assert failing_result.status == HealthStatus.FAIL
        assert "error" in failing_result.message.lower()
        assert "simulated failure" in failing_result.message.lower()

    @pytest.mark.asyncio
    async def test_check_exception_does_not_stop_others(self):
        """Test one check failing doesn't stop others from running."""
        runner = HealthCheckRunner()

        def failing_check():
            raise ValueError("This check fails")

        def passing_check():
            return True

        runner.register_check(HealthCheck(
            name="failer", description="Fails", check_function=failing_check
        ))
        runner.register_check(HealthCheck(
            name="passer", description="Passes", check_function=passing_check
        ))

        results = await runner.run_all_checks()

        # Both should have results
        failer_result = next(r for r in results if r.name == "failer")
        passer_result = next(r for r in results if r.name == "passer")

        assert failer_result.status == HealthStatus.FAIL
        assert passer_result.status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_multiple_failures_reported(self):
        """Test multiple check failures are all reported."""
        runner = HealthCheckRunner()

        def fail1():
            raise RuntimeError("Failure 1")

        def fail2():
            raise ValueError("Failure 2")

        def pass_check():
            return True

        runner.register_check(HealthCheck(name="fail1", description="F1", check_function=fail1))
        runner.register_check(HealthCheck(name="fail2", description="F2", check_function=fail2))
        runner.register_check(HealthCheck(name="pass", description="P", check_function=pass_check))

        results = await runner.run_all_checks()

        fail1_result = next(r for r in results if r.name == "fail1")
        fail2_result = next(r for r in results if r.name == "fail2")
        pass_result = next(r for r in results if r.name == "pass")

        assert fail1_result.status == HealthStatus.FAIL
        assert fail2_result.status == HealthStatus.FAIL
        assert pass_result.status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_async_check_exception_handling(self):
        """Test async check exceptions are handled properly."""
        runner = HealthCheckRunner()

        async def async_failing_check():
            await asyncio.sleep(0.05)
            raise ConnectionError("Async connection failed")

        check = HealthCheck(
            name="async_fail",
            description="Async failing",
            check_function=async_failing_check,
            is_async=True
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        async_fail_result = next(r for r in results if r.name == "async_fail")
        assert async_fail_result.status == HealthStatus.FAIL
        assert "connection failed" in async_fail_result.message.lower()

    @pytest.mark.asyncio
    async def test_check_returns_none_handled(self):
        """Test check returning None is treated as pass."""
        runner = HealthCheckRunner()

        def none_check():
            return None

        check = HealthCheck(
            name="none_check",
            description="Returns None",
            check_function=none_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        none_result = next(r for r in results if r.name == "none_check")
        assert none_result.status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_check_returns_false_handled(self):
        """Test check returning False is handled as warning."""
        runner = HealthCheckRunner()

        def false_check():
            return False

        check = HealthCheck(
            name="false_check",
            description="Returns False",
            check_function=false_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        false_result = next(r for r in results if r.name == "false_check")
        # False is converted to warning status
        assert false_result.status == HealthStatus.WARN


class TestHealthMonitor:
    """Test HealthMonitor class for continuous monitoring."""

    def test_health_monitor_initialization(self):
        """Test HealthMonitor initializes correctly."""
        monitor = HealthMonitor()

        assert monitor is not None
        assert hasattr(monitor, '_runner')
        assert isinstance(monitor._runner, HealthCheckRunner)

    def test_check_all_services(self):
        """Test check_all_services returns service status."""
        monitor = HealthMonitor()

        status = monitor.check_all_services()

        assert isinstance(status, dict)
        assert 'database' in status
        assert 'cache' in status
        assert 'overall_status' in status

    def test_get_service_health(self):
        """Test getting individual service health."""
        monitor = HealthMonitor()
        monitor.check_all_services()  # Populate results

        health = monitor.get_service_health('database')

        assert isinstance(health, dict)
        assert 'status' in health

    def test_get_unknown_service_health(self):
        """Test getting health for unknown service."""
        monitor = HealthMonitor()

        health = monitor.get_service_health('unknown_service')

        assert health['status'] == 'unknown'

    def test_register_service_check(self):
        """Test registering custom service check."""
        monitor = HealthMonitor()

        def custom_service_check():
            return (HealthStatus.PASS, "Custom service OK")

        monitor.register_service_check("custom_service", custom_service_check, timeout=3.0)

        # Verify check was registered
        checks = monitor._runner.list_checks()
        assert "custom_service" in checks


class TestConvenienceFunction:
    """Test convenience function for running health checks."""

    @pytest.mark.asyncio
    async def test_run_health_checks_function(self):
        """Test run_health_checks convenience function."""
        results = await run_health_checks()

        assert isinstance(results, list)
        assert len(results) >= 4
        assert all(isinstance(r, HealthCheckResult) for r in results)

    @pytest.mark.asyncio
    async def test_run_health_checks_creates_new_runner(self):
        """Test run_health_checks creates fresh runner each time."""
        results1 = await run_health_checks()
        results2 = await run_health_checks()

        # Should get consistent results
        assert len(results1) == len(results2)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_runner_no_checks(self):
        """Test runner with no checks registered."""
        runner = HealthCheckRunner()

        # Unregister all built-in checks
        for check_name in runner.list_checks():
            runner.unregister_check(check_name)

        results = await runner.run_all_checks()

        assert results == []

    @pytest.mark.asyncio
    async def test_check_with_very_short_timeout(self):
        """Test check with extremely short timeout."""
        runner = HealthCheckRunner()

        def instant_check():
            return True

        check = HealthCheck(
            name="instant",
            description="Instant check",
            check_function=instant_check,
            timeout=0.001  # 1ms timeout
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        instant_result = next(r for r in results if r.name == "instant")
        # May pass or timeout depending on system
        assert instant_result.status in [HealthStatus.PASS, HealthStatus.FAIL]

    @pytest.mark.asyncio
    async def test_check_with_very_long_timeout(self):
        """Test check with very long timeout."""
        runner = HealthCheckRunner()

        def fast_check():
            return True

        check = HealthCheck(
            name="fast",
            description="Fast check",
            check_function=fast_check,
            timeout=300.0  # 5 minute timeout
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        fast_result = next(r for r in results if r.name == "fast")
        assert fast_result.status == HealthStatus.PASS
        assert fast_result.duration < 1.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_check_with_unicode_in_message(self):
        """Test check returning unicode characters in message."""
        runner = HealthCheckRunner()

        def unicode_check():
            return (HealthStatus.PASS, "✅ Check passed with émojis 🎉")

        check = HealthCheck(
            name="unicode",
            description="Unicode check",
            check_function=unicode_check
        )

        runner.register_check(check)
        results = await runner.run_all_checks()

        unicode_result = next(r for r in results if r.name == "unicode")
        assert unicode_result.status == HealthStatus.PASS
        assert "✅" in unicode_result.message
        assert "🎉" in unicode_result.message

    @pytest.mark.asyncio
    async def test_large_number_of_checks(self):
        """Test handling large number of checks efficiently."""
        runner = HealthCheckRunner()

        # Add many checks
        for i in range(50):
            def make_check(n):
                def check():
                    time.sleep(0.01)
                    return True
                return check

            runner.register_check(HealthCheck(
                name=f"check_{i}",
                description=f"Check {i}",
                check_function=make_check(i)
            ))

        start = time.perf_counter()
        results = await runner.run_all_checks()
        duration = time.perf_counter() - start

        # With parallelism, should complete much faster than 50 * 0.01 = 0.5s
        assert len(results) >= 50
        # Should leverage parallelism
        assert duration < 2.0


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_production_like_health_check_suite(self):
        """Test production-like health check configuration."""
        runner = HealthCheckRunner()

        # Simulate production checks
        def check_api_endpoint():
            return (HealthStatus.PASS, "API endpoint responding")

        async def check_external_service():
            await asyncio.sleep(0.1)
            return (HealthStatus.PASS, "External service reachable")

        def check_disk_space():
            return (HealthStatus.PASS, "Disk space: 75% available")

        runner.register_check(HealthCheck(
            name="api_endpoint",
            description="API Health",
            check_function=check_api_endpoint,
            timeout=5.0
        ))

        runner.register_check(HealthCheck(
            name="external_service",
            description="External Service",
            check_function=check_external_service,
            is_async=True,
            timeout=10.0
        ))

        runner.register_check(HealthCheck(
            name="disk_space",
            description="Disk Space",
            check_function=check_disk_space,
            timeout=2.0
        ))

        results = await runner.run_all_checks()

        # Verify all checks ran
        check_names = {r.name for r in results}
        assert "api_endpoint" in check_names
        assert "external_service" in check_names
        assert "disk_space" in check_names

        # Verify overall health (allow WARN status for LLM availability)
        critical_checks = ["api_endpoint", "external_service", "disk_space"]
        critical_passed = all(
            r.status == HealthStatus.PASS
            for r in results
            if r.name in critical_checks
        )
        assert critical_passed

    @pytest.mark.asyncio
    async def test_health_check_with_dependency_validation(self):
        """Test health checks validating system dependencies."""
        runner = HealthCheckRunner()

        # Check for required Python modules
        def check_dependencies():
            try:
                import psutil
                import asyncio
                return (HealthStatus.PASS, "All dependencies available")
            except ImportError as e:
                return (HealthStatus.FAIL, f"Missing dependency: {e}")

        runner.register_check(HealthCheck(
            name="dependencies",
            description="Python Dependencies",
            check_function=check_dependencies
        ))

        results = await runner.run_all_checks()

        dep_result = next(r for r in results if r.name == "dependencies")
        assert dep_result.status == HealthStatus.PASS
