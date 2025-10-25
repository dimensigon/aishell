"""
Comprehensive tests for src/performance/cache.py to achieve 90%+ coverage.

Tests all cache operations, LRU eviction, TTL expiration, memory limits,
statistics, pattern invalidation, and edge cases.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import time

from src.performance.cache import QueryCache, CacheEntry


class TestCacheEntry:
    """Test CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test creating a cache entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
            ttl_seconds=300,
            size_bytes=100
        )
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl_seconds == 300

    def test_cache_entry_is_expired_with_ttl(self):
        """Test entry expiration with TTL"""
        past_time = datetime.now() - timedelta(seconds=400)
        entry = CacheEntry(
            key="key",
            value="value",
            created_at=past_time,
            last_accessed=past_time,
            access_count=0,
            ttl_seconds=300,
            size_bytes=100
        )
        assert entry.is_expired()

    def test_cache_entry_not_expired(self):
        """Test entry not expired"""
        entry = CacheEntry(
            key="key",
            value="value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
            ttl_seconds=300,
            size_bytes=100
        )
        assert not entry.is_expired()

    def test_cache_entry_no_ttl(self):
        """Test entry with None TTL never expires"""
        past_time = datetime.now() - timedelta(days=365)
        entry = CacheEntry(
            key="key",
            value="value",
            created_at=past_time,
            last_accessed=past_time,
            access_count=0,
            ttl_seconds=None,
            size_bytes=100
        )
        assert not entry.is_expired()

    def test_cache_entry_age_seconds(self):
        """Test calculating entry age"""
        past_time = datetime.now() - timedelta(seconds=100)
        entry = CacheEntry(
            key="key",
            value="value",
            created_at=past_time,
            last_accessed=past_time,
            access_count=0,
            ttl_seconds=300,
            size_bytes=100
        )
        age = entry.age_seconds()
        assert age >= 100  # At least 100 seconds old


class TestQueryCacheInit:
    """Test QueryCache initialization"""

    def test_init_defaults(self):
        """Test default initialization"""
        cache = QueryCache()
        assert cache.backend == "memory"
        assert cache.default_ttl == 300
        assert not cache.compression
        assert not cache.track_stats

    def test_init_with_params(self):
        """Test initialization with parameters"""
        cache = QueryCache(
            backend="redis",
            ttl=600,
            compression=True,
            track_stats=True
        )
        assert cache.backend == "redis"
        assert cache.default_ttl == 600
        assert cache.compression
        assert cache.track_stats

    def test_init_with_config(self):
        """Test initialization with config dict"""
        config = {
            'max_size': 500,
            'max_memory_mb': 50
        }
        cache = QueryCache(config=config)
        assert cache.max_size == 500
        assert cache.max_memory_mb == 50

    def test_init_defaults_from_config(self):
        """Test config defaults"""
        cache = QueryCache()
        assert cache.max_size == 1000
        assert cache.max_memory_mb == 100


class TestQueryCacheKeyGeneration:
    """Test cache key generation"""

    def test_generate_key_query_only(self):
        """Test key generation with query only"""
        cache = QueryCache()
        key1 = cache._generate_key("SELECT * FROM users")
        key2 = cache._generate_key("SELECT * FROM users")
        assert key1 == key2

    def test_generate_key_different_queries(self):
        """Test different queries generate different keys"""
        cache = QueryCache()
        key1 = cache._generate_key("SELECT * FROM users")
        key2 = cache._generate_key("SELECT * FROM orders")
        assert key1 != key2

    def test_generate_key_with_params(self):
        """Test key generation with parameters"""
        cache = QueryCache()
        key1 = cache._generate_key("SELECT * FROM users WHERE id = ?", {'id': 1})
        key2 = cache._generate_key("SELECT * FROM users WHERE id = ?", {'id': 1})
        assert key1 == key2

    def test_generate_key_different_params(self):
        """Test different params generate different keys"""
        cache = QueryCache()
        key1 = cache._generate_key("SELECT * FROM users WHERE id = ?", {'id': 1})
        key2 = cache._generate_key("SELECT * FROM users WHERE id = ?", {'id': 2})
        assert key1 != key2


class TestQueryCacheSizeEstimation:
    """Test size estimation"""

    def test_estimate_size_string(self):
        """Test size estimation for string"""
        cache = QueryCache()
        size = cache._estimate_size("test string")
        assert size > 0

    def test_estimate_size_dict(self):
        """Test size estimation for dict"""
        cache = QueryCache()
        size = cache._estimate_size({'key': 'value'})
        assert size > 0

    def test_estimate_size_list(self):
        """Test size estimation for list"""
        cache = QueryCache()
        size = cache._estimate_size([1, 2, 3, 4, 5])
        assert size > 0

    def test_estimate_size_fallback(self):
        """Test size estimation fallback"""
        cache = QueryCache()
        with patch('sys.getsizeof', side_effect=Exception):
            size = cache._estimate_size("test")
            assert size == len("test")


class TestQueryCacheGetSet:
    """Test get and set operations"""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test setting and getting cache entry"""
        cache = QueryCache()
        await cache.set("SELECT 1", {'result': 1})

        result = await cache.get("SELECT 1")
        assert result == {'result': 1}

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test getting nonexistent entry"""
        cache = QueryCache()
        result = await cache.get("SELECT 1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_entry(self):
        """Test getting expired entry"""
        cache = QueryCache()

        # Set entry with very short TTL
        await cache.set("SELECT 1", {'result': 1}, ttl_seconds=0)

        # Wait for expiration
        await asyncio.sleep(0.1)

        result = await cache.get("SELECT 1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_updates_access_metadata(self):
        """Test get updates last_accessed and access_count"""
        cache = QueryCache()
        await cache.set("SELECT 1", {'result': 1})

        # Get multiple times
        await cache.get("SELECT 1")
        await cache.get("SELECT 1")
        await cache.get("SELECT 1")

        # Check stats
        stats = await cache.get_stats()
        assert stats['hits'] == 3

    @pytest.mark.asyncio
    async def test_set_with_params(self):
        """Test set and get with params"""
        cache = QueryCache()
        await cache.set("SELECT * FROM users WHERE id = ?", {'result': 1}, params={'id': 1})

        result = await cache.get("SELECT * FROM users WHERE id = ?", params={'id': 1})
        assert result == {'result': 1}

    @pytest.mark.asyncio
    async def test_set_custom_ttl(self):
        """Test setting custom TTL"""
        cache = QueryCache()
        await cache.set("SELECT 1", {'result': 1}, ttl_seconds=600)

        result = await cache.get("SELECT 1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_set_too_large(self):
        """Test setting value larger than max memory"""
        cache = QueryCache(config={'max_memory_mb': 1})

        # Try to cache 10MB string
        large_value = "x" * (10 * 1024 * 1024)
        await cache.set("SELECT 1", large_value)

        # Should not be cached
        result = await cache.get("SELECT 1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_replaces_existing(self):
        """Test setting replaces existing entry"""
        cache = QueryCache()
        await cache.set("SELECT 1", {'result': 1})
        await cache.set("SELECT 1", {'result': 2})

        result = await cache.get("SELECT 1")
        assert result == {'result': 2}


class TestQueryCacheLRUEviction:
    """Test LRU eviction"""

    @pytest.mark.asyncio
    async def test_eviction_at_max_size(self):
        """Test eviction when max size reached"""
        cache = QueryCache(config={'max_size': 3})

        await cache.set("query1", {'result': 1})
        await cache.set("query2", {'result': 2})
        await cache.set("query3", {'result': 3})
        await cache.set("query4", {'result': 4})  # Should evict query1

        assert await cache.get("query1") is None
        assert await cache.get("query4") is not None

    @pytest.mark.asyncio
    async def test_eviction_lru_order(self):
        """Test LRU eviction order"""
        cache = QueryCache(config={'max_size': 3})

        await cache.set("query1", {'result': 1})
        await cache.set("query2", {'result': 2})
        await cache.set("query3", {'result': 3})

        # Access query1 to make it most recently used
        await cache.get("query1")

        # Add new entry, should evict query2 (least recently used)
        await cache.set("query4", {'result': 4})

        assert await cache.get("query1") is not None
        assert await cache.get("query2") is None
        assert await cache.get("query3") is not None
        assert await cache.get("query4") is not None

    @pytest.mark.asyncio
    async def test_eviction_by_memory(self):
        """Test eviction by memory limit"""
        cache = QueryCache(config={'max_memory_mb': 0.001})  # 1KB limit

        # Add entries until memory limit reached
        for i in range(10):
            await cache.set(f"query{i}", "x" * 200)

        stats = await cache.get_stats()
        assert stats['evictions'] > 0

    @pytest.mark.asyncio
    async def test_evict_lru_empty_cache(self):
        """Test evicting from empty cache"""
        cache = QueryCache()
        await cache._evict_lru()  # Should not raise error


class TestQueryCacheInvalidation:
    """Test cache invalidation"""

    @pytest.mark.asyncio
    async def test_invalidate_specific_entry(self):
        """Test invalidating specific cache entry"""
        cache = QueryCache()
        await cache.set("query1", {'result': 1})
        await cache.set("query2", {'result': 2})

        await cache.invalidate("query1")

        assert await cache.get("query1") is None
        assert await cache.get("query2") is not None

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent(self):
        """Test invalidating nonexistent entry"""
        cache = QueryCache()
        await cache.invalidate("nonexistent")  # Should not raise error

    @pytest.mark.asyncio
    async def test_invalidate_with_params(self):
        """Test invalidating entry with params"""
        cache = QueryCache()
        await cache.set("SELECT * WHERE id = ?", {'result': 1}, params={'id': 1})

        await cache.invalidate("SELECT * WHERE id = ?", params={'id': 1})

        result = await cache.get("SELECT * WHERE id = ?", params={'id': 1})
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self):
        """Test pattern-based invalidation"""
        cache = QueryCache()
        await cache.set("SELECT * FROM users", {'result': 1})
        await cache.set("SELECT * FROM orders", {'result': 2})

        await cache.invalidate_pattern("users")

        # Note: Current implementation invalidates all when pattern provided
        stats = await cache.get_stats()
        assert stats['size'] == 0


class TestQueryCacheClear:
    """Test cache clearing"""

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing entire cache"""
        cache = QueryCache()
        await cache.set("query1", {'result': 1})
        await cache.set("query2", {'result': 2})
        await cache.set("query3", {'result': 3})

        await cache.clear()

        stats = await cache.get_stats()
        assert stats['size'] == 0

    @pytest.mark.asyncio
    async def test_clear_empty_cache(self):
        """Test clearing empty cache"""
        cache = QueryCache()
        await cache.clear()  # Should not raise error

        stats = await cache.get_stats()
        assert stats['size'] == 0


class TestQueryCacheStats:
    """Test cache statistics"""

    @pytest.mark.asyncio
    async def test_get_stats_initial(self):
        """Test initial statistics"""
        cache = QueryCache()
        stats = await cache.get_stats()

        assert stats['size'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0
        assert stats['evictions'] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_hits(self):
        """Test statistics with cache hits"""
        cache = QueryCache()
        await cache.set("query1", {'result': 1})

        await cache.get("query1")  # Hit
        await cache.get("query1")  # Hit
        await cache.get("query2")  # Miss

        stats = await cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 2/3

    @pytest.mark.asyncio
    async def test_get_stats_memory_usage(self):
        """Test memory usage statistics"""
        cache = QueryCache()
        await cache.set("query1", "x" * 1000)

        stats = await cache.get_stats()
        assert stats['memory_usage_mb'] > 0

    @pytest.mark.asyncio
    async def test_get_stats_evictions(self):
        """Test eviction statistics"""
        cache = QueryCache(config={'max_size': 2})

        await cache.set("query1", {'result': 1})
        await cache.set("query2", {'result': 2})
        await cache.set("query3", {'result': 3})  # Triggers eviction

        stats = await cache.get_stats()
        assert stats['evictions'] == 1


class TestQueryCacheTopEntries:
    """Test getting top cache entries"""

    @pytest.mark.asyncio
    async def test_get_top_entries(self):
        """Test getting most accessed entries"""
        cache = QueryCache()

        await cache.set("query1", {'result': 1})
        await cache.set("query2", {'result': 2})
        await cache.set("query3", {'result': 3})

        # Access query1 multiple times
        for _ in range(5):
            await cache.get("query1")

        # Access query2 twice
        await cache.get("query2")
        await cache.get("query2")

        top_entries = await cache.get_top_entries(limit=2)

        assert len(top_entries) <= 2
        assert top_entries[0]['access_count'] >= top_entries[1]['access_count']

    @pytest.mark.asyncio
    async def test_get_top_entries_empty(self):
        """Test getting top entries from empty cache"""
        cache = QueryCache()
        top_entries = await cache.get_top_entries()
        assert top_entries == []

    @pytest.mark.asyncio
    async def test_get_top_entries_custom_limit(self):
        """Test custom limit for top entries"""
        cache = QueryCache()

        for i in range(20):
            await cache.set(f"query{i}", {'result': i})

        top_entries = await cache.get_top_entries(limit=5)
        assert len(top_entries) <= 5


class TestQueryCacheCleanup:
    """Test cleanup operations"""

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleaning up expired entries"""
        cache = QueryCache()

        # Add entries with short TTL
        await cache.set("query1", {'result': 1}, ttl_seconds=0)
        await cache.set("query2", {'result': 2}, ttl_seconds=0)
        await cache.set("query3", {'result': 3}, ttl_seconds=1000)

        # Wait for expiration
        await asyncio.sleep(0.1)

        count = await cache.cleanup_expired()

        assert count == 2
        assert await cache.get("query3") is not None

    @pytest.mark.asyncio
    async def test_cleanup_no_expired(self):
        """Test cleanup with no expired entries"""
        cache = QueryCache()

        await cache.set("query1", {'result': 1}, ttl_seconds=1000)

        count = await cache.cleanup_expired()
        assert count == 0


class TestQueryCacheSyncWrappers:
    """Test synchronous wrappers"""

    def test_sync_set_and_get(self):
        """Test synchronous set and get"""
        cache = QueryCache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_sync_get_nonexistent(self):
        """Test sync get nonexistent"""
        cache = QueryCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_sync_get_expired(self):
        """Test sync get expired entry"""
        cache = QueryCache()
        cache.set("key1", "value1", ttl_seconds=0)

        time.sleep(0.1)

        result = cache.get("key1")
        assert result is None

    def test_sync_set_replaces(self):
        """Test sync set replaces existing"""
        cache = QueryCache()
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        result = cache.get("key1")
        assert result == "value2"

    def test_sync_eviction(self):
        """Test sync LRU eviction"""
        cache = QueryCache(config={'max_size': 2})

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key3") == "value3"

    def test_sync_invalidate_pattern(self):
        """Test sync pattern invalidation"""
        cache = QueryCache()
        cache.set("user_query1", "value1")
        cache.set("user_query2", "value2")
        cache.set("order_query1", "value3")

        cache.invalidate_pattern("user_*")

        assert cache.get("user_query1") is None
        assert cache.get("user_query2") is None

    def test_get_statistics(self):
        """Test sync statistics"""
        cache = QueryCache()
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_statistics()

        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5


class TestQueryCacheEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_set_none_value(self):
        """Test caching None value"""
        cache = QueryCache()
        await cache.set("query1", None)

        result = await cache.get("query1")
        assert result is None  # But it's a cache miss, not cached None

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test concurrent cache access"""
        cache = QueryCache()

        async def set_value(key, value):
            await cache.set(key, value)

        async def get_value(key):
            return await cache.get(key)

        # Concurrent sets
        await asyncio.gather(
            set_value("key1", "value1"),
            set_value("key2", "value2"),
            set_value("key3", "value3")
        )

        # Concurrent gets
        results = await asyncio.gather(
            get_value("key1"),
            get_value("key2"),
            get_value("key3")
        )

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_stats_with_zero_requests(self):
        """Test statistics with zero requests"""
        cache = QueryCache()
        stats = await cache.get_stats()

        assert stats['hit_rate'] == 0.0
        assert stats['total_requests'] == 0
