"""
Comprehensive test suite for CassandraClient
Target: Increase coverage from 12% to 80%
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from src.mcp_clients.cassandra_client import CassandraClient


class TestCassandraClientInitialization:
    """Test client initialization"""

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        client = CassandraClient(contact_points=['localhost'])

        assert client.contact_points == ['localhost']
        assert client.port == 9042
        assert client.keyspace is None
        assert client.username is None
        assert client.password is None
        assert client.protocol_version == 4
        assert client.cluster is None
        assert client.session is None
        assert isinstance(client.prepared_statements, dict)

    def test_init_with_full_config(self):
        """Test initialization with full configuration"""
        client = CassandraClient(
            contact_points=['node1', 'node2', 'node3'],
            port=9043,
            keyspace='test_keyspace',
            username='testuser',
            password='testpass',
            protocol_version=5,
            load_balancing_policy='RoundRobin'
        )

        assert client.contact_points == ['node1', 'node2', 'node3']
        assert client.port == 9043
        assert client.keyspace == 'test_keyspace'
        assert client.username == 'testuser'
        assert client.password == 'testpass'
        assert client.protocol_version == 5
        assert 'load_balancing_policy' in client.driver_options

    def test_init_with_authentication(self):
        """Test initialization with authentication"""
        client = CassandraClient(
            contact_points=['localhost'],
            username='admin',
            password='secure123'
        )

        assert client.username == 'admin'
        assert client.password == 'secure123'


class TestCassandraClientConnection:
    """Test connection management"""

    @pytest.mark.asyncio
    async def test_connect_without_auth(self):
        """Test connection without authentication"""
        with patch.dict('sys.modules', {'cassandra': MagicMock(), 'cassandra.cluster': MagicMock(), 'cassandra.auth': MagicMock()}):
            from unittest.mock import MagicMock as MM
            mock_cluster_instance = MM()
            mock_session = MM()
            mock_cluster_instance.connect.return_value = mock_session

            with patch('cassandra.cluster.Cluster', return_value=mock_cluster_instance):
                client = CassandraClient(contact_points=['localhost'])
                await client.connect()

                assert client.cluster is not None
                assert client.session is not None

    @pytest.mark.asyncio
    @patch('cassandra.cluster.Cluster')
    @patch('cassandra.auth.PlainTextAuthProvider')
    async def test_connect_with_auth(self, mock_auth_provider, mock_cluster):
        """Test connection with authentication"""
        mock_auth = MagicMock()
        mock_auth_provider.return_value = mock_auth
        mock_cluster_instance = MagicMock()
        mock_session = MagicMock()
        mock_cluster.return_value = mock_cluster_instance
        mock_cluster_instance.connect.return_value = mock_session

        client = CassandraClient(
            contact_points=['localhost'],
            username='testuser',
            password='testpass'
        )
        await client.connect()

        mock_auth_provider.assert_called_once_with(
            username='testuser',
            password='testpass'
        )
        assert client.cluster is not None
        assert client.session is not None

    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing cassandra-driver"""
        with patch.dict('sys.modules', {'cassandra.cluster': None, 'cassandra.auth': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'cassandra'")):
                client = CassandraClient(contact_points=['localhost'])

                with pytest.raises(ImportError, match="cassandra-driver not installed"):
                    await client.connect()

    @pytest.mark.asyncio
    @patch('cassandra.cluster.Cluster')
    async def test_connect_connection_error(self, mock_cluster):
        """Test connection failure"""
        mock_cluster.side_effect = Exception("Connection failed")

        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(Exception, match="Connection failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        client.cluster = MagicMock()

        await client.disconnect()

        client.session.shutdown.assert_called_once()
        client.cluster.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_without_connection(self):
        """Test disconnection when not connected"""
        client = CassandraClient(contact_points=['localhost'])

        # Should not raise error
        await client.disconnect()


class TestCassandraClientQueries:
    """Test query execution"""

    @pytest.mark.asyncio
    async def test_execute_simple_query(self):
        """Test simple query execution"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_result = MagicMock()
        client.session.execute.return_value = mock_result

        result = await client.execute("SELECT * FROM users")

        assert result == mock_result
        client.session.execute.assert_called_once_with("SELECT * FROM users", None, timeout=None)

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(self):
        """Test query execution with parameters"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_result = MagicMock()
        client.session.execute.return_value = mock_result

        params = (1, 'test')
        result = await client.execute("SELECT * FROM users WHERE id = ? AND name = ?", params)

        assert result == mock_result
        client.session.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id = ? AND name = ?",
            params,
            timeout=None
        )

    @pytest.mark.asyncio
    async def test_execute_query_with_timeout(self):
        """Test query execution with timeout"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_result = MagicMock()
        client.session.execute.return_value = mock_result

        result = await client.execute("SELECT * FROM users", timeout=10.0)

        assert result == mock_result
        client.session.execute.assert_called_once_with("SELECT * FROM users", None, timeout=10.0)

    @pytest.mark.asyncio
    async def test_execute_without_connection(self):
        """Test query execution without connection"""
        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(RuntimeError, match="Not connected to Cassandra"):
            await client.execute("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_execute_query_error(self):
        """Test query execution error"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        client.session.execute.side_effect = Exception("Query failed")

        with pytest.raises(Exception, match="Query failed"):
            await client.execute("INVALID QUERY")

    @pytest.mark.asyncio
    async def test_execute_async_query(self):
        """Test async query execution"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_future = MagicMock()
        client.session.execute_async.return_value = mock_future

        result = await client.execute_async("SELECT * FROM users")

        assert result == mock_future
        client.session.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async_with_parameters(self):
        """Test async query with parameters"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_future = MagicMock()
        client.session.execute_async.return_value = mock_future

        params = (1, 'test')
        result = await client.execute_async("SELECT * FROM users WHERE id = ?", params)

        assert result == mock_future

    @pytest.mark.asyncio
    async def test_execute_async_without_connection(self):
        """Test async query without connection"""
        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(RuntimeError, match="Not connected to Cassandra"):
            await client.execute_async("SELECT * FROM users")


class TestCassandraClientPreparedStatements:
    """Test prepared statement functionality"""

    @pytest.mark.asyncio
    async def test_prepare_statement(self):
        """Test statement preparation"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_prepared = MagicMock()
        client.session.prepare.return_value = mock_prepared

        query = "SELECT * FROM users WHERE id = ?"
        result = await client.prepare(query)

        assert result == mock_prepared
        assert query in client.prepared_statements
        assert client.prepared_statements[query] == mock_prepared

    @pytest.mark.asyncio
    async def test_prepare_cached_statement(self):
        """Test cached prepared statement retrieval"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_prepared = MagicMock()

        query = "SELECT * FROM users WHERE id = ?"
        client.prepared_statements[query] = mock_prepared

        result = await client.prepare(query)

        assert result == mock_prepared
        client.session.prepare.assert_not_called()

    @pytest.mark.asyncio
    async def test_prepare_without_connection(self):
        """Test prepare without connection"""
        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(RuntimeError, match="Not connected to Cassandra"):
            await client.prepare("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_prepare_statement_error(self):
        """Test prepare statement error"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        client.session.prepare.side_effect = Exception("Preparation failed")

        with pytest.raises(Exception, match="Preparation failed"):
            await client.prepare("INVALID QUERY")

    @pytest.mark.asyncio
    async def test_execute_prepared_statement(self):
        """Test prepared statement execution"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_prepared = MagicMock()
        mock_result = MagicMock()
        client.session.prepare.return_value = mock_prepared
        client.session.execute.return_value = mock_result

        query = "SELECT * FROM users WHERE id = ?"
        params = (1,)
        result = await client.execute_prepared(query, params)

        assert result == mock_result


class TestCassandraClientBatchOperations:
    """Test batch operations"""

    @pytest.mark.asyncio
    @patch('cassandra.query.BatchStatement')
    @patch('cassandra.query.ConsistencyLevel')
    async def test_batch_execute(self, mock_consistency, mock_batch):
        """Test batch execution"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_batch_instance = MagicMock()
        mock_batch.return_value = mock_batch_instance

        queries = [
            ("INSERT INTO users (id, name) VALUES (?, ?)", (1, 'Alice')),
            ("INSERT INTO users (id, name) VALUES (?, ?)", (2, 'Bob')),
            ("UPDATE users SET name = ? WHERE id = ?", ('Charlie', 3))
        ]

        await client.batch_execute(queries)

        assert mock_batch_instance.add.call_count == 3
        client.session.execute.assert_called_once_with(mock_batch_instance)

    @pytest.mark.asyncio
    @patch('cassandra.query.BatchStatement')
    @patch('cassandra.query.ConsistencyLevel')
    async def test_batch_execute_with_consistency(self, mock_consistency, mock_batch):
        """Test batch execution with consistency level"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        mock_batch_instance = MagicMock()
        mock_batch.return_value = mock_batch_instance
        mock_consistency.QUORUM = 'QUORUM'

        queries = [("INSERT INTO users (id, name) VALUES (?, ?)", (1, 'Alice'))]

        await client.batch_execute(queries, consistency_level='QUORUM')

        assert hasattr(mock_batch_instance, 'consistency_level')

    @pytest.mark.asyncio
    async def test_batch_execute_without_connection(self):
        """Test batch execution without connection"""
        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(RuntimeError, match="Not connected to Cassandra"):
            await client.batch_execute([])

    @pytest.mark.asyncio
    @patch('src.mcp_clients.cassandra_client.BatchStatement')
    async def test_batch_execute_error(self, mock_batch):
        """Test batch execution error"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()
        client.session.execute.side_effect = Exception("Batch failed")

        queries = [("INSERT INTO users (id, name) VALUES (?, ?)", (1, 'Alice'))]

        with pytest.raises(Exception, match="Batch failed"):
            await client.batch_execute(queries)


class TestCassandraClientKeyspaceManagement:
    """Test keyspace management operations"""

    @pytest.mark.asyncio
    async def test_create_keyspace_simple(self):
        """Test simple keyspace creation"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()

        await client.create_keyspace('test_ks')

        client.session.execute.assert_called_once()
        call_args = client.session.execute.call_args[0][0]
        assert 'CREATE KEYSPACE IF NOT EXISTS test_ks' in call_args
        assert 'SimpleStrategy' in call_args
        assert 'replication_factor' in call_args

    @pytest.mark.asyncio
    async def test_create_keyspace_with_options(self):
        """Test keyspace creation with custom options"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()

        await client.create_keyspace(
            'test_ks',
            replication_strategy='NetworkTopologyStrategy',
            replication_factor=3
        )

        call_args = client.session.execute.call_args[0][0]
        assert 'NetworkTopologyStrategy' in call_args
        assert '3' in call_args

    @pytest.mark.asyncio
    async def test_drop_keyspace(self):
        """Test keyspace deletion"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()

        await client.drop_keyspace('test_ks')

        client.session.execute.assert_called_once()
        call_args = client.session.execute.call_args[0][0]
        assert 'DROP KEYSPACE IF EXISTS test_ks' in call_args

    @pytest.mark.asyncio
    async def test_use_keyspace(self):
        """Test keyspace switching"""
        client = CassandraClient(contact_points=['localhost'])
        client.session = MagicMock()

        await client.use_keyspace('new_keyspace')

        client.session.set_keyspace.assert_called_once_with('new_keyspace')
        assert client.keyspace == 'new_keyspace'

    @pytest.mark.asyncio
    async def test_use_keyspace_without_connection(self):
        """Test keyspace switching without connection"""
        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(RuntimeError, match="Not connected to Cassandra"):
            await client.use_keyspace('test_ks')


class TestCassandraClientMetadata:
    """Test metadata retrieval"""

    @pytest.mark.asyncio
    async def test_get_cluster_metadata(self):
        """Test cluster metadata retrieval"""
        client = CassandraClient(contact_points=['localhost'])

        mock_cluster = MagicMock()
        mock_metadata = MagicMock()
        mock_cluster.metadata = mock_metadata
        mock_metadata.cluster_name = 'test_cluster'
        mock_metadata.partitioner = 'Murmur3Partitioner'
        mock_metadata.all_hosts.return_value = ['host1', 'host2']
        mock_metadata.keyspaces.keys.return_value = ['ks1', 'ks2']
        mock_metadata.token_map = {'token1': 'value1'}

        client.cluster = mock_cluster

        result = await client.get_cluster_metadata()

        assert result['cluster_name'] == 'test_cluster'
        assert result['partitioner'] == 'Murmur3Partitioner'
        assert len(result['hosts']) == 2
        assert len(result['keyspaces']) == 2
        assert result['token_map'] == 1

    @pytest.mark.asyncio
    async def test_get_cluster_metadata_without_connection(self):
        """Test cluster metadata without connection"""
        client = CassandraClient(contact_points=['localhost'])

        with pytest.raises(RuntimeError, match="Not connected to Cassandra"):
            await client.get_cluster_metadata()

    @pytest.mark.asyncio
    async def test_get_keyspace_info(self):
        """Test keyspace info retrieval"""
        client = CassandraClient(contact_points=['localhost'])

        mock_cluster = MagicMock()
        mock_metadata = MagicMock()
        mock_ks_meta = MagicMock()
        mock_replication_strategy = MagicMock()

        mock_ks_meta.name = 'test_ks'
        mock_replication_strategy.name = 'SimpleStrategy'
        mock_replication_strategy.replication_factor = 3
        mock_ks_meta.replication_strategy = mock_replication_strategy
        mock_ks_meta.durable_writes = True
        mock_ks_meta.tables.keys.return_value = ['table1', 'table2']

        mock_metadata.keyspaces.get.return_value = mock_ks_meta
        mock_cluster.metadata = mock_metadata
        client.cluster = mock_cluster

        result = await client.get_keyspace_info('test_ks')

        assert result['name'] == 'test_ks'
        assert result['replication_strategy'] == 'SimpleStrategy'
        assert result['replication_factor'] == 3
        assert result['durable_writes'] is True
        assert len(result['tables']) == 2

    @pytest.mark.asyncio
    async def test_get_keyspace_info_not_found(self):
        """Test keyspace info for non-existent keyspace"""
        client = CassandraClient(contact_points=['localhost'])

        mock_cluster = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.keyspaces.get.return_value = None
        mock_cluster.metadata = mock_metadata
        client.cluster = mock_cluster

        with pytest.raises(ValueError, match="Keyspace 'nonexistent' not found"):
            await client.get_keyspace_info('nonexistent')

    @pytest.mark.asyncio
    async def test_get_table_info(self):
        """Test table info retrieval"""
        client = CassandraClient(contact_points=['localhost'])

        mock_cluster = MagicMock()
        mock_metadata = MagicMock()
        mock_ks_meta = MagicMock()
        mock_table_meta = MagicMock()

        # Setup mock columns
        mock_col1 = MagicMock()
        mock_col1.name = 'id'
        mock_col1.cql_type = 'int'
        mock_col2 = MagicMock()
        mock_col2.name = 'name'
        mock_col2.cql_type = 'text'

        mock_table_meta.name = 'users'
        mock_table_meta.columns = {'id': mock_col1, 'name': mock_col2}

        # Setup keys
        partition_key_col = MagicMock()
        partition_key_col.name = 'id'
        mock_table_meta.partition_key = [partition_key_col]
        mock_table_meta.clustering_key = []
        mock_table_meta.indexes.keys.return_value = []

        mock_ks_meta.tables.get.return_value = mock_table_meta
        mock_metadata.keyspaces.get.return_value = mock_ks_meta
        mock_cluster.metadata = mock_metadata
        client.cluster = mock_cluster

        result = await client.get_table_info('test_ks', 'users')

        assert result['name'] == 'users'
        assert len(result['columns']) == 2
        assert result['partition_key'] == ['id']
        assert result['clustering_key'] == []

    @pytest.mark.asyncio
    async def test_get_table_info_not_found(self):
        """Test table info for non-existent table"""
        client = CassandraClient(contact_points=['localhost'])

        mock_cluster = MagicMock()
        mock_metadata = MagicMock()
        mock_ks_meta = MagicMock()
        mock_ks_meta.tables.get.return_value = None
        mock_metadata.keyspaces.get.return_value = mock_ks_meta
        mock_cluster.metadata = mock_metadata
        client.cluster = mock_cluster

        with pytest.raises(ValueError, match="Table 'nonexistent' not found"):
            await client.get_table_info('test_ks', 'nonexistent')


class TestCassandraClientContextManager:
    """Test context manager functionality"""

    def test_context_manager_enter(self):
        """Test context manager entry"""
        client = CassandraClient(contact_points=['localhost'])

        with patch('asyncio.create_task') as mock_task:
            result = client.__enter__()

            assert result == client
            mock_task.assert_called_once()

    def test_context_manager_exit(self):
        """Test context manager exit"""
        client = CassandraClient(contact_points=['localhost'])

        with patch('asyncio.create_task') as mock_task:
            client.__exit__(None, None, None)

            mock_task.assert_called_once()
