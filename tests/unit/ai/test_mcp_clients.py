"""
Comprehensive Unit Tests for MCP Client Integration

Tests protocol compliance, connection management, query execution,
error handling, and connection pooling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Any, Dict

from src.mcp_clients.base import (
    BaseMCPClient,
    MCPClientError,
    ConnectionState,
    ConnectionConfig,
    QueryResult
)
from src.mcp_clients.oracle_client import OracleClient
from src.mcp_clients.postgresql_client import PostgreSQLClient
from src.mcp_clients.manager import ConnectionManager, ConnectionInfo


# Test Fixtures

@pytest.fixture
def oracle_config():
    """Oracle connection configuration"""
    return ConnectionConfig(
        host='localhost',
        port=1521,
        database='TESTDB',
        username='testuser',
        password='testpass',
        extra_params={'encoding': 'UTF-8'}
    )


@pytest.fixture
def postgresql_config():
    """PostgreSQL connection configuration"""
    return ConnectionConfig(
        host='localhost',
        port=5432,
        database='testdb',
        username='testuser',
        password='testpass',
        extra_params={'connect_timeout': 10}
    )


@pytest.fixture
def mock_oracle_connection():
    """Mock Oracle connection"""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.description = [
        ('ID', int),
        ('NAME', str),
        ('VALUE', float)
    ]
    cursor.fetchall.return_value = [
        (1, 'test1', 10.5),
        (2, 'test2', 20.3)
    ]
    cursor.rowcount = 2
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
def mock_postgresql_connection():
    """Mock PostgreSQL connection"""
    conn = MagicMock()
    cursor = MagicMock()

    # Mock cursor description
    desc_id = MagicMock()
    desc_id.name = 'id'
    desc_id.type_code = 23  # INTEGER

    desc_name = MagicMock()
    desc_name.name = 'name'
    desc_name.type_code = 1043  # VARCHAR

    cursor.description = [desc_id, desc_name]
    cursor.fetchall.return_value = [
        {'id': 1, 'name': 'test1'},
        {'id': 2, 'name': 'test2'}
    ]
    cursor.rowcount = 2
    conn.cursor.return_value = cursor
    return conn


# Test Base Protocol Compliance

class TestMCPProtocolCompliance:
    """Test MCP protocol interface compliance"""

    @pytest.mark.asyncio
    async def test_base_client_state_property(self):
        """Test state property exists and returns ConnectionState"""
        client = OracleClient()
        assert hasattr(client, 'state')
        assert isinstance(client.state, ConnectionState)
        assert client.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_base_client_connect_method(self, oracle_config):
        """Test connect method exists and has correct signature"""
        client = OracleClient()
        assert hasattr(client, 'connect')
        assert asyncio.iscoroutinefunction(client.connect)

    @pytest.mark.asyncio
    async def test_base_client_disconnect_method(self):
        """Test disconnect method exists and has correct signature"""
        client = OracleClient()
        assert hasattr(client, 'disconnect')
        assert asyncio.iscoroutinefunction(client.disconnect)

    @pytest.mark.asyncio
    async def test_base_client_execute_query_method(self):
        """Test execute_query method exists and has correct signature"""
        client = OracleClient()
        assert hasattr(client, 'execute_query')
        assert asyncio.iscoroutinefunction(client.execute_query)

    @pytest.mark.asyncio
    async def test_base_client_health_check_method(self):
        """Test health_check method exists and has correct signature"""
        client = OracleClient()
        assert hasattr(client, 'health_check')
        assert asyncio.iscoroutinefunction(client.health_check)


# Test Oracle Client

class TestOracleClient:
    """Test Oracle client implementation"""

    @pytest.mark.asyncio
    async def test_oracle_connect_success(self, oracle_config, mock_oracle_connection):
        """Test successful Oracle connection"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            result = await client.connect(oracle_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_oracle_connect_failure(self, oracle_config):
        """Test Oracle connection failure handling"""
        client = OracleClient()

        with patch('oracledb.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(oracle_config)

            assert exc_info.value.error_code == "CONNECTION_FAILED"
            assert client.state == ConnectionState.ERROR

    @pytest.mark.asyncio
    async def test_oracle_disconnect(self, oracle_config, mock_oracle_connection):
        """Test Oracle disconnect"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_config)
            result = await client.disconnect()

            assert result is True
            assert client.state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_oracle_execute_query(self, oracle_config, mock_oracle_connection):
        """Test Oracle query execution"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_config)
            result = await client.execute_query("SELECT * FROM test")

            assert isinstance(result, QueryResult)
            assert result.columns == ['ID', 'NAME', 'VALUE']
            assert len(result.rows) == 2
            assert result.rowcount == 2
            assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_oracle_execute_query_not_connected(self):
        """Test query execution when not connected"""
        client = OracleClient()

        with pytest.raises(MCPClientError) as exc_info:
            await client.execute_query("SELECT * FROM test")

        assert exc_info.value.error_code == "NOT_CONNECTED"

    @pytest.mark.asyncio
    async def test_oracle_get_table_info(self, oracle_config, mock_oracle_connection):
        """Test Oracle table info retrieval"""
        client = OracleClient()

        # Setup mock for table info query
        cursor = mock_oracle_connection.cursor.return_value
        cursor.description = [
            ('COLUMN_NAME', str),
            ('DATA_TYPE', str),
            ('DATA_LENGTH', int),
            ('NULLABLE', str),
            ('DATA_DEFAULT', str)
        ]
        cursor.fetchall.return_value = [
            ('ID', 'NUMBER', 10, 'N', None),
            ('NAME', 'VARCHAR2', 100, 'Y', None)
        ]

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_config)
            table_info = await client.get_table_info('TEST_TABLE')

            assert table_info['table_name'] == 'TEST_TABLE'
            assert len(table_info['columns']) == 2
            assert table_info['columns'][0]['name'] == 'ID'
            assert table_info['columns'][0]['nullable'] is False


# Test PostgreSQL Client

class TestPostgreSQLClient:
    """Test PostgreSQL client implementation"""

    @pytest.mark.asyncio
    async def test_postgresql_connect_success(self, postgresql_config, mock_postgresql_connection):
        """Test successful PostgreSQL connection"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgresql_connection):
            result = await client.connect(postgresql_config)

            assert result is True
            assert client.state == ConnectionState.CONNECTED
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_postgresql_connect_failure(self, postgresql_config):
        """Test PostgreSQL connection failure handling"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(MCPClientError) as exc_info:
                await client.connect(postgresql_config)

            assert exc_info.value.error_code == "CONNECTION_FAILED"
            assert client.state == ConnectionState.ERROR

    @pytest.mark.asyncio
    async def test_postgresql_execute_query(self, postgresql_config, mock_postgresql_connection):
        """Test PostgreSQL query execution"""
        client = PostgreSQLClient()

        with patch('psycopg2.connect', return_value=mock_postgresql_connection):
            await client.connect(postgresql_config)
            result = await client.execute_query("SELECT * FROM test")

            assert isinstance(result, QueryResult)
            assert result.columns == ['id', 'name']
            assert len(result.rows) == 2
            assert result.rowcount == 2

    @pytest.mark.asyncio
    async def test_postgresql_get_schemas(self, postgresql_config, mock_postgresql_connection):
        """Test PostgreSQL schema retrieval"""
        client = PostgreSQLClient()

        # Setup mock for schema query
        cursor = mock_postgresql_connection.cursor.return_value
        desc = MagicMock()
        desc.name = 'schema_name'
        cursor.description = [desc]
        cursor.fetchall.return_value = [
            {'schema_name': 'public'},
            {'schema_name': 'custom'}
        ]

        with patch('psycopg2.connect', return_value=mock_postgresql_connection):
            await client.connect(postgresql_config)
            schemas = await client.get_schemas()

            assert len(schemas) == 2
            assert 'public' in schemas
            assert 'custom' in schemas


# Test Connection Manager

class TestConnectionManager:
    """Test connection manager functionality"""

    @pytest.mark.asyncio
    async def test_create_oracle_connection(self, oracle_config, mock_oracle_connection):
        """Test creating Oracle connection through manager"""
        manager = ConnectionManager(max_connections=5)

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            conn_id = await manager.create_connection(
                'test-oracle',
                'oracle',
                oracle_config
            )

            assert conn_id == 'test-oracle'
            assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_create_postgresql_connection(self, postgresql_config, mock_postgresql_connection):
        """Test creating PostgreSQL connection through manager"""
        manager = ConnectionManager(max_connections=5)

        with patch('psycopg2.connect', return_value=mock_postgresql_connection):
            conn_id = await manager.create_connection(
                'test-pg',
                'postgresql',
                postgresql_config
            )

            assert conn_id == 'test-pg'
            assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_max_connections_limit(self, oracle_config, mock_oracle_connection):
        """Test max connections limit enforcement"""
        manager = ConnectionManager(max_connections=2)

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await manager.create_connection('conn1', 'oracle', oracle_config)
            await manager.create_connection('conn2', 'oracle', oracle_config)

            with pytest.raises(MCPClientError) as exc_info:
                await manager.create_connection('conn3', 'oracle', oracle_config)

            assert exc_info.value.error_code == "MAX_CONNECTIONS"

    @pytest.mark.asyncio
    async def test_get_connection(self, oracle_config, mock_oracle_connection):
        """Test retrieving connection by ID"""
        manager = ConnectionManager()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await manager.create_connection('test', 'oracle', oracle_config)
            client = await manager.get_connection('test')

            assert isinstance(client, OracleClient)
            assert client.is_connected

    @pytest.mark.asyncio
    async def test_get_nonexistent_connection(self):
        """Test getting connection that doesn't exist"""
        manager = ConnectionManager()

        with pytest.raises(MCPClientError) as exc_info:
            await manager.get_connection('nonexistent')

        assert exc_info.value.error_code == "CONNECTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_close_connection(self, oracle_config, mock_oracle_connection):
        """Test closing connection"""
        manager = ConnectionManager()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await manager.create_connection('test', 'oracle', oracle_config)
            result = await manager.close_connection('test')

            assert result is True
            assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_close_all_connections(self, oracle_config, mock_oracle_connection):
        """Test closing all connections"""
        manager = ConnectionManager()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await manager.create_connection('conn1', 'oracle', oracle_config)
            await manager.create_connection('conn2', 'oracle', oracle_config)

            count = await manager.close_all()

            assert count == 2
            assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_list_connections(self, oracle_config, mock_oracle_connection):
        """Test listing all connections"""
        manager = ConnectionManager()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await manager.create_connection('conn1', 'oracle', oracle_config)
            connections = manager.list_connections()

            assert len(connections) == 1
            assert connections[0]['connection_id'] == 'conn1'
            assert connections[0]['client_type'] == 'oracle'

    @pytest.mark.asyncio
    async def test_manager_stats(self, oracle_config, postgresql_config,
                                 mock_oracle_connection, mock_postgresql_connection):
        """Test manager statistics"""
        manager = ConnectionManager(max_connections=5)

        with patch('oracledb.connect', return_value=mock_oracle_connection), \
             patch('psycopg2.connect', return_value=mock_postgresql_connection):

            await manager.create_connection('oracle1', 'oracle', oracle_config)
            await manager.create_connection('pg1', 'postgresql', postgresql_config)

            stats = manager.get_stats()

            assert stats['total_connections'] == 2
            assert stats['max_connections'] == 5
            assert stats['utilization'] == 0.4
            assert stats['by_type']['oracle'] == 1
            assert stats['by_type']['postgresql'] == 1


# Test Error Handling

class TestErrorHandling:
    """Test comprehensive error handling"""

    @pytest.mark.asyncio
    async def test_query_execution_error(self, oracle_config, mock_oracle_connection):
        """Test query execution error handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor.return_value
        cursor.execute.side_effect = Exception("SQL execution failed")

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_query("INVALID SQL")

            assert exc_info.value.error_code == "QUERY_FAILED"

    @pytest.mark.asyncio
    async def test_ddl_execution_error(self, oracle_config, mock_oracle_connection):
        """Test DDL execution error handling"""
        client = OracleClient()

        cursor = mock_oracle_connection.cursor.return_value
        cursor.execute.side_effect = Exception("DDL failed")

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_config)

            with pytest.raises(MCPClientError) as exc_info:
                await client.execute_ddl("CREATE TABLE test (id INT)")

            assert exc_info.value.error_code == "DDL_FAILED"

    @pytest.mark.asyncio
    async def test_unknown_client_type(self, oracle_config):
        """Test unknown client type error"""
        manager = ConnectionManager()

        with pytest.raises(MCPClientError) as exc_info:
            await manager.create_connection('test', 'unknown', oracle_config)

        assert exc_info.value.error_code == "UNKNOWN_CLIENT_TYPE"


# Test Health Check

class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, oracle_config, mock_oracle_connection):
        """Test health check for connected client"""
        client = OracleClient()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await client.connect(oracle_config)
            health = await client.health_check()

            assert health['state'] == 'connected'
            assert health['connected'] is True
            assert 'connection_time' in health

    @pytest.mark.asyncio
    async def test_health_check_all_connections(self, oracle_config, mock_oracle_connection):
        """Test health check for all connections"""
        manager = ConnectionManager()

        with patch('oracledb.connect', return_value=mock_oracle_connection):
            await manager.create_connection('conn1', 'oracle', oracle_config)
            health = await manager.health_check_all()

            assert 'conn1' in health
            assert health['conn1']['state'] == 'connected'
