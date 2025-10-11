"""Database connection pooling for multi-database support."""

from typing import Dict, Any, Optional
import threading
import queue
import time


class ConnectionPool:
    """Connection pool for a single database."""

    def __init__(self, connection_string: str, max_connections: int = 10):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self._available = queue.Queue(maxsize=max_connections)
        self._all_connections = []
        self._active_count = 0
        self._lock = threading.Lock()

        # Initialize pool
        for _ in range(max_connections):
            conn = object()  # Mock connection
            self._available.put(conn)
            self._all_connections.append(conn)

    def get_connection(self, timeout: float = None):
        """Get connection from pool."""
        try:
            conn = self._available.get(timeout=timeout)
            with self._lock:
                self._active_count += 1
            return conn
        except queue.Empty:
            raise Exception("Connection pool exhausted")

    def release_connection(self, conn):
        """Release connection back to pool."""
        with self._lock:
            self._active_count -= 1
        self._available.put(conn)

    @property
    def active_connections(self):
        """Get count of active connections."""
        return self._active_count

    @property
    def available_connections(self):
        """Get count of available connections."""
        return self._available.qsize()


class ConnectionPoolManager:
    """Manages connection pools for multiple databases."""

    def __init__(self, auto_scale: bool = False):
        self.auto_scale = auto_scale
        self.pools: Dict[str, ConnectionPool] = {}
        self._lock = threading.Lock()

    def create_pool(self, pool_id: str, connection_string: str,
                    max_connections: int = 10, min_connections: int = None):
        """Create a connection pool."""
        with self._lock:
            if pool_id in self.pools:
                raise ValueError(f"Pool {pool_id} already exists")

            # Use min_connections if provided for auto_scale, otherwise use max_connections
            if self.auto_scale and min_connections:
                pool = ConnectionPool(connection_string, min_connections)
                pool.min_connections = min_connections
                pool.max_connections = max_connections
            else:
                pool = ConnectionPool(connection_string, max_connections)
            self.pools[pool_id] = pool

    def get_connection(self, pool_id: str, timeout: float = None):
        """Get connection from pool."""
        pool = self.pools.get(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        return pool.get_connection(timeout)

    def release_connection(self, pool_id: str, conn):
        """Release connection back to pool."""
        pool = self.pools.get(pool_id)
        if pool:
            pool.release_connection(conn)

    def get_pool_statistics(self, pool_id: str) -> Dict[str, int]:
        """Get pool statistics."""
        pool = self.pools.get(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        return {
            'total_connections': pool.max_connections,
            'active_connections': pool.active_connections,
            'available_connections': pool.available_connections
        }

    def get_pool_size(self, pool_id: str) -> int:
        """Get current pool size."""
        pool = self.pools.get(pool_id)
        if not pool:
            return 0
        return pool.max_connections
