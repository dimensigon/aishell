"""
Tests for performance module.

Covers optimization, monitoring, and caching functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.performance.optimizer import PerformanceOptimizer, OptimizationMetrics
from src.performance.monitor import SystemMonitor, HealthStatus, HealthCheck
from src.performance.cache import QueryCache, CacheEntry


class TestPerformanceOptimizer:
    """Test cases for PerformanceOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance."""
        return PerformanceOptimizer({'slow_query_threshold': 0.5})

    @pytest.mark.asyncio
    async def test_optimize_query_basic(self, optimizer):
        """Test basic query optimization."""
        query = "SELECT * FROM users WHERE id = 1"
        optimized = await optimizer.optimize_query(query)
        assert optimized is not None
        assert len(optimized) > 0

    @pytest.mark.asyncio
    async def test_optimize_query_disabled(self, optimizer):
        """Test optimization when disabled."""
        optimizer.enable_optimization(False)
        query = "SELECT * FROM users"
        optimized = await optimizer.optimize_query(query)
        assert optimized == query

    @pytest.mark.asyncio
    async def test_record_execution(self, optimizer):
        """Test recording query execution metrics."""
        query = "SELECT * FROM users"
        await optimizer.record_execution(query, 0.1)
        await optimizer.record_execution(query, 0.2)

        metrics = await optimizer.get_metrics()
        assert metrics.query_count == 2
        assert metrics.avg_execution_time > 0

    @pytest.mark.asyncio
    async def test_slow_query_detection(self, optimizer):
        """Test slow query detection."""
        query = "SELECT * FROM large_table"
        await optimizer.record_execution(query, 1.5)  # Exceeds threshold

        metrics = await optimizer.get_metrics()
        assert len(metrics.slow_queries) > 0

    @pytest.mark.asyncio
    async def test_suggest_indexes(self, optimizer):
        """Test index suggestions."""
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        await optimizer.record_execution(query, 2.0)

        suggestions = await optimizer.suggest_indexes()
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_optimize_connection_pool_high_usage(self, optimizer):
        """Test connection pool optimization for high usage."""
        config = await optimizer.optimize_connection_pool(0.9)
        assert config['max_size'] > 10

    @pytest.mark.asyncio
    async def test_optimize_connection_pool_low_usage(self, optimizer):
        """Test connection pool optimization for low usage."""
        config = await optimizer.optimize_connection_pool(0.1)
        assert config['max_size'] >= config['min_size']

    @pytest.mark.asyncio
    async def test_reset_stats(self, optimizer):
        """Test statistics reset."""
        await optimizer.record_execution("SELECT 1", 0.1)
        await optimizer.reset_stats()

        metrics = await optimizer.get_metrics()
        assert metrics.query_count == 0

    @pytest.mark.asyncio
    async def test_pattern_extraction(self, optimizer):
        """Test query pattern extraction."""
        query1 = "SELECT * FROM users WHERE id = 1"
        query2 = "SELECT * FROM users WHERE id = 2"

        await optimizer.record_execution(query1, 0.1)
        await optimizer.record_execution(query2, 0.1)

        # Both should be grouped under same pattern
        assert len(optimizer._query_patterns) > 0

    @pytest.mark.asyncio
    async def test_metrics_aggregation(self, optimizer):
        """Test metrics aggregation across multiple queries."""
        queries = [
            ("SELECT * FROM users", 0.1),
            ("SELECT * FROM orders", 0.2),
            ("SELECT * FROM products", 0.15)
        ]

        for query, time in queries:
            await optimizer.record_execution(query, time)

        metrics = await optimizer.get_metrics()
        assert metrics.query_count == 3
        assert 0.1 <= metrics.avg_execution_time <= 0.2


class TestSystemMonitor:
    """Test cases for SystemMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        return SystemMonitor({
            'cpu_threshold': 80.0,
            'memory_threshold': 85.0,
            'check_interval': 1
        })

    @pytest.mark.asyncio
    async def test_perform_health_check(self, monitor):
        """Test health check execution."""
        checks = await monitor.perform_health_check()
        assert 'system' in checks
        assert 'database' in checks
        assert 'performance' in checks

    @pytest.mark.asyncio
    async def test_health_check_status(self, monitor):
        """Test health check status determination."""
        checks = await monitor.perform_health_check()
        for check in checks.values():
            assert isinstance(check, HealthCheck)
            assert isinstance(check.status, HealthStatus)

    @pytest.mark.asyncio
    async def test_record_metrics(self, monitor):
        """Test metrics recording."""
        await monitor.record_metrics(
            active_connections=5,
            query_count=10,
            avg_response_time=0.5
        )

        assert len(monitor.metrics_history) == 1
        assert monitor.metrics_history[0].query_count == 10

    @pytest.mark.asyncio
    async def test_get_health_summary(self, monitor):
        """Test health summary generation."""
        await monitor.perform_health_check()
        summary = await monitor.get_health_summary()

        assert 'status' in summary
        assert 'checks' in summary
        assert isinstance(summary['checks'], list)

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, monitor):
        """Test metrics summary generation."""
        await monitor.record_metrics(5, 10, 0.5)
        await monitor.record_metrics(6, 15, 0.6)

        summary = await monitor.get_metrics_summary(duration_minutes=60)
        assert 'metrics' in summary
        assert summary['sample_count'] == 2

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, monitor):
        """Test start/stop monitoring."""
        await monitor.start_monitoring()
        assert monitor._monitoring

        await asyncio.sleep(0.1)

        await monitor.stop_monitoring()
        assert not monitor._monitoring

    @pytest.mark.asyncio
    async def test_clear_history(self, monitor):
        """Test history clearing."""
        await monitor.perform_health_check()
        await monitor.record_metrics(5, 10, 0.5)

        await monitor.clear_history()
        assert len(monitor.health_checks) == 0
        assert len(monitor.metrics_history) == 0


class TestQueryCache:
    """Test cases for QueryCache."""

    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return QueryCache({
            'max_size': 100,
            'default_ttl': 60,
            'max_memory_mb': 10
        })

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """Test basic cache set/get."""
        query = "SELECT * FROM users"
        result = [{'id': 1, 'name': 'Test'}]

        await cache.set(query, result)
        cached = await cache.get(query)

        assert cached == result

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss."""
        result = await cache.get("SELECT * FROM nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_with_params(self, cache):
        """Test caching with parameters."""
        query = "SELECT * FROM users WHERE id = ?"
        params = {'id': 1}
        result = [{'id': 1, 'name': 'Test'}]

        await cache.set(query, result, params)
        cached = await cache.get(query, params)

        assert cached == result

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache):
        """Test TTL expiration."""
        query = "SELECT * FROM users"
        result = [{'id': 1}]

        # Create entry with very short TTL
        await cache.set(query, result, ttl_seconds=0)
        await asyncio.sleep(0.1)

        cached = await cache.get(query)
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_invalidate(self, cache):
        """Test cache invalidation."""
        query = "SELECT * FROM users"
        result = [{'id': 1}]

        await cache.set(query, result)
        await cache.invalidate(query)

        cached = await cache.get(query)
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """Test cache clearing."""
        await cache.set("SELECT 1", [1])
        await cache.set("SELECT 2", [2])

        await cache.clear()
        stats = await cache.get_stats()

        assert stats['size'] == 0

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics."""
        await cache.set("SELECT 1", [1])
        await cache.get("SELECT 1")  # Hit
        await cache.get("SELECT 2")  # Miss

        stats = await cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache):
        """Test LRU eviction."""
        small_cache = QueryCache({'max_size': 2})

        await small_cache.set("Q1", [1])
        await small_cache.set("Q2", [2])
        await small_cache.set("Q3", [3])  # Should evict Q1

        assert await small_cache.get("Q1") is None
        assert await small_cache.get("Q2") == [2]
        assert await small_cache.get("Q3") == [3]

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache):
        """Test expired entry cleanup."""
        await cache.set("Q1", [1], ttl_seconds=0)
        await asyncio.sleep(0.1)

        removed = await cache.cleanup_expired()
        assert removed == 1

    @pytest.mark.asyncio
    async def test_top_entries(self, cache):
        """Test getting top accessed entries."""
        await cache.set("Q1", [1])
        await cache.set("Q2", [2])

        # Access Q1 multiple times
        await cache.get("Q1")
        await cache.get("Q1")
        await cache.get("Q2")

        top = await cache.get_top_entries(limit=2)
        assert len(top) <= 2
        assert top[0]['access_count'] >= top[1]['access_count']
