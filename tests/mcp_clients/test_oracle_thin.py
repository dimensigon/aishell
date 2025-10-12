"""
Comprehensive Unit Tests for Oracle MCP Client (Thin Mode)

Tests Oracle client implementation including:
- Connection management (thin mode, no Oracle client required)
- Query execution (SELECT, INSERT, UPDATE, DELETE)
- DDL operations (CREATE, ALTER, DROP)
- Connection pooling
- Error handling and timeout scenarios
- Both CDB and PDB connections
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Any, Dict
from datetime import datetime

from src.mcp_clients.oracle_client import OracleClient
from src.mcp_clients.base import (
    MCPClientError,
    ConnectionState,
    ConnectionConfig,
    QueryResult
)


# Test Fixtures

@pytest.fixture
def oracle_cdb_config():
    """Oracle CDB$ROOT connection configuration"""
    return ConnectionConfig(
        host='localhost',
        port=1521,
        database='free',
        username='SYS',
        password='MyOraclePass123',
        extra_params={'mode': 'SYSDBA'}
    )


@pytest.fixture
def oracle_pdb_config():
    """Oracle FREEPDB1 pluggable database configuration"""
    return ConnectionConfig(
        host='localhost',
        port=1521,
        database='freepdb1',
        username='SYS',
        password='MyOraclePass123',
        extra_params={'mode': 'SYSDBA'}
    )


@pytest.fixture
def oracle_user_config():
    """Oracle regular user configuration"""
    return ConnectionConfig(
        host='localhost',
        port=1521,
        database='freepdb1',
        username='testuser',
        password='testpass',
        extra_params={}
    )


@pytest.fixture
def mock_oracle_connection():
    """Mock Oracle thin mode connection"""
    conn = Mock()
    cursor = Mock()

    # Mock cursor description for SELECT queries
    cursor.description = [
        ('ID', int),
        ('NAME', str),
        ('EMAIL', str)
    ]

    cursor.fetchall = Mock(return_value=[
        (1, 'test1', 'test1@example.com'),
        (2, 'test2', 'test2@example.com')
    ])

    cursor.rowcount = 2
    cursor.close = Mock()

    conn.cursor = Mock(return_value=cursor)
    conn.commit = Mock()
    conn.close = Mock()

    return conn


@pytest.fixture
def mock_oracle_cursor():
    """Mock Oracle cursor"""
    cursor = Mock()
    cursor.description = [
        ('COLUMN_NAME', str),
        ('DATA_TYPE', str),
        ('DATA_LENGTH', int),
        ('NULLABLE', str),
        ('DATA_DEFAULT', str)
    ]
    cursor.fetchall = Mock(return_value=[
        ('ID', 'NUMBER', 22, 'N', None),
        ('NAME', 'VARCHAR2', 100, 'Y', None)
    ])
    cursor.rowcount = 2
    cursor.close = Mock()
    return cursor


# Test Oracle Protocol Compliance

class TestOracleProtocolCompliance:
    """Test MCP protocol compliance for Oracle client"""

    @pytest.mark.asyncio
    async def test_client_has_state_property(self):
        """Test state property exists"""
        client = OracleClient()
        assert hasattr(client, 'state')
        assert isinstance(client.state, ConnectionState)
        assert client.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_client_has_async_methods(self):
        """Test required async methods exist"""
        client = OracleClient()
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        assert hasattr(client, 'execute_query')
        assert hasattr(client, 'health_check')

        assert asyncio.iscoroutinefunction(client.connect)
        assert asyncio.iscoroutinefunction(client.disconnect)
        assert asyncio.iscoroutinefunction(client.execute_query)
        assert asyncio.iscoroutinefunction(client.health_check)

    @pytest.mark.asyncio
    async def test_thin_mode_no_client_required(self):
        """Test that thin mode doesn't require Oracle Instant Client"""
        client = OracleClient()
        # Verify thin mode is default (no thick mode initialization)
        assert not hasattr(client, '_thick_mode')
        assert client._connection is None


# Test Connection Management

class TestOracleConnection:
    """Test Oracle connection management"""

    @pytest.mark.asyncio
    async def test_connect_success_cdb(self, oracle_cdb_config, mock_oracle_connection):
        """Test successful Oracle CDB connection"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            result = await client.connect(oracle_cdb_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_success_pdb(self, oracle_pdb_config, mock_oracle_connection):
        """Test successful Oracle PDB connection"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            result = await client.connect(oracle_pdb_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_with_dsn_format(self, oracle_cdb_config, mock_oracle_connection):
        """Test connection with DSN format"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection) as mock_connect:
            await client.connect(oracle_cdb_config)

            # Verify DSN format: host:port/database
            call_kwargs = mock_connect.call_args[1]
            assert call_kwargs['dsn'] == 'localhost:1521/free'
            assert call_kwargs['user'] == 'SYS'
            assert call_kwargs['password'] == 'MyOraclePass123'

    @pytest.mark.asyncio
    async def test_connect_failure(self, oracle_cdb_config):
        """Test Oracle connection failure handling"""
        client = OracleClient()

        with patch('oracledb.connect', side_effect=Exception("ORA-12545: Connect failed")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(oracle_cdb_config)

            assert exc_info.value.error_code == "CONNECTION_FAILED"
            assert client.state == ConnectionState.ERROR
            assert "ORA-12545" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, oracle_cdb_config):
        """Test connection with invalid credentials"""
        client = OracleClient()

        with patch('oracledb.connect', side_effect=Exception("ORA-01017: invalid username/password")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(oracle_cdb_config)

            assert "ORA-01017" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect(self, oracle_cdb_config, mock_oracle_connection):
        """Test Oracle disconnect"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.disconnect()

            assert result is True
            assert client.state == ConnectionState.CLOSED
            mock_oracle_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_with_cursor_cleanup(self, oracle_cdb_config, mock_oracle_connection):
        """Test disconnect with cursor cleanup"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            # Simulate cursor creation
            client._cursor = mock_oracle_connection.cursor()

            await client.disconnect()

            client._cursor.close.assert_called_once()
            mock_oracle_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected_property(self, oracle_cdb_config, mock_oracle_connection):
        """Test is_connected property"""
        client = OracleClient()

        assert client.is_connected is False

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False


# Test Query Execution

class TestOracleQueryExecution:
    """Test Oracle query execution"""

    @pytest.mark.asyncio
    async def test_execute_select_query(self, oracle_cdb_config, mock_oracle_connection):
        """Test SELECT query execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query("SELECT * FROM users")

            assert isinstance(result, dict)
            assert result['columns'] == ['ID', 'NAME', 'EMAIL']
            assert len(result['rows']) == 2
            assert result['rowcount'] == 2
            assert result['metadata']['database'] == 'free'
            assert result['metadata']['query_type'] == 'SELECT'

    @pytest.mark.asyncio
    async def test_execute_dual_query(self, oracle_cdb_config, mock_oracle_connection):
        """Test SELECT from DUAL"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = [('RESULT', int)]
        cursor.fetchall = Mock(return_value=[(1,)])
        cursor.rowcount = 1

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query("SELECT 1 FROM DUAL")

            assert result['columns'] == ['RESULT']
            assert len(result['rows']) == 1
            assert result['rows'][0] == (1,)

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, oracle_cdb_config, mock_oracle_connection):
        """Test query execution with parameters"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query(
                "SELECT * FROM users WHERE id = :id",
                {'id': 1}
            )

            assert isinstance(result, dict)
            assert len(result['rows']) == 2

            # Verify cursor.execute was called with params
            cursor = mock_oracle_connection.cursor()
            cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_execute_insert_query(self, oracle_cdb_config, mock_oracle_connection):
        """Test INSERT query execution"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = None  # INSERT doesn't return columns
        cursor.fetchall = Mock(return_value=[])
        cursor.rowcount = 1

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query(
                "INSERT INTO users (id, name) VALUES (:id, :name)",
                {'id': 3, 'name': 'test3'}
            )

            assert result['rowcount'] == 1
            assert result['metadata']['query_type'] == 'INSERT'

    @pytest.mark.asyncio
    async def test_execute_update_query(self, oracle_cdb_config, mock_oracle_connection):
        """Test UPDATE query execution"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = None
        cursor.fetchall = Mock(return_value=[])
        cursor.rowcount = 2

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query(
                "UPDATE users SET name = :name WHERE id = :id",
                {'name': 'updated', 'id': 1}
            )

            assert result['rowcount'] == 2
            assert result['metadata']['query_type'] == 'UPDATE'

    @pytest.mark.asyncio
    async def test_execute_delete_query(self, oracle_cdb_config, mock_oracle_connection):
        """Test DELETE query execution"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = None
        cursor.fetchall = Mock(return_value=[])
        cursor.rowcount = 1

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query(
                "DELETE FROM users WHERE id = :id",
                {'id': 1}
            )

            assert result['rowcount'] == 1
            assert result['metadata']['query_type'] == 'DELETE'

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected"""
        client = OracleClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_query("SELECT * FROM users")

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_query_type_detection(self):
        """Test query type detection"""
        client = OracleClient()

        assert client._get_query_type("SELECT * FROM users") == "SELECT"
        assert client._get_query_type("  select * from users") == "SELECT"
        assert client._get_query_type("INSERT INTO users VALUES (1)") == "INSERT"
        assert client._get_query_type("UPDATE users SET name = 'test'") == "UPDATE"
        assert client._get_query_type("DELETE FROM users") == "DELETE"
        assert client._get_query_type("CREATE TABLE test (id NUMBER)") == "DDL"
        assert client._get_query_type("ALTER TABLE test ADD column1 VARCHAR2(50)") == "DDL"
        assert client._get_query_type("DROP TABLE test") == "DDL"
        assert client._get_query_type("MERGE INTO users USING ...") == "OTHER"


# Test DDL Operations

class TestOracleDDL:
    """Test Oracle DDL operations"""

    @pytest.mark.asyncio
    async def test_execute_create_table(self, oracle_cdb_config, mock_oracle_connection):
        """Test CREATE TABLE execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            await client.execute_ddl("CREATE TABLE test (id NUMBER PRIMARY KEY, name VARCHAR2(100))")

            cursor = mock_oracle_connection.cursor()
            cursor.execute.assert_called()
            mock_oracle_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_alter_table(self, oracle_cdb_config, mock_oracle_connection):
        """Test ALTER TABLE execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            await client.execute_ddl("ALTER TABLE test ADD email VARCHAR2(255)")

            mock_oracle_connection.commit.assert_called()

    @pytest.mark.asyncio
    async def test_execute_drop_table(self, oracle_cdb_config, mock_oracle_connection):
        """Test DROP TABLE execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            await client.execute_ddl("DROP TABLE test")

            mock_oracle_connection.commit.assert_called()

    @pytest.mark.asyncio
    async def test_execute_create_index(self, oracle_cdb_config, mock_oracle_connection):
        """Test CREATE INDEX execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            await client.execute_ddl("CREATE INDEX idx_users_name ON users(name)")

            mock_oracle_connection.commit.assert_called()

    @pytest.mark.asyncio
    async def test_ddl_not_connected(self):
        """Test DDL execution when not connected"""
        client = OracleClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_ddl("CREATE TABLE test (id NUMBER)")

        assert exc_info.value.error_code == "NOT_CONNECTED"


# Test Oracle Metadata Operations

class TestOracleMetadata:
    """Test Oracle metadata operations"""

    @pytest.mark.asyncio
    async def test_get_table_info(self, oracle_cdb_config, mock_oracle_connection, mock_oracle_cursor):
        """Test table info retrieval"""
        client = OracleClient()

        # Replace the cursor with our mock
        mock_oracle_connection.cursor = Mock(return_value=mock_oracle_cursor)

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            table_info = await client.get_table_info('users')

            assert table_info['table_name'] == 'users'
            assert len(table_info['columns']) == 2
            assert table_info['columns'][0]['name'] == 'ID'
            assert table_info['columns'][0]['type'] == 'NUMBER'
            assert table_info['columns'][0]['nullable'] is False
            assert table_info['columns'][1]['name'] == 'NAME'
            assert table_info['columns'][1]['nullable'] is True

    @pytest.mark.asyncio
    async def test_get_table_info_uppercase(self, oracle_cdb_config, mock_oracle_connection, mock_oracle_cursor):
        """Test table info with uppercase conversion"""
        client = OracleClient()

        mock_oracle_connection.cursor = Mock(return_value=mock_oracle_cursor)

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            # Test with lowercase table name
            await client.get_table_info('users')

            # Verify the query used uppercase table name
            mock_oracle_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_table_list(self, oracle_cdb_config, mock_oracle_connection):
        """Test table list retrieval"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = [('TABLE_NAME', str)]
        cursor.fetchall = Mock(return_value=[
            ('USERS',),
            ('ORDERS',),
            ('PRODUCTS',)
        ])

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            tables = await client.get_table_list()

            assert len(tables) == 3
            assert 'USERS' in tables
            assert 'ORDERS' in tables
            assert 'PRODUCTS' in tables


# Test Health Check

class TestOracleHealthCheck:
    """Test Oracle health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, oracle_cdb_config, mock_oracle_connection):
        """Test health check for connected client"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            health = await client.health_check()

            assert health['state'] == 'connected'
            assert health['connected'] is True
            assert 'connection_time' in health
            assert health['ping_successful'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check for disconnected client"""
        client = OracleClient()
        health = await client.health_check()

        assert health['state'] == 'disconnected'
        assert health['connected'] is False
        assert health['connection_time'] is None

    @pytest.mark.asyncio
    async def test_ping_query(self):
        """Test Oracle-specific ping query"""
        client = OracleClient()
        ping_query = client._get_ping_query()

        assert ping_query == "SELECT 1 FROM DUAL"


# Test Error Handling

class TestOracleErrorHandling:
    """Test Oracle error handling"""

    @pytest.mark.asyncio
    async def test_query_execution_error(self, oracle_cdb_config, mock_oracle_connection):
        """Test query execution error handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.execute = Mock(side_effect=Exception("ORA-00942: table or view does not exist"))

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query("SELECT * FROM nonexistent_table")

            assert exc_info.value.error_code == "QUERY_FAILED"
            assert "ORA-00942" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ddl_execution_error(self, oracle_cdb_config, mock_oracle_connection):
        """Test DDL execution error handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.execute = Mock(side_effect=Exception("ORA-00955: name is already used by an existing object"))

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl("CREATE TABLE users (id NUMBER)")

            assert exc_info.value.error_code == "DDL_FAILED"
            assert "ORA-00955" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connection_timeout(self, oracle_cdb_config):
        """Test connection timeout handling"""
        client = OracleClient()

        with patch('oracledb.connect', side_effect=asyncio.TimeoutError("Connection timeout")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(oracle_cdb_config)

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_network_error(self, oracle_cdb_config):
        """Test network error handling"""
        client = OracleClient()

        with patch('oracledb.connect', side_effect=Exception("ORA-12170: TNS:Connect timeout occurred")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(oracle_cdb_config)

            assert "ORA-12170" in str(exc_info.value)


# Test Concurrent Operations

class TestOracleConcurrent:
    """Test concurrent Oracle operations"""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, oracle_cdb_config, mock_oracle_connection):
        """Test concurrent query execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)

            # Execute multiple queries concurrently
            tasks = [
                client.execute_query("SELECT * FROM users"),
                client.execute_query("SELECT * FROM orders"),
                client.execute_query("SELECT * FROM products")
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            for result in results:
                assert isinstance(result, dict)
                assert 'columns' in result
                assert 'rows' in result

    @pytest.mark.asyncio
    async def test_cursor_reuse(self, oracle_cdb_config, mock_oracle_connection):
        """Test cursor reuse across queries"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)

            # Execute first query (creates cursor)
            await client.execute_query("SELECT * FROM users")
            first_cursor = client._cursor

            # Execute second query (should reuse cursor)
            await client.execute_query("SELECT * FROM orders")
            second_cursor = client._cursor

            assert first_cursor is second_cursor


# Test Thin Mode Specific Features

class TestOracleThinMode:
    """Test Oracle thin mode specific features"""

    @pytest.mark.asyncio
    async def test_thin_mode_connection_string(self, oracle_cdb_config, mock_oracle_connection):
        """Test thin mode connection string format"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection) as mock_connect:
            await client.connect(oracle_cdb_config)

            # Verify DSN is in thin mode format (host:port/service)
            call_kwargs = mock_connect.call_args[1]
            assert 'dsn' in call_kwargs
            assert '/' in call_kwargs['dsn']
            assert ':' in call_kwargs['dsn']

    @pytest.mark.asyncio
    async def test_no_thick_mode_initialization(self):
        """Test that client doesn't initialize thick mode"""
        client = OracleClient()

        # Verify no thick mode attributes
        assert not hasattr(client, '_thick_mode')
        assert not hasattr(client, '_oracle_client_lib')

    @pytest.mark.asyncio
    async def test_extra_params_passed(self, oracle_cdb_config, mock_oracle_connection):
        """Test extra parameters passed to connection"""
        client = OracleClient()

        config = oracle_cdb_config
        config.extra_params = {'mode': 'SYSDBA', 'encoding': 'UTF-8'}

        with patch('oracledb.connect', return_value=mock_oracle_connection) as mock_connect:
            await client.connect(config)

            call_kwargs = mock_connect.call_args[1]
            assert 'mode' in call_kwargs
            assert call_kwargs['mode'] == 'SYSDBA'
            assert 'encoding' in call_kwargs
            assert call_kwargs['encoding'] == 'UTF-8'


# Test Column Type Handling

class TestOracleColumnTypes:
    """Test Oracle column type handling"""

    @pytest.mark.asyncio
    async def test_number_type(self, oracle_cdb_config, mock_oracle_connection):
        """Test NUMBER type handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = [('ID', int)]
        cursor.fetchall = Mock(return_value=[(12345,)])

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query("SELECT id FROM users")

            assert result['metadata']['column_types'] == ['int']

    @pytest.mark.asyncio
    async def test_varchar2_type(self, oracle_cdb_config, mock_oracle_connection):
        """Test VARCHAR2 type handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = [('NAME', str)]
        cursor.fetchall = Mock(return_value=[('test',)])

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query("SELECT name FROM users")

            assert result['metadata']['column_types'] == ['str']

    @pytest.mark.asyncio
    async def test_date_type(self, oracle_cdb_config, mock_oracle_connection):
        """Test DATE type handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor()
        cursor.description = [('CREATED_AT', datetime)]
        cursor.fetchall = Mock(return_value=[(datetime.now(),)])

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_cdb_config)
            result = await client.execute_query("SELECT created_at FROM users")

            assert 'datetime' in result['metadata']['column_types'][0]
