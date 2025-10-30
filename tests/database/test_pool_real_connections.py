"""
Tests for real database connections in connection pool.

This test suite validates PostgreSQL and MySQL connection creation,
validation, and reconnection logic.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from src.database.pool import ConnectionPool, ConnectionPoolManager


class TestConnectionStringParsing:
    """Test connection string parsing for different database types."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_parse_postgresql_connection_string(self, mock_connect):
        """Test parsing PostgreSQL connection string."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool("postgresql://user:pass@localhost:5432/testdb")

        assert pool.db_type == 'postgresql'
        assert pool.conn_params['host'] == 'localhost'
        assert pool.conn_params['port'] == 5432
        assert pool.conn_params['user'] == 'user'
        assert pool.conn_params['password'] == 'pass'
        assert pool.conn_params['database'] == 'testdb'

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_parse_postgres_scheme(self, mock_connect):
        """Test parsing with 'postgres' scheme."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool("postgres://user:pass@db.example.com/mydb")

        assert pool.db_type == 'postgresql'
        assert pool.conn_params['host'] == 'db.example.com'
        assert pool.conn_params['database'] == 'mydb'

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_parse_postgresql_default_port(self, mock_connect):
        """Test PostgreSQL default port assignment."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool("postgresql://user:pass@localhost/testdb")

        assert pool.conn_params['port'] == 5432

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_parse_mysql_connection_string(self, mock_connect):
        """Test parsing MySQL connection string."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool("mysql://root:password@localhost:3306/mydb")

        assert pool.db_type == 'mysql'
        assert pool.conn_params['host'] == 'localhost'
        assert pool.conn_params['port'] == 3306
        assert pool.conn_params['user'] == 'root'
        assert pool.conn_params['password'] == 'password'
        assert pool.conn_params['database'] == 'mydb'

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_parse_mysql_default_port(self, mock_connect):
        """Test MySQL default port assignment."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool("mysql://root:pass@localhost/testdb")

        assert pool.conn_params['port'] == 3306

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_parse_connection_without_password(self, mock_connect):
        """Test parsing connection string without password."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool("postgresql://user@localhost/testdb")

        assert pool.conn_params['user'] == 'user'
        assert 'password' not in pool.conn_params

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_parse_connection_with_query_params(self, mock_connect):
        """Test parsing connection string with query parameters."""
        mock_connect.return_value = MagicMock()
        pool = ConnectionPool(
            "postgresql://user:pass@localhost/testdb?sslmode=require&connect_timeout=10"
        )

        assert pool.conn_params['sslmode'] == 'require'
        assert pool.conn_params['connect_timeout'] == '10'

    def test_parse_mock_connection(self):
        """Test parsing mock/test connection string."""
        pool = ConnectionPool("test://db")

        assert pool.db_type == 'mock'
        assert pool.conn_params == {}

    def test_unsupported_database_type(self):
        """Test that unsupported database types raise error."""
        with pytest.raises(ValueError, match="Unsupported database type"):
            ConnectionPool("oracle://user:pass@localhost/db")


class TestPostgreSQLConnections:
    """Test PostgreSQL connection creation and validation."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_create_postgresql_connection(self, mock_connect):
        """Test creating PostgreSQL connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

        # Verify connection was created
        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['host'] == 'localhost'
        assert call_kwargs['database'] == 'testdb'
        assert call_kwargs['user'] == 'user'

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', False)
    def test_postgresql_without_driver(self):
        """Test PostgreSQL connection without driver raises error."""
        with pytest.raises(ImportError, match="psycopg2 is required"):
            ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_postgresql_health_check_healthy(self, mock_connect):
        """Test health check for healthy PostgreSQL connection."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

        # Get connection and verify health check
        conn = pool.get_connection()
        assert pool._health_check(conn)

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_postgresql_health_check_closed(self, mock_connect):
        """Test health check for closed PostgreSQL connection."""
        mock_conn = MagicMock()
        mock_conn.closed = True
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

        # Get connection and verify health check fails
        conn = pool.get_connection()
        assert not pool._health_check(conn)

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_postgresql_health_check_exception(self, mock_connect):
        """Test health check handles exceptions."""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Connection lost")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

        conn = pool.get_connection()
        assert not pool._health_check(conn)


class TestMySQLConnections:
    """Test MySQL connection creation and validation."""

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_create_mysql_connection(self, mock_connect):
        """Test creating MySQL connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=1)

        # Verify connection was created
        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['host'] == 'localhost'
        assert call_kwargs['database'] == 'testdb'
        assert call_kwargs['user'] == 'root'

    @patch('src.database.pool.PYMYSQL_AVAILABLE', False)
    def test_mysql_without_driver(self):
        """Test MySQL connection without driver raises error."""
        with pytest.raises(ImportError, match="pymysql is required"):
            ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=1)

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_mysql_health_check_healthy(self, mock_connect):
        """Test health check for healthy MySQL connection."""
        mock_conn = MagicMock()
        mock_conn.open = True
        mock_conn.ping.return_value = None
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=1)

        # Get connection and verify health check
        conn = pool.get_connection()
        assert pool._health_check(conn)
        mock_conn.ping.assert_called_with(reconnect=False)

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_mysql_health_check_closed(self, mock_connect):
        """Test health check for closed MySQL connection."""
        mock_conn = MagicMock()
        mock_conn.open = False
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=1)

        # Get connection and verify health check fails
        conn = pool.get_connection()
        assert not pool._health_check(conn)

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_mysql_health_check_exception(self, mock_connect):
        """Test health check handles exceptions."""
        mock_conn = MagicMock()
        mock_conn.open = True
        mock_conn.ping.side_effect = Exception("Connection lost")
        mock_connect.return_value = mock_conn

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=1)

        conn = pool.get_connection()
        assert not pool._health_check(conn)


class TestConnectionReconnection:
    """Test connection reconnection logic."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_reconnect_stale_connection(self, mock_connect):
        """Test reconnecting stale connection."""
        old_conn = MagicMock()
        old_conn.closed = True
        new_conn = MagicMock()
        new_conn.closed = False

        # First call returns old conn, subsequent calls return new conn
        mock_connect.side_effect = [old_conn, new_conn]

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

        # Reconnect the old connection
        result = pool._reconnect(old_conn)

        assert result is new_conn
        old_conn.close.assert_called_once()

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_reconnect_mysql_connection(self, mock_connect):
        """Test reconnecting MySQL connection."""
        old_conn = MagicMock()
        new_conn = MagicMock()

        mock_connect.side_effect = [old_conn, new_conn]

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=1)

        # Reconnect the old connection
        result = pool._reconnect(old_conn)

        assert result is new_conn
        old_conn.close.assert_called_once()

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_reconnect_failure(self, mock_connect):
        """Test reconnection failure handling."""
        old_conn = MagicMock()

        # First call succeeds, second call fails
        mock_connect.side_effect = [old_conn, Exception("Connection failed")]

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=1)

        # Reconnect should return None on failure
        result = pool._reconnect(old_conn)

        assert result is None


class TestConnectionPoolCleanup:
    """Test connection pool cleanup."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_close_all_postgresql_connections(self, mock_connect):
        """Test closing all PostgreSQL connections."""
        mock_conns = [MagicMock() for _ in range(3)]
        mock_connect.side_effect = mock_conns

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=3)

        # Close all connections
        pool.close_all()

        # Verify all connections were closed
        for conn in mock_conns:
            conn.close.assert_called_once()

        assert len(pool._all_connections) == 0
        assert pool.active_connections == 0

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_close_all_mysql_connections(self, mock_connect):
        """Test closing all MySQL connections."""
        mock_conns = [MagicMock() for _ in range(3)]
        mock_connect.side_effect = mock_conns

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=3)

        # Close all connections
        pool.close_all()

        # Verify all connections were closed
        for conn in mock_conns:
            conn.close.assert_called_once()

        assert len(pool._all_connections) == 0
        assert pool.active_connections == 0

    def test_close_all_mock_connections(self):
        """Test closing mock connections (no-op)."""
        pool = ConnectionPool("test://db", max_connections=3)

        # Should not raise exception
        pool.close_all()

        assert len(pool._all_connections) == 0


class TestThreadSafety:
    """Test thread-safety with real connections."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_concurrent_connection_creation(self, mock_connect):
        """Test concurrent connection creation is thread-safe."""
        # Create unique mock connections
        mock_conns = [MagicMock() for _ in range(10)]
        for i, conn in enumerate(mock_conns):
            conn.id = i
            conn.closed = False
            mock_cursor = MagicMock()
            conn.cursor.return_value = mock_cursor

        mock_connect.side_effect = mock_conns

        pool = ConnectionPool("postgresql://user:pass@localhost/testdb", max_connections=5)

        results = []
        errors = []

        def get_and_release():
            try:
                conn = pool.get_connection(timeout=2.0)
                time.sleep(0.01)  # Simulate work
                pool.release_connection(conn)
                results.append("success")
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_and_release)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len(results) == 10
        assert len(errors) == 0

    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.pymysql.connect')
    def test_concurrent_mysql_operations(self, mock_connect):
        """Test concurrent MySQL operations are thread-safe."""
        mock_conns = [MagicMock() for _ in range(10)]
        for i, conn in enumerate(mock_conns):
            conn.id = i
            conn.open = True
            conn.ping.return_value = None

        mock_connect.side_effect = mock_conns

        pool = ConnectionPool("mysql://root:pass@localhost/testdb", max_connections=5)

        results = []

        def get_and_release():
            try:
                conn = pool.get_connection(timeout=2.0)
                time.sleep(0.01)
                pool.release_connection(conn)
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_and_release)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len([r for r in results if r == "success"]) == 10


class TestConnectionPoolManagerWithRealConnections:
    """Test ConnectionPoolManager with real connection types."""

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    def test_manager_multiple_database_types(self, mock_pg_connect):
        """Test manager with multiple database types."""
        mock_pg_conn = MagicMock()
        mock_pg_connect.return_value = mock_pg_conn

        manager = ConnectionPoolManager()

        # Create pools for different databases
        manager.create_pool("postgres_pool", "postgresql://user:pass@localhost/db1", max_connections=5)
        manager.create_pool("test_pool", "test://db2", max_connections=3)

        assert len(manager.pools) == 2
        assert manager.pools["postgres_pool"].db_type == 'postgresql'
        assert manager.pools["test_pool"].db_type == 'mock'

    @patch('src.database.pool.PSYCOPG2_AVAILABLE', True)
    @patch('src.database.pool.PYMYSQL_AVAILABLE', True)
    @patch('src.database.pool.psycopg2.connect')
    @patch('src.database.pool.pymysql.connect')
    def test_manager_postgres_and_mysql(self, mock_mysql_connect, mock_pg_connect):
        """Test manager with both PostgreSQL and MySQL."""
        mock_pg_conn = MagicMock()
        mock_mysql_conn = MagicMock()
        mock_pg_connect.return_value = mock_pg_conn
        mock_mysql_connect.return_value = mock_mysql_conn

        manager = ConnectionPoolManager()

        manager.create_pool("pg", "postgresql://user:pass@localhost/pgdb", max_connections=3)
        manager.create_pool("my", "mysql://root:pass@localhost/mydb", max_connections=3)

        assert manager.pools["pg"].db_type == 'postgresql'
        assert manager.pools["my"].db_type == 'mysql'
