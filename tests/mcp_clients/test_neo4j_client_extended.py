"""
Comprehensive test suite for Neo4jClient
Target: Increase coverage from 15% to 80%
"""

import pytest
from unittest.mock import MagicMock, patch, call
from src.mcp_clients.neo4j_client import Neo4jClient


class TestNeo4jClientInitialization:
    """Test client initialization"""

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        assert client.uri == 'bolt://localhost:7687'
        assert client.username == 'neo4j'
        assert client.password == 'password'
        assert client.database == 'neo4j'
        assert client.encrypted is True
        assert client.driver is None

    def test_init_with_full_config(self):
        """Test initialization with full configuration"""
        client = Neo4jClient(
            uri='bolt://neo4j.example.com:7687',
            username='admin',
            password='secure123',
            database='production',
            encrypted=False,
            max_connection_lifetime=3600,
            max_connection_pool_size=100
        )

        assert client.uri == 'bolt://neo4j.example.com:7687'
        assert client.username == 'admin'
        assert client.database == 'production'
        assert client.encrypted is False
        assert 'max_connection_lifetime' in client.driver_options

    def test_init_with_custom_database(self):
        """Test initialization with custom database"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password',
            database='custom_db'
        )

        assert client.database == 'custom_db'


class TestNeo4jClientConnection:
    """Test connection management"""

    @pytest.mark.asyncio
    @patch('neo4j.GraphDatabase')
    async def test_connect_success(self, mock_graph_db):
        """Test successful connection"""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )
        await client.connect()

        assert client.driver is not None
        mock_driver.verify_connectivity.assert_called_once()

    @pytest.mark.asyncio
    @patch('neo4j.GraphDatabase')
    async def test_connect_with_encryption(self, mock_graph_db):
        """Test connection with encryption"""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password',
            encrypted=True
        )
        await client.connect()

        mock_graph_db.driver.assert_called_once()
        call_kwargs = mock_graph_db.driver.call_args[1]
        assert call_kwargs['encrypted'] is True

    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing neo4j driver"""
        with patch.dict('sys.modules', {'neo4j': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'neo4j'")):
                client = Neo4jClient(
                    uri='bolt://localhost:7687',
                    username='neo4j',
                    password='password'
                )

                with pytest.raises(ImportError, match="neo4j driver not installed"):
                    await client.connect()

    @pytest.mark.asyncio
    @patch('neo4j.GraphDatabase')
    async def test_connect_failure(self, mock_graph_db):
        """Test connection failure"""
        mock_graph_db.driver.side_effect = Exception("Connection failed")

        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        with pytest.raises(Exception, match="Connection failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )
        client.driver = MagicMock()

        await client.disconnect()

        client.driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_without_connection(self):
        """Test disconnection when not connected"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        # Should not raise error
        await client.disconnect()


class TestNeo4jClientQueries:
    """Test query execution"""

    @pytest.mark.asyncio
    async def test_execute_query_simple(self):
        """Test simple query execution"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        # Mock records
        mock_record1 = {'name': 'Alice', 'age': 30}
        mock_record2 = {'name': 'Bob', 'age': 25}
        mock_result.__iter__.return_value = [mock_record1, mock_record2]

        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.execute_query("MATCH (n:Person) RETURN n.name, n.age")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(self):
        """Test query execution with parameters"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []

        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        params = {'name': 'Alice', 'age': 30}
        result = await client.execute_query(
            "CREATE (n:Person {name: $name, age: $age})",
            params
        )

        mock_session.run.assert_called_once_with(
            "CREATE (n:Person {name: $name, age: $age})",
            params
        )

    @pytest.mark.asyncio
    async def test_execute_query_custom_database(self):
        """Test query execution on custom database"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []

        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.execute_query(
            "MATCH (n) RETURN n",
            database='custom_db'
        )

        mock_driver.session.assert_called_with(database='custom_db')

    @pytest.mark.asyncio
    async def test_execute_query_without_connection(self):
        """Test query execution without connection"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        with pytest.raises(RuntimeError, match="Not connected to Neo4j"):
            await client.execute_query("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    async def test_execute_query_error(self):
        """Test query execution error"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.run.side_effect = Exception("Query failed")

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        with pytest.raises(Exception, match="Query failed"):
            await client.execute_query("INVALID QUERY")


class TestNeo4jClientTransactions:
    """Test transaction operations"""

    @pytest.mark.asyncio
    async def test_execute_write_transaction(self):
        """Test write transaction"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_write.return_value = [{'created': 1}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.execute_write(
            "CREATE (n:Person {name: $name}) RETURN n",
            {'name': 'Alice'}
        )

        mock_session.execute_write.assert_called_once()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_read_transaction(self):
        """Test read transaction"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_read.return_value = [{'name': 'Alice'}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.execute_read(
            "MATCH (n:Person) RETURN n.name",
            {}
        )

        mock_session.execute_read.assert_called_once()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_execute_write_without_connection(self):
        """Test write transaction without connection"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        with pytest.raises(RuntimeError, match="Not connected to Neo4j"):
            await client.execute_write("CREATE (n:Person)")


class TestNeo4jClientNodeOperations:
    """Test node CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_node_single_label(self):
        """Test node creation with single label"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        node_data = {'name': 'Alice', 'age': 30}
        mock_session.execute_write.return_value = [{'n': node_data}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.create_node('Person', {'name': 'Alice', 'age': 30})

        assert result == node_data

    @pytest.mark.asyncio
    async def test_create_node_multiple_labels(self):
        """Test node creation with multiple labels"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        node_data = {'name': 'Alice', 'role': 'Developer'}
        mock_session.execute_write.return_value = [{'n': node_data}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.create_node(
            ['Person', 'Employee'],
            {'name': 'Alice', 'role': 'Developer'}
        )

        assert result == node_data

    @pytest.mark.asyncio
    async def test_get_node_found(self):
        """Test getting existing node"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()

        # Create a mock node object that behaves like Neo4j node
        mock_node = MagicMock()
        mock_node.__iter__ = lambda self: iter(['name', 'age'])
        mock_node.__getitem__ = lambda self, key: {'name': 'Alice', 'age': 30}[key]

        mock_session.execute_read.return_value = [{'n': mock_node}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_node('Person', 'name', 'Alice')

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_node_not_found(self):
        """Test getting non-existent node"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_read.return_value = []

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_node('Person', 'name', 'NonExistent')

        assert result is None

    @pytest.mark.asyncio
    async def test_update_node(self):
        """Test node update"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        updated_node = {'name': 'Alice', 'age': 31}
        mock_session.execute_write.return_value = [{'n': updated_node}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.update_node(
            'Person',
            'name',
            'Alice',
            {'age': 31}
        )

        assert result == updated_node

    @pytest.mark.asyncio
    async def test_delete_node_with_detach(self):
        """Test node deletion with detach"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_write.return_value = [{'deleted': 1}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.delete_node('Person', 'name', 'Alice', detach=True)

        assert result == 1

    @pytest.mark.asyncio
    async def test_delete_node_without_detach(self):
        """Test node deletion without detach"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_write.return_value = [{'deleted': 1}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.delete_node('Person', 'name', 'Alice', detach=False)

        assert result == 1


class TestNeo4jClientRelationships:
    """Test relationship operations"""

    @pytest.mark.asyncio
    async def test_create_relationship(self):
        """Test relationship creation"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        rel_data = {'since': '2020'}
        mock_session.execute_write.return_value = [{'r': rel_data}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.create_relationship(
            'Person', 'name', 'Alice',
            'Person', 'name', 'Bob',
            'KNOWS',
            {'since': '2020'}
        )

        assert result == rel_data

    @pytest.mark.asyncio
    async def test_create_relationship_without_properties(self):
        """Test relationship creation without properties"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_write.return_value = [{'r': {}}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.create_relationship(
            'Person', 'name', 'Alice',
            'Person', 'name', 'Bob',
            'FOLLOWS'
        )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_relationships_outgoing(self):
        """Test getting outgoing relationships"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        relationships = [
            {'r': {'type': 'KNOWS'}, 'target_labels': ['Person'], 'target_node': {'name': 'Bob'}}
        ]
        mock_session.execute_read.return_value = relationships

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_relationships(
            'Person', 'name', 'Alice', direction='outgoing'
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_relationships_incoming(self):
        """Test getting incoming relationships"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        relationships = []
        mock_session.execute_read.return_value = relationships

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_relationships(
            'Person', 'name', 'Alice', direction='incoming'
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_relationships_both(self):
        """Test getting all relationships"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        relationships = [
            {'r': {}, 'target_labels': ['Person'], 'target_node': {'name': 'Bob'}},
            {'r': {}, 'target_labels': ['Person'], 'target_node': {'name': 'Charlie'}}
        ]
        mock_session.execute_read.return_value = relationships

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_relationships(
            'Person', 'name', 'Alice', direction='both'
        )

        assert len(result) == 2


class TestNeo4jClientMetadata:
    """Test metadata operations"""

    @pytest.mark.asyncio
    async def test_get_database_info(self):
        """Test database info retrieval"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        db_info = {
            'name': 'Neo4j Kernel',
            'versions': ['4.4.0'],
            'edition': 'community'
        }
        mock_session.run.return_value = [db_info]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_database_info()

        assert result == db_info

    @pytest.mark.asyncio
    async def test_get_node_count_all(self):
        """Test getting count of all nodes"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_read.return_value = [{'count': 100}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_node_count()

        assert result == 100

    @pytest.mark.asyncio
    async def test_get_node_count_by_label(self):
        """Test getting count of nodes by label"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_read.return_value = [{'count': 50}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_node_count('Person')

        assert result == 50

    @pytest.mark.asyncio
    async def test_get_relationship_count_all(self):
        """Test getting count of all relationships"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_read.return_value = [{'count': 200}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_relationship_count()

        assert result == 200

    @pytest.mark.asyncio
    async def test_get_relationship_count_by_type(self):
        """Test getting count of relationships by type"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_session.execute_read.return_value = [{'count': 75}]

        mock_driver.session.return_value.__enter__.return_value = mock_session
        client.driver = mock_driver

        result = await client.get_relationship_count('KNOWS')

        assert result == 75


class TestNeo4jClientGraphAlgorithms:
    """Test graph algorithm operations"""

    @pytest.mark.asyncio
    async def test_execute_graph_algorithm_not_implemented(self):
        """Test graph algorithm execution (not implemented)"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        client.driver = MagicMock()

        with pytest.raises(NotImplementedError, match="Graph algorithms require"):
            await client.execute_graph_algorithm('pageRank', {})


class TestNeo4jClientContextManager:
    """Test context manager functionality"""

    def test_context_manager_enter(self):
        """Test context manager entry"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        with patch('asyncio.create_task') as mock_task:
            result = client.__enter__()

            assert result == client
            mock_task.assert_called_once()

    def test_context_manager_exit(self):
        """Test context manager exit"""
        client = Neo4jClient(
            uri='bolt://localhost:7687',
            username='neo4j',
            password='password'
        )

        with patch('asyncio.create_task') as mock_task:
            client.__exit__(None, None, None)

            mock_task.assert_called_once()
