"""
Comprehensive Unit Tests for MySQL MCP Client

Tests MySQL client implementation including connection management,
query execution, connection pooling, and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Any, Dict

from src.mcp_clients.mysql_client import MySQLClient
from src.mcp_clients.base import (
    MCPClientError,
    ConnectionState,
    ConnectionConfig,
    QueryResult
)


# Test Fixtures

@pytest.fixture
def mysql_config():
    """MySQL connection configuration"""
    return ConnectionConfig(
        host='localhost',
        port=3307,
        database='testdb',
        username='testuser',
        password='testpass',
        extra_params={'charset': 'utf8mb4'}
    )


@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection"""
    conn = AsyncMock()
    cursor = AsyncMock()

    # Mock cursor description
    cursor.description = [
        ('id', 'INT'),
        ('name', 'VARCHAR'),
        ('email', 'VARCHAR')
    ]

    cursor.fetchall = AsyncMock(return_value=[
        {'id': 1, 'name': 'test1', 'email': 'test1@example.com'},
        {'id': 2, 'name': 'test2', 'email': 'test2@example.com'}
    ])

    cursor.rowcount = 2
    cursor.close = AsyncMock()

    conn.cursor = AsyncMock(return_value=cursor)
    conn.close = Mock()

    return conn


@pytest.fixture
def mock_mysql_pool():
    """Mock MySQL connection pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    cursor = AsyncMock()

    cursor.description = [('count', 'INT')]
    cursor.fetchall = AsyncMock(return_value=[{'count': 10}])
    cursor.rowcount = 1
    cursor.close = AsyncMock()

    conn.cursor = AsyncMock(return_value=cursor)
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock()

    pool.acquire = Mock(return_value=conn)
    pool.close = Mock()
    pool.wait_closed = AsyncMock()

    return pool


# Test MySQL Protocol Compliance

class TestMySQLProtocolCompliance:
    """Test MCP protocol compliance for MySQL client"""

    @pytest.mark.asyncio
    async def test_client_has_state_property(self):
        """Test state property exists"""
        client = MySQLClient()
        assert hasattr(client, 'state')
        assert isinstance(client.state, ConnectionState)
        assert client.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_client_has_async_methods(self):
        """Test required async methods exist"""
        client = MySQLClient()
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        assert hasattr(client, 'execute_query')
        assert hasattr(client, 'health_check')

        assert asyncio.iscoroutinefunction(client.connect)
        assert asyncio.iscoroutinefunction(client.disconnect)
        assert asyncio.iscoroutinefunction(client.execute_query)
        assert asyncio.iscoroutinefunction(client.health_check)


# Test Connection Management

class TestMySQLConnection:
    """Test MySQL connection management"""

    @pytest.mark.asyncio
    async def test_connect_success(self, mysql_config, mock_mysql_connection):
        """Test successful MySQL connection"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            result = await client.connect(mysql_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_failure(self, mysql_config):
        """Test MySQL connection failure handling"""
        client = MySQLClient()

        with patch('aiomysql.connect', side_effect=Exception("Connection refused")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(mysql_config)

            assert exc_info.value.error_code == "CONNECTION_FAILED"
            assert client.state == ConnectionState.ERROR
            assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect(self, mysql_config, mock_mysql_connection):
        """Test MySQL disconnect"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            result = await client.disconnect()

            assert result is True
            assert client.state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_is_connected_property(self, mysql_config, mock_mysql_connection):
        """Test is_connected property"""
        client = MySQLClient()

        assert client.is_connected is False

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False


# Test Query Execution

class TestMySQLQueryExecution:
    """Test MySQL query execution"""

    @pytest.mark.asyncio
    async def test_execute_select_query(self, mysql_config, mock_mysql_connection):
        """Test SELECT query execution"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            result = await client.execute_query("SELECT * FROM users")

            assert isinstance(result, QueryResult)
            assert result.columns == ['id', 'name', 'email']
            assert len(result.rows) == 2
            assert result.rowcount == 2
            assert result.execution_time >= 0
            assert result.metadata['database'] == 'testdb'
            assert result.metadata['query_type'] == 'SELECT'

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, mysql_config, mock_mysql_connection):
        """Test query execution with parameters"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            result = await client.execute_query(
                "SELECT * FROM users WHERE id = %s",
                {'id': 1}
            )

            assert isinstance(result, QueryResult)
            assert len(result.rows) == 2

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected"""
        client = MySQLClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_query("SELECT * FROM users")

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_execute_ddl(self, mysql_config, mock_mysql_connection):
        """Test DDL execution"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            result = await client.execute_ddl("CREATE TABLE test (id INT)")

            assert result is True

    @pytest.mark.asyncio
    async def test_query_type_detection(self, mysql_config, mock_mysql_connection):
        """Test query type detection"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)

            # Override description for non-SELECT queries
            cursor = await mock_mysql_connection.cursor.return_value
            cursor.description = None

            assert client._get_query_type("SELECT * FROM users") == "SELECT"
            assert client._get_query_type("INSERT INTO users VALUES (1)") == "INSERT"
            assert client._get_query_type("UPDATE users SET name = 'test'") == "UPDATE"
            assert client._get_query_type("DELETE FROM users") == "DELETE"
            assert client._get_query_type("CREATE TABLE test (id INT)") == "DDL"


# Test Connection Pooling

class TestMySQLConnectionPool:
    """Test MySQL connection pooling"""

    @pytest.mark.asyncio
    async def test_create_pool(self, mysql_config, mock_mysql_pool):
        """Test connection pool creation"""
        client = MySQLClient()

        with patch('aiomysql.create_pool', return_value=mock_mysql_pool):
            await client.create_pool(mysql_config, pool_size=10)

            assert client._pool is not None

    @pytest.mark.asyncio
    async def test_execute_with_pool(self, mysql_config, mock_mysql_pool):
        """Test query execution with connection pool"""
        client = MySQLClient()
        client._config = mysql_config

        with patch('aiomysql.create_pool', return_value=mock_mysql_pool):
            await client.create_pool(mysql_config, pool_size=10)
            result = await client.execute_with_pool("SELECT COUNT(*) FROM users")

            assert result['columns'] == ['count']
            assert len(result['rows']) == 1
            assert result['rowcount'] == 1

    @pytest.mark.asyncio
    async def test_execute_with_pool_not_initialized(self):
        """Test pool execution when pool not initialized"""
        client = MySQLClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_with_pool("SELECT * FROM users")

        assert exc_info.value.error_code == "NO_POOL"

    @pytest.mark.asyncio
    async def test_pool_cleanup_on_disconnect(self, mysql_config, mock_mysql_pool):
        """Test pool cleanup on disconnect"""
        client = MySQLClient()

        with patch('aiomysql.create_pool', return_value=mock_mysql_pool):
            await client.create_pool(mysql_config)
            await client.disconnect()

            mock_mysql_pool.close.assert_called_once()
            mock_mysql_pool.wait_closed.assert_called_once()


# Test MySQL Metadata Operations

class TestMySQLMetadata:
    """Test MySQL metadata operations"""

    @pytest.mark.asyncio
    async def test_get_table_info(self, mysql_config, mock_mysql_connection):
        """Test table info retrieval"""
        client = MySQLClient()

        # Setup mock for table info query
        cursor = mock_mysql_connection.cursor.return_value
        cursor.description = [
            ('COLUMN_NAME', 'VARCHAR'),
            ('DATA_TYPE', 'VARCHAR'),
            ('CHARACTER_MAXIMUM_LENGTH', 'INT'),
            ('IS_NULLABLE', 'VARCHAR'),
            ('COLUMN_DEFAULT', 'VARCHAR'),
            ('COLUMN_KEY', 'VARCHAR')
        ]
        cursor.fetchall = AsyncMock(return_value=[
            {'COLUMN_NAME': 'id', 'DATA_TYPE': 'int', 'CHARACTER_MAXIMUM_LENGTH': None,
             'IS_NULLABLE': 'NO', 'COLUMN_DEFAULT': None, 'COLUMN_KEY': 'PRI'},
            {'COLUMN_NAME': 'name', 'DATA_TYPE': 'varchar', 'CHARACTER_MAXIMUM_LENGTH': 100,
             'IS_NULLABLE': 'YES', 'COLUMN_DEFAULT': None, 'COLUMN_KEY': ''}
        ])

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            table_info = await client.get_table_info('users')

            assert table_info['table_name'] == 'users'
            assert len(table_info['columns']) == 2
            assert table_info['columns'][0]['name'] == 'id'
            assert table_info['columns'][0]['nullable'] is False
            assert table_info['columns'][0]['key'] == 'PRI'

    @pytest.mark.asyncio
    async def test_get_table_list(self, mysql_config, mock_mysql_connection):
        """Test table list retrieval"""
        client = MySQLClient()

        cursor = mock_mysql_connection.cursor.return_value
        cursor.description = [('TABLE_NAME', 'VARCHAR')]
        cursor.fetchall = AsyncMock(return_value=[
            {'TABLE_NAME': 'users'},
            {'TABLE_NAME': 'orders'},
            {'TABLE_NAME': 'products'}
        ])

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            tables = await client.get_table_list()

            assert len(tables) == 3
            assert 'users' in tables
            assert 'orders' in tables
            assert 'products' in tables

    @pytest.mark.asyncio
    async def test_get_schemas(self, mysql_config, mock_mysql_connection):
        """Test schema retrieval"""
        client = MySQLClient()

        cursor = mock_mysql_connection.cursor.return_value
        cursor.description = [('SCHEMA_NAME', 'VARCHAR')]
        cursor.fetchall = AsyncMock(return_value=[
            {'SCHEMA_NAME': 'testdb'},
            {'SCHEMA_NAME': 'production'}
        ])

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            schemas = await client.get_schemas()

            assert len(schemas) == 2
            assert 'testdb' in schemas
            assert 'production' in schemas


# Test Health Check

class TestMySQLHealthCheck:
    """Test MySQL health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, mysql_config, mock_mysql_connection):
        """Test health check for connected client"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)
            health = await client.health_check()

            assert health['state'] == 'connected'
            assert health['connected'] is True
            assert 'connection_time' in health
            assert health['ping_successful'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check for disconnected client"""
        client = MySQLClient()
        health = await client.health_check()

        assert health['state'] == 'disconnected'
        assert health['connected'] is False
        assert health['connection_time'] is None


# Test Error Handling

class TestMySQLErrorHandling:
    """Test MySQL error handling"""

    @pytest.mark.asyncio
    async def test_query_execution_error(self, mysql_config, mock_mysql_connection):
        """Test query execution error handling"""
        client = MySQLClient()

        cursor = mock_mysql_connection.cursor.return_value
        cursor.execute = AsyncMock(side_effect=Exception("SQL syntax error"))

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query("INVALID SQL")

            assert exc_info.value.error_code == "QUERY_FAILED"
            assert "SQL syntax error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ddl_execution_error(self, mysql_config, mock_mysql_connection):
        """Test DDL execution error handling"""
        client = MySQLClient()

        cursor = mock_mysql_connection.cursor.return_value
        cursor.execute = AsyncMock(side_effect=Exception("Table already exists"))

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl("CREATE TABLE users (id INT)")

            assert exc_info.value.error_code == "DDL_FAILED"

    @pytest.mark.asyncio
    async def test_connection_error_message(self, mysql_config):
        """Test connection error message"""
        client = MySQLClient()

        with patch('aiomysql.connect', side_effect=Exception("Access denied")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(mysql_config)

            assert "Access denied" in str(exc_info.value)


# Test Concurrent Operations

class TestMySQLConcurrent:
    """Test concurrent MySQL operations"""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mysql_config, mock_mysql_connection):
        """Test concurrent query execution"""
        client = MySQLClient()

        with patch('aiomysql.connect', return_value=mock_mysql_connection):
            await client.connect(mysql_config)

            # Execute multiple queries concurrently
            tasks = [
                client.execute_query("SELECT * FROM users"),
                client.execute_query("SELECT * FROM orders"),
                client.execute_query("SELECT * FROM products")
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            for result in results:
                assert isinstance(result, QueryResult)
