"""
Extended cache implementations with fallback mechanisms.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Optional
from .cache import QueryCache


class CacheFallback(QueryCache):
    """
    Cache with fallback mechanism for when live queries fail.
    """

    async def execute_with_fallback(
        self,
        query: str,
        executor: Callable,
        use_cache: bool = True
    ) -> Any:
        """
        Execute query with cache fallback.

        Args:
            query: SQL query
            executor: Function to execute query
            use_cache: Whether to use cache on failure

        Returns:
            Query result
        """
        try:
            # Try live query first
            result = await executor()
            # Cache successful result
            self.set(query, result)
            return result
        except Exception as e:
            # Live query failed, try cache
            if use_cache:
                cached = self.get(query)
                if cached is not None:
                    return cached
            raise


class StaleCache(QueryCache):
    """
    Cache that accepts stale entries when fresh data unavailable.
    """

    def __init__(self, ttl: float = 300, stale_ttl: float = 3600, **kwargs):
        """
        Initialize stale cache.

        Args:
            ttl: Fresh data TTL in seconds
            stale_ttl: Stale data TTL in seconds (longer)
        """
        super().__init__(ttl=ttl, **kwargs)
        self.stale_ttl = stale_ttl

    def _get_sync(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """
        Get value from cache, optionally allowing stale entries.

        Args:
            key: Cache key
            allow_stale: Whether to return stale entries

        Returns:
            Cached value or None
        """
        entry = self._cache.get(key)

        if entry is None:
            return None

        # Check if expired
        if entry.is_expired():
            # Check if within stale TTL
            age = entry.age_seconds()
            if allow_stale and age <= self.stale_ttl:
                # Return stale entry
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry.value
            else:
                # Too stale, remove
                self._cache.pop(key)
                self._total_size_bytes -= entry.size_bytes
                return None

        # Not expired, return fresh value
        entry.last_accessed = datetime.now()
        entry.access_count += 1
        self._cache.move_to_end(key)
        return entry.value

    async def get_or_fetch(
        self,
        key: str,
        fetcher: Callable,
        allow_stale: bool = True,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Get value from cache or fetch, accepting stale on timeout.

        Args:
            key: Cache key
            fetcher: Function to fetch fresh data
            allow_stale: Whether to accept stale data
            timeout: Fetch timeout in seconds

        Returns:
            Cached or fetched value
        """
        # Check cache first (including stale if allowed)
        cached = self._get_sync(key, allow_stale=allow_stale)

        # Try to fetch fresh data
        try:
            if timeout:
                result = await asyncio.wait_for(fetcher(), timeout=timeout)
            else:
                result = await fetcher()

            # Cache fresh result
            self.set(key, result)
            return result

        except (asyncio.TimeoutError, asyncio.CancelledError):
            # Timeout - return stale if available and allowed
            if allow_stale and cached is not None:
                return cached
            raise asyncio.TimeoutError("Fetch timeout and no cached value available")

        except Exception:
            # Other error - return stale if available
            if allow_stale and cached is not None:
                return cached
            raise
