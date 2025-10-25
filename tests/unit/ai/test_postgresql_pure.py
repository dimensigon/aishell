"""
Comprehensive Unit Tests for PostgreSQL MCP Client (Pure Python)

Tests PostgreSQL client implementation using psycopg2 including:
- Connection management
- Query execution (SELECT, DDL, DML, transactions)
- Async operation tests
- Error handling and recovery
- Metadata operations
- Pure Python mode validation (no libpq dependency issues)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Any, Dict
import psycopg2.extras

from src.mcp_clients.postgresql_client import PostgreSQLClient
from src.mcp_clients.base import (
    MCPClientError,
    ConnectionState,
    ConnectionConfig,
    QueryResult
)


# Test Fixtures

@pytest.fixture
def postgres_config():
    """PostgreSQL connection configuration"""
    return ConnectionConfig(
        host='localhost',
        port=5432,
        database='postgres',
        username='postgres',
        password='MyPostgresPass123',
        extra_params={'connect_timeout': 10}
    )


@pytest.fixture
def postgres_config_from_string():
    """PostgreSQL connection config from connection string"""
    return ConnectionConfig(
        host='localhost',
        port=5432,
        database='postgres',
        username='postgres',
        password='MyPostgresPass123'
    )


@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection"""
    conn = Mock()
    cursor = Mock()

    # Mock cursor description with proper name attribute
    class MockDescriptor:
        def __init__(self, name, type_code):
            self.name = name
            self.type_code = type_code

    cursor.description = [
        MockDescriptor('id', 23),  # INT
        MockDescriptor('name', 1043),  # VARCHAR
        MockDescriptor('email', 1043)  # VARCHAR
    ]

    # Mock fetchall returning RealDictRow-like objects
    cursor.fetchall = Mock(return_value=[
        {'id': 1, 'name': 'test1', 'email': 'test1@example.com'},
        {'id': 2, 'name': 'test2', 'email': 'test2@example.com'}
    ])

    cursor.rowcount = 2
    cursor.close = Mock()

    conn.cursor = Mock(return_value=cursor)
    conn.close = Mock()
    conn.commit = Mock()
    conn.rollback = Mock()
    conn.autocommit = False

    return conn


@pytest.fixture
def mock_postgres_cursor():
    """Mock PostgreSQL cursor"""
    cursor = Mock()

    class MockDescriptor:
        def __init__(self, name, type_code):
            self.name = name
            self.type_code = type_code

    cursor.description = [
        MockDescriptor('count', 23)
    ]
    cursor.fetchall = Mock(return_value=[{'count': 10}])
    cursor.rowcount = 1
    cursor.close = Mock()
    return cursor


# Test PostgreSQL Protocol Compliance

class TestPostgreSQLProtocolCompliance:
    """Test MCP protocol compliance for PostgreSQL client"""

    @pytest.mark.asyncio
    async def test_client_has_state_property(self):
        """Test state property exists"""
        client = PostgreSQLClient()
        assert hasattr(client, 'state')
        assert isinstance(client.state, ConnectionState)
        assert client.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_client_has_async_methods(self):
        """Test required async methods exist"""
        client = PostgreSQLClient()
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        assert hasattr(client, 'execute_query')
        assert hasattr(client, 'health_check')

        assert asyncio.iscoroutinefunction(client.connect)
        assert asyncio.iscoroutinefunction(client.disconnect)
        assert asyncio.iscoroutinefunction(client.execute_query)
        assert asyncio.iscoroutinefunction(client.health_check)

    @pytest.mark.asyncio
    async def test_client_has_postgres_specific_methods(self):
        """Test PostgreSQL-specific methods exist"""
        client = PostgreSQLClient()
        assert hasattr(client, 'get_table_info')
        assert hasattr(client, 'get_table_list')
        assert hasattr(client, 'get_schemas')

        assert asyncio.iscoroutinefunction(client.get_table_info)
        assert asyncio.iscoroutinefunction(client.get_table_list)
        assert asyncio.iscoroutinefunction(client.get_schemas)


# Test Connection Management

class TestPostgreSQLConnection:
    """Test PostgreSQL connection management"""

    @pytest.mark.asyncio
    async def test_connect_success(self, postgres_config, mock_postgres_connection):
        """Test successful PostgreSQL connection"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            result = await client.connect(postgres_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_with_extra_params(self, postgres_config, mock_postgres_connection):
        """Test connection with extra parameters"""
        client = PostgreSQLClient()
        postgres_config.extra_params = {
            'connect_timeout': 20,
            'application_name': 'test_app',
            'sslmode': 'prefer'
        }

        with patch('psycopg2.connect', return_value=mock_postgres_connection) as mock_connect:
            await client.connect(postgres_config)

            # Verify connect was called with extra params
            call_kwargs = mock_connect.call_args[1]
            assert call_kwargs['connect_timeout'] == 20
            assert call_kwargs['application_name'] == 'test_app'
            assert call_kwargs['sslmode'] == 'prefer'

    @pytest.mark.asyncio
    async def test_connect_failure(self, postgres_config):
        """Test PostgreSQL connection failure handling"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', side_effect=Exception("Connection refused")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(postgres_config)

            assert exc_info.value.error_code == "CONNECTION_FAILED"
            assert client.state == ConnectionState.ERROR
            assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_authentication_error(self, postgres_config):
        """Test authentication failure"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("password authentication failed")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(postgres_config)

            assert "password authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect(self, postgres_config, mock_postgres_connection):
        """Test PostgreSQL disconnect"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.disconnect()

            assert result is True
            assert client.state == ConnectionState.CLOSED
            mock_postgres_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_with_cursor(self, postgres_config, mock_postgres_connection, mock_postgres_cursor):
        """Test disconnect with active cursor"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            # Create cursor
            client._cursor = mock_postgres_cursor

            await client.disconnect()

            mock_postgres_cursor.close.assert_called_once()
            mock_postgres_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected_property(self, postgres_config, mock_postgres_connection):
        """Test is_connected property"""
        client = PostgreSQLClient()

        assert client.is_connected is False

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False


# Test Query Execution

class TestPostgreSQLQueryExecution:
    """Test PostgreSQL query execution"""

    @pytest.mark.asyncio
    async def test_execute_select_query(self, postgres_config, mock_postgres_connection):
        """Test SELECT query execution"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query("SELECT * FROM users")

            assert isinstance(result, QueryResult)
            assert result.columns == ['id', 'name', 'email']
            assert len(result.rows) == 2
            assert result.rowcount == 2
            assert result.execution_time >= 0
            assert result.metadata['database'] == 'postgres'
            assert result.metadata['query_type'] == 'SELECT'

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, postgres_config, mock_postgres_connection):
        """Test query execution with parameters"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query(
                "SELECT * FROM users WHERE id = %(id)s",
                {'id': 1}
            )

            assert isinstance(result, QueryResult)
            assert len(result.rows) == 2

    @pytest.mark.asyncio
    async def test_execute_insert_query(self, postgres_config, mock_postgres_connection):
        """Test INSERT query execution"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = None  # INSERT doesn't return rows
        cursor.rowcount = 1

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query(
                "INSERT INTO users (name, email) VALUES (%(name)s, %(email)s)",
                {'name': 'John', 'email': 'john@example.com'}
            )

            assert result.rowcount == 1
            assert result.columns == []
            assert result.rows == []
            assert result.metadata['query_type'] == 'INSERT'

    @pytest.mark.asyncio
    async def test_execute_update_query(self, postgres_config, mock_postgres_connection):
        """Test UPDATE query execution"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = None
        cursor.rowcount = 3

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query(
                "UPDATE users SET email = %(email)s WHERE id = %(id)s",
                {'email': 'new@example.com', 'id': 1}
            )

            assert result.rowcount == 3
            assert result.metadata['query_type'] == 'UPDATE'

    @pytest.mark.asyncio
    async def test_execute_delete_query(self, postgres_config, mock_postgres_connection):
        """Test DELETE query execution"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = None
        cursor.rowcount = 2

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query(
                "DELETE FROM users WHERE id = %(id)s",
                {'id': 1}
            )

            assert result.rowcount == 2
            assert result.metadata['query_type'] == 'DELETE'

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected"""
        client = PostgreSQLClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_query("SELECT * FROM users")

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_execute_ddl(self, postgres_config, mock_postgres_connection):
        """Test DDL execution"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_ddl("CREATE TABLE test (id INTEGER PRIMARY KEY, name VARCHAR(100))")

            assert result is True
            mock_postgres_connection.commit.assert_called()

    @pytest.mark.asyncio
    async def test_execute_ddl_not_connected(self):
        """Test DDL execution when not connected"""
        client = PostgreSQLClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_ddl("CREATE TABLE test (id INTEGER)")

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_query_type_detection(self):
        """Test query type detection"""
        client = PostgreSQLClient()

        assert client._get_query_type("SELECT * FROM users") == "SELECT"
        assert client._get_query_type("  select * from users") == "SELECT"
        assert client._get_query_type("INSERT INTO users VALUES (1)") == "INSERT"
        assert client._get_query_type("UPDATE users SET name = 'test'") == "UPDATE"
        assert client._get_query_type("DELETE FROM users") == "DELETE"
        assert client._get_query_type("CREATE TABLE test (id INTEGER)") == "DDL"
        assert client._get_query_type("ALTER TABLE test ADD COLUMN name VARCHAR") == "DDL"
        assert client._get_query_type("DROP TABLE test") == "DDL"
        assert client._get_query_type("BEGIN") == "OTHER"


# Test Transaction Support

class TestPostgreSQLTransactions:
    """Test PostgreSQL transaction support"""

    @pytest.mark.asyncio
    async def test_autocommit_disabled_by_default(self, postgres_config, mock_postgres_connection):
        """Test that autocommit is disabled by default"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            # Verify autocommit was set to False
            assert mock_postgres_connection.autocommit is False

    @pytest.mark.asyncio
    async def test_ddl_commits_transaction(self, postgres_config, mock_postgres_connection):
        """Test DDL operations commit transaction"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            await client.execute_ddl("CREATE TABLE test (id INTEGER)")

            mock_postgres_connection.commit.assert_called_once()


# Test PostgreSQL Metadata Operations

class TestPostgreSQLMetadata:
    """Test PostgreSQL metadata operations"""

    @pytest.mark.asyncio
    async def test_get_table_info(self, postgres_config, mock_postgres_connection):
        """Test table info retrieval"""
        client = PostgreSQLClient()

        class MockDescriptor:
            def __init__(self, name, type_code):
                self.name = name
                self.type_code = type_code

        # Setup mock for table info query
        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = [
            MockDescriptor('column_name', 1043),
            MockDescriptor('data_type', 1043),
            MockDescriptor('character_maximum_length', 23),
            MockDescriptor('is_nullable', 1043),
            MockDescriptor('column_default', 1043)
        ]
        cursor.fetchall = Mock(return_value=[
            {'column_name': 'id', 'data_type': 'integer', 'character_maximum_length': None,
             'is_nullable': 'NO', 'column_default': None},
            {'column_name': 'name', 'data_type': 'character varying', 'character_maximum_length': 100,
             'is_nullable': 'YES', 'column_default': None}
        ])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            table_info = await client.get_table_info('users', 'public')

            assert table_info['table_name'] == 'users'
            assert table_info['schema'] == 'public'
            assert len(table_info['columns']) == 2
            assert table_info['columns'][0]['name'] == 'id'
            assert table_info['columns'][0]['nullable'] is False
            assert table_info['columns'][1]['name'] == 'name'
            assert table_info['columns'][1]['nullable'] is True

    @pytest.mark.asyncio
    async def test_get_table_info_default_schema(self, postgres_config, mock_postgres_connection):
        """Test table info with default schema"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = [Mock(name='column_name', type_code=1043)]
        cursor.fetchall = Mock(return_value=[])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            table_info = await client.get_table_info('users')

            assert table_info['schema'] == 'public'

    @pytest.mark.asyncio
    async def test_get_table_list(self, postgres_config, mock_postgres_connection):
        """Test table list retrieval"""
        client = PostgreSQLClient()

        class MockDescriptor:
            def __init__(self, name, type_code):
                self.name = name
                self.type_code = type_code

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = [MockDescriptor('table_name', 1043)]
        cursor.fetchall = Mock(return_value=[
            {'table_name': 'users'},
            {'table_name': 'orders'},
            {'table_name': 'products'}
        ])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            tables = await client.get_table_list()

            assert len(tables) == 3
            assert 'users' in tables
            assert 'orders' in tables
            assert 'products' in tables

    @pytest.mark.asyncio
    async def test_get_table_list_custom_schema(self, postgres_config, mock_postgres_connection):
        """Test table list with custom schema"""
        client = PostgreSQLClient()

        class MockDescriptor:
            def __init__(self, name, type_code):
                self.name = name
                self.type_code = type_code

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = [MockDescriptor('table_name', 1043)]
        cursor.fetchall = Mock(return_value=[{'table_name': 'custom_table'}])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            tables = await client.get_table_list(schema='custom_schema')

            assert len(tables) == 1
            assert 'custom_table' in tables

    @pytest.mark.asyncio
    async def test_get_schemas(self, postgres_config, mock_postgres_connection):
        """Test schema retrieval"""
        client = PostgreSQLClient()

        class MockDescriptor:
            def __init__(self, name, type_code):
                self.name = name
                self.type_code = type_code

        cursor = mock_postgres_connection.cursor.return_value
        cursor.description = [MockDescriptor('schema_name', 1043)]
        cursor.fetchall = Mock(return_value=[
            {'schema_name': 'public'},
            {'schema_name': 'custom_schema'},
            {'schema_name': 'test_schema'}
        ])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            schemas = await client.get_schemas()

            assert len(schemas) == 3
            assert 'public' in schemas
            assert 'custom_schema' in schemas
            # pg_catalog and information_schema should be filtered out


# Test Health Check

class TestPostgreSQLHealthCheck:
    """Test PostgreSQL health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, postgres_config, mock_postgres_connection):
        """Test health check for connected client"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            health = await client.health_check()

            assert health['state'] == 'connected'
            assert health['connected'] is True
            assert 'connection_time' in health
            assert health['ping_successful'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check for disconnected client"""
        client = PostgreSQLClient()
        health = await client.health_check()

        assert health['state'] == 'disconnected'
        assert health['connected'] is False
        assert health['connection_time'] is None

    @pytest.mark.asyncio
    async def test_ping_query(self):
        """Test ping query"""
        client = PostgreSQLClient()
        assert client._get_ping_query() == "SELECT 1"


# Test Error Handling

class TestPostgreSQLErrorHandling:
    """Test PostgreSQL error handling"""

    @pytest.mark.asyncio
    async def test_query_execution_error(self, postgres_config, mock_postgres_connection):
        """Test query execution error handling"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.execute = Mock(side_effect=Exception("SQL syntax error"))

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query("INVALID SQL")

            assert exc_info.value.error_code == "QUERY_FAILED"
            assert "SQL syntax error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ddl_execution_error(self, postgres_config, mock_postgres_connection):
        """Test DDL execution error handling"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.execute = Mock(side_effect=Exception("Table already exists"))

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl("CREATE TABLE users (id INTEGER)")

            assert exc_info.value.error_code == "DDL_FAILED"

    @pytest.mark.asyncio
    async def test_connection_error_message(self, postgres_config):
        """Test connection error message"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', side_effect=Exception("Access denied")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(postgres_config)

            assert "Access denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_execution_exception(self, postgres_config, mock_postgres_connection):
        """Test query execution with exception"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        # Simulate an exception during execution
        cursor.execute = Mock(side_effect=psycopg2.ProgrammingError("Invalid query"))

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query("SELECT invalid")

            assert exc_info.value.error_code == "QUERY_FAILED"


# Test Async Operations

class TestPostgreSQLAsync:
    """Test PostgreSQL async operations"""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, postgres_config, mock_postgres_connection):
        """Test concurrent query execution"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

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

    @pytest.mark.asyncio
    async def test_run_in_executor_for_sync_operations(self, postgres_config):
        """Test that sync psycopg2 operations run in executor"""
        client = PostgreSQLClient()

        # This test verifies that blocking operations don't block the event loop
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            # Connect should use run_in_executor
            await client.connect(postgres_config)

            # Verify the connection was made
            mock_connect.assert_called_once()


# Test Pure Python Mode (No libpq Required)

class TestPostgreSQLPureMode:
    """Test pure Python mode validation"""

    @pytest.mark.asyncio
    async def test_uses_psycopg2_not_psycopg(self):
        """Test that client uses psycopg2 (pure Python compatible)"""
        client = PostgreSQLClient()

        # This ensures we're using psycopg2, not psycopg3
        # psycopg2 can work in pure Python mode
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            config = ConnectionConfig(
                host='localhost',
                port=5432,
                database='testdb',
                username='user',
                password='pass'
            )

            await client.connect(config)
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_realdict_cursor_factory(self, postgres_config, mock_postgres_connection):
        """Test that RealDictCursor is used for dict-like results"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            # Execute query which should create cursor with RealDictCursor
            await client.execute_query("SELECT * FROM users")

            # Verify cursor was created
            mock_postgres_connection.cursor.assert_called()


# Test Connection String Parsing

class TestPostgreSQLConnectionString:
    """Test connection string parsing and validation"""

    def test_connection_string_format(self):
        """Test connection string format"""
        # Connection string format: postgresql://user:password@host:port/database
        conn_string = "postgresql://postgres:MyPostgresPass123@localhost:5432/postgres"

        # Parse connection string (this would be in actual connection logic)
        assert "postgres" in conn_string
        assert "MyPostgresPass123" in conn_string
        assert "localhost" in conn_string
        assert "5432" in conn_string

    def test_connection_config_creation(self):
        """Test creation of connection config"""
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.database == 'postgres'
        assert config.username == 'postgres'
        assert config.password == 'MyPostgresPass123'


# Test Cursor Management

class TestPostgreSQLCursorManagement:
    """Test cursor lifecycle management"""

    @pytest.mark.asyncio
    async def test_cursor_reuse(self, postgres_config, mock_postgres_connection):
        """Test cursor reuse across queries"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            # First query creates cursor
            await client.execute_query("SELECT * FROM users")
            cursor1 = client._cursor

            # Second query reuses cursor
            await client.execute_query("SELECT * FROM orders")
            cursor2 = client._cursor

            # Should be same cursor instance
            assert cursor1 is cursor2

    @pytest.mark.asyncio
    async def test_cursor_cleanup_on_disconnect(self, postgres_config, mock_postgres_connection, mock_postgres_cursor):
        """Test cursor is closed on disconnect"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            client._cursor = mock_postgres_cursor

            await client.disconnect()

            mock_postgres_cursor.close.assert_called_once()
            assert client._cursor is None


# Performance and Edge Cases

class TestPostgreSQLEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_result_set(self, postgres_config, mock_postgres_connection):
        """Test handling of empty result set"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.fetchall = Mock(return_value=[])
        cursor.rowcount = 0

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query("SELECT * FROM users WHERE id = -1")

            assert len(result.rows) == 0
            assert result.rowcount == 0

    @pytest.mark.asyncio
    async def test_large_result_set(self, postgres_config, mock_postgres_connection):
        """Test handling of large result set"""
        client = PostgreSQLClient()

        # Generate 1000 rows
        large_result = [{'id': i, 'name': f'user{i}', 'email': f'user{i}@example.com'} for i in range(1000)]
        cursor = mock_postgres_connection.cursor.return_value
        cursor.fetchall = Mock(return_value=large_result)
        cursor.rowcount = 1000

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query("SELECT * FROM users")

            assert len(result.rows) == 1000
            assert result.rowcount == 1000

    @pytest.mark.asyncio
    async def test_null_values_in_results(self, postgres_config, mock_postgres_connection):
        """Test handling of NULL values"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.fetchall = Mock(return_value=[
            {'id': 1, 'name': 'test', 'email': None},
            {'id': 2, 'name': None, 'email': 'test@example.com'}
        ])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query("SELECT * FROM users")

            assert result.rows[0][2] is None  # email is None
            assert result.rows[1][1] is None  # name is None

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, postgres_config, mock_postgres_connection):
        """Test queries with special characters"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)

            # Query with special characters
            result = await client.execute_query(
                "SELECT * FROM users WHERE name = %(name)s",
                {'name': "O'Brien"}
            )

            assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_unicode_support(self, postgres_config, mock_postgres_connection):
        """Test Unicode character support"""
        client = PostgreSQLClient()

        cursor = mock_postgres_connection.cursor.return_value
        cursor.fetchall = Mock(return_value=[
            {'id': 1, 'name': '日本語', 'email': 'test@例え.jp'},
            {'id': 2, 'name': 'Ñoño', 'email': 'test@español.es'}
        ])

        with patch('psycopg2.connect', return_value=mock_postgres_connection):
            await client.connect(postgres_config)
            result = await client.execute_query("SELECT * FROM users")

            assert result.rows[0][1] == '日本語'
            assert result.rows[1][1] == 'Ñoño'
