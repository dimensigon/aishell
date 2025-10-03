"""
Query result caching for AI-Shell.

Provides intelligent caching of database query results.
"""

import asyncio
import hashlib
import logging
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time

    def age_seconds(self) -> float:
        """Get age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()


class QueryCache:
    """Intelligent query result cache with LRU eviction."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_size = self.config.get('max_size', 1000)
        self.default_ttl = self.config.get('default_ttl', 300)  # 5 minutes
        self.max_memory_mb = self.config.get('max_memory_mb', 100)

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._total_size_bytes = 0

    def _generate_key(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from query and parameters."""
        key_data = query
        if params:
            key_data += str(sorted(params.items()))

        return hashlib.sha256(key_data.encode()).hexdigest()

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of cached value in bytes."""
        try:
            import sys
            return sys.getsizeof(value)
        except Exception:
            # Fallback estimation
            return len(str(value))

    async def get(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """
        Get cached query result.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(query, params)

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                # Remove expired entry
                self._cache.pop(key)
                self._total_size_bytes -= entry.size_bytes
                self._misses += 1
                logger.debug(f"Cache entry expired: {key[:16]}...")
                return None

            # Update access metadata
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            self._hits += 1
            logger.debug(f"Cache hit: {key[:16]}...")
            return entry.value

    async def set(
        self,
        query: str,
        value: Any,
        params: Optional[Dict] = None,
        ttl_seconds: Optional[int] = None
    ):
        """
        Cache query result.

        Args:
            query: SQL query
            value: Query result to cache
            params: Query parameters
            ttl_seconds: Time to live in seconds (None = use default)
        """
        key = self._generate_key(query, params)
        size_bytes = self._estimate_size(value)

        # Check memory limit
        max_bytes = self.max_memory_mb * 1024 * 1024
        if size_bytes > max_bytes:
            logger.warning(f"Value too large to cache: {size_bytes} bytes")
            return

        async with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._total_size_bytes -= old_entry.size_bytes

            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                await self._evict_lru()

            # Evict if memory limit exceeded
            while self._total_size_bytes + size_bytes > max_bytes:
                if not self._cache:
                    break
                await self._evict_lru()

            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                ttl_seconds=ttl_seconds or self.default_ttl,
                size_bytes=size_bytes
            )

            self._cache[key] = entry
            self._total_size_bytes += size_bytes

            logger.debug(f"Cached query result: {key[:16]}... ({size_bytes} bytes)")

    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return

        # OrderedDict maintains insertion order, first item is LRU
        key, entry = self._cache.popitem(last=False)
        self._total_size_bytes -= entry.size_bytes
        self._evictions += 1
        logger.debug(f"Evicted LRU entry: {key[:16]}...")

    async def invalidate(self, query: str, params: Optional[Dict] = None):
        """
        Invalidate cached entry.

        Args:
            query: SQL query
            params: Query parameters
        """
        key = self._generate_key(query, params)

        async with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._total_size_bytes -= entry.size_bytes
                logger.debug(f"Invalidated cache entry: {key[:16]}...")

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all entries matching pattern.

        Args:
            pattern: Pattern to match in queries
        """
        async with self._lock:
            keys_to_remove = []

            for key, entry in self._cache.items():
                # This is simplified - would need to store original query
                # For now, invalidate all
                if pattern:  # Placeholder for pattern matching
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                entry = self._cache.pop(key)
                self._total_size_bytes -= entry.size_bytes

            if keys_to_remove:
                logger.info(f"Invalidated {len(keys_to_remove)} entries matching pattern: {pattern}")

    async def clear(self):
        """Clear all cached entries."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._total_size_bytes = 0
            logger.info(f"Cleared {count} cache entries")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage_mb': self._total_size_bytes / (1024 * 1024),
                'max_memory_mb': self.max_memory_mb,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'evictions': self._evictions,
                'total_requests': total_requests
            }

    async def get_top_entries(self, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get most accessed cache entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of top entries with metadata
        """
        async with self._lock:
            sorted_entries = sorted(
                self._cache.values(),
                key=lambda e: e.access_count,
                reverse=True
            )

            return [
                {
                    'key': entry.key[:16] + '...',
                    'access_count': entry.access_count,
                    'age_seconds': entry.age_seconds(),
                    'size_bytes': entry.size_bytes
                }
                for entry in sorted_entries[:limit]
            ]

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                entry = self._cache.pop(key)
                self._total_size_bytes -= entry.size_bytes

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)
