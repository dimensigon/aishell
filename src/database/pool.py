"""Database connection pooling for multi-database support."""

from typing import Dict, Any, Optional, Union
import threading
import queue
import time
import re
from urllib.parse import urlparse, parse_qs

# Import database drivers
try:
    import psycopg2
    import psycopg2.extensions
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class ConnectionPool:
    """Connection pool for a single database with health checks."""

    def __init__(self, connection_string: str, max_connections: int = 10):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self._available = queue.Queue(maxsize=max_connections)
        self._all_connections = []
        self._active_count = 0
        self._lock = threading.Lock()
        self._health_check_interval = 30  # seconds
        self._last_health_check = time.time()

        # Parse connection string to determine database type
        self.db_type = self._parse_db_type()
        self.conn_params = self._parse_connection_string()

        # Initialize pool with real connections
        for _ in range(max_connections):
            conn = self._create_connection()
            self._available.put(conn)
            self._all_connections.append(conn)

    def _parse_db_type(self) -> str:
        """Parse database type from connection string."""
        parsed = urlparse(self.connection_string)
        scheme = parsed.scheme.lower()

        if scheme in ('postgresql', 'postgres'):
            return 'postgresql'
        elif scheme in ('mysql', 'mysql+pymysql'):
            return 'mysql'
        elif scheme in ('test', ''):
            return 'mock'  # For testing
        else:
            raise ValueError(f"Unsupported database type: {scheme}")

    def _parse_connection_string(self) -> Dict[str, Any]:
        """Parse connection string into connection parameters."""
        if self.db_type == 'mock':
            return {}

        parsed = urlparse(self.connection_string)

        params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/') if parsed.path else None
        }

        # Parse query parameters
        if parsed.query:
            query_params = parse_qs(parsed.query)
            for key, value in query_params.items():
                params[key] = value[0] if len(value) == 1 else value

        # Set default ports
        if not params['port']:
            if self.db_type == 'postgresql':
                params['port'] = 5432
            elif self.db_type == 'mysql':
                params['port'] = 3306

        # Remove None values
        return {k: v for k, v in params.items() if v is not None}

    def _create_connection(self) -> Union[object, Any]:
        """Create a real database connection based on db_type."""
        if self.db_type == 'mock':
            return object()  # Mock connection for tests

        elif self.db_type == 'postgresql':
            if not PSYCOPG2_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL connections")

            try:
                conn = psycopg2.connect(**self.conn_params)
                conn.autocommit = False
                return conn
            except Exception as e:
                raise ConnectionError(f"Failed to create PostgreSQL connection: {e}")

        elif self.db_type == 'mysql':
            if not PYMYSQL_AVAILABLE:
                raise ImportError("pymysql is required for MySQL connections")

            try:
                conn = pymysql.connect(**self.conn_params)
                return conn
            except Exception as e:
                raise ConnectionError(f"Failed to create MySQL connection: {e}")

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def _health_check(self, conn) -> bool:
        """
        Check if connection is healthy.

        Args:
            conn: Connection to check

        Returns:
            True if healthy, False otherwise
        """
        if self.db_type == 'mock':
            return True

        try:
            if self.db_type == 'postgresql':
                if not PSYCOPG2_AVAILABLE:
                    return False
                # Check if connection is closed
                if conn.closed:
                    return False
                # Execute simple query to verify connection
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True

            elif self.db_type == 'mysql':
                if not PYMYSQL_AVAILABLE:
                    return False
                # Check if connection is open
                if not conn.open:
                    return False
                # Ping the server
                conn.ping(reconnect=False)
                return True

            return False
        except Exception:
            return False

    def _reconnect(self, old_conn) -> Union[object, Any]:
        """
        Attempt to reconnect a stale connection.

        Args:
            old_conn: The stale connection to replace

        Returns:
            New connection or None if reconnection fails
        """
        try:
            # Close old connection if possible
            if self.db_type == 'postgresql' and hasattr(old_conn, 'close'):
                try:
                    old_conn.close()
                except Exception:
                    pass
            elif self.db_type == 'mysql' and hasattr(old_conn, 'close'):
                try:
                    old_conn.close()
                except Exception:
                    pass

            # Create new connection
            return self._create_connection()
        except Exception as e:
            # Log error but don't raise - we'll handle this in get_connection
            return None

    def _get_healthy_connection(self, timeout: float = None):
        """
        Get a healthy connection from pool.

        Args:
            timeout: Timeout in seconds

        Returns:
            Healthy connection

        Raises:
            Exception if pool exhausted or no healthy connection found
        """
        try:
            conn = self._available.get(timeout=timeout)

            # Perform health check if interval exceeded
            current_time = time.time()
            if current_time - self._last_health_check > self._health_check_interval:
                if not self._health_check(conn):
                    # Connection unhealthy, attempt to reconnect
                    new_conn = self._reconnect(conn)
                    if new_conn is not None:
                        # Replace in all_connections list
                        with self._lock:
                            try:
                                idx = self._all_connections.index(conn)
                                self._all_connections[idx] = new_conn
                            except ValueError:
                                # Connection not in list, just append
                                self._all_connections.append(new_conn)
                        conn = new_conn
                    else:
                        # Reconnection failed, try to create a new connection
                        try:
                            conn = self._create_connection()
                            with self._lock:
                                self._all_connections.append(conn)
                        except Exception as e:
                            raise Exception(f"Failed to get healthy connection: {e}")
                self._last_health_check = current_time

            return conn
        except queue.Empty:
            raise Exception("Connection pool exhausted")

    def get_connection(self, timeout: float = None):
        """Get healthy connection from pool."""
        conn = self._get_healthy_connection(timeout)
        with self._lock:
            self._active_count += 1
        return conn

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

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            # Close all connections
            for conn in self._all_connections:
                if self.db_type != 'mock':
                    try:
                        if hasattr(conn, 'close'):
                            conn.close()
                    except Exception:
                        pass  # Ignore errors during cleanup

            # Clear the queues
            while not self._available.empty():
                try:
                    self._available.get_nowait()
                except queue.Empty:
                    break

            self._all_connections.clear()
            self._active_count = 0


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
