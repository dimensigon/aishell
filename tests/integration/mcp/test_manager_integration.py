"""Connection Manager integration tests."""
import asyncio
import pytest
from tests.integration.mcp.config import DOCKER_CONFIGS


class TestConnectionManagerBasics:
    """Test connection manager basic operations."""

    @pytest.mark.asyncio
    async def test_create_postgresql_connection(self, connection_manager, docker_services):
        """Test creating PostgreSQL connection."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        assert conn_id is not None
        assert connection_manager.has_connection(conn_id)

    @pytest.mark.asyncio
    async def test_create_mysql_connection(self, connection_manager, docker_services):
        """Test creating MySQL connection."""
        config = DOCKER_CONFIGS['mysql']

        conn_id = await connection_manager.create_connection(
            database_type='mysql',
            **config
        )

        assert conn_id is not None
        assert connection_manager.has_connection(conn_id)

    @pytest.mark.asyncio
    async def test_create_mongodb_connection(self, connection_manager, docker_services):
        """Test creating MongoDB connection."""
        config = DOCKER_CONFIGS['mongodb']

        conn_id = await connection_manager.create_connection(
            database_type='mongodb',
            **config
        )

        assert conn_id is not None
        assert connection_manager.has_connection(conn_id)

    @pytest.mark.asyncio
    async def test_create_redis_connection(self, connection_manager, docker_services):
        """Test creating Redis connection."""
        config = DOCKER_CONFIGS['redis']

        conn_id = await connection_manager.create_connection(
            database_type='redis',
            **config
        )

        assert conn_id is not None
        assert connection_manager.has_connection(conn_id)

    @pytest.mark.asyncio
    async def test_get_connection_by_id(self, connection_manager, docker_services):
        """Test retrieving connection by ID."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        connection = connection_manager.get_connection(conn_id)

        assert connection is not None
        assert connection.is_connected()


class TestConnectionManagerMultipleConnections:
    """Test managing multiple connections."""

    @pytest.mark.asyncio
    async def test_create_multiple_connections_same_type(self, connection_manager, docker_services):
        """Test creating multiple connections to same database type."""
        config = DOCKER_CONFIGS['postgresql']

        conn_ids = []
        for i in range(3):
            conn_id = await connection_manager.create_connection(
                database_type='postgresql',
                **config,
                connection_name=f'pg_conn_{i}'
            )
            conn_ids.append(conn_id)

        assert len(conn_ids) == 3
        assert len(set(conn_ids)) == 3  # All unique

        for conn_id in conn_ids:
            assert connection_manager.has_connection(conn_id)

    @pytest.mark.asyncio
    async def test_create_connections_different_types(self, connection_manager, docker_services):
        """Test creating connections to different database types."""
        pg_config = DOCKER_CONFIGS['postgresql']
        mysql_config = DOCKER_CONFIGS['mysql']
        redis_config = DOCKER_CONFIGS['redis']

        pg_conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **pg_config
        )
        mysql_conn_id = await connection_manager.create_connection(
            database_type='mysql',
            **mysql_config
        )
        redis_conn_id = await connection_manager.create_connection(
            database_type='redis',
            **redis_config
        )

        assert all([
            connection_manager.has_connection(pg_conn_id),
            connection_manager.has_connection(mysql_conn_id),
            connection_manager.has_connection(redis_conn_id)
        ])

    @pytest.mark.asyncio
    async def test_list_all_connections(self, connection_manager, docker_services):
        """Test listing all connections."""
        configs = [
            ('postgresql', DOCKER_CONFIGS['postgresql']),
            ('mysql', DOCKER_CONFIGS['mysql']),
            ('redis', DOCKER_CONFIGS['redis'])
        ]

        for db_type, config in configs:
            await connection_manager.create_connection(
                database_type=db_type,
                **config
            )

        connections = connection_manager.list_connections()

        assert len(connections) == 3


class TestConnectionManagerClosing:
    """Test closing connections."""

    @pytest.mark.asyncio
    async def test_close_single_connection(self, connection_manager, docker_services):
        """Test closing a single connection."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        await connection_manager.close_connection(conn_id)

        assert not connection_manager.has_connection(conn_id)

    @pytest.mark.asyncio
    async def test_close_all_connections(self, connection_manager, docker_services):
        """Test closing all connections."""
        configs = [
            ('postgresql', DOCKER_CONFIGS['postgresql']),
            ('mysql', DOCKER_CONFIGS['mysql']),
            ('redis', DOCKER_CONFIGS['redis'])
        ]

        for db_type, config in configs:
            await connection_manager.create_connection(
                database_type=db_type,
                **config
            )

        await connection_manager.close_all()

        connections = connection_manager.list_connections()
        assert len(connections) == 0

    @pytest.mark.asyncio
    async def test_close_nonexistent_connection(self, connection_manager):
        """Test closing a non-existent connection."""
        with pytest.raises(Exception):
            await connection_manager.close_connection('nonexistent_id')


class TestConnectionManagerPoolLimits:
    """Test connection pool limits."""

    @pytest.mark.asyncio
    async def test_respect_max_connections(self, connection_manager, docker_services):
        """Test respecting maximum connection limits."""
        config = DOCKER_CONFIGS['postgresql']

        connection_manager.set_max_connections(3)

        conn_ids = []
        for i in range(3):
            conn_id = await connection_manager.create_connection(
                database_type='postgresql',
                **config,
                connection_name=f'pg_conn_{i}'
            )
            conn_ids.append(conn_id)

        # Try to create 4th connection (should fail or queue)
        with pytest.raises(Exception) as exc_info:
            await connection_manager.create_connection(
                database_type='postgresql',
                **config,
                connection_name='pg_conn_4'
            )

        assert 'limit' in str(exc_info.value).lower() or 'maximum' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connection_available_after_close(self, connection_manager, docker_services):
        """Test connection slot becomes available after closing."""
        config = DOCKER_CONFIGS['postgresql']

        connection_manager.set_max_connections(2)

        # Create 2 connections
        conn_id1 = await connection_manager.create_connection(
            database_type='postgresql',
            **config,
            connection_name='pg_conn_1'
        )
        conn_id2 = await connection_manager.create_connection(
            database_type='postgresql',
            **config,
            connection_name='pg_conn_2'
        )

        # Close one connection
        await connection_manager.close_connection(conn_id1)

        # Should be able to create new connection
        conn_id3 = await connection_manager.create_connection(
            database_type='postgresql',
            **config,
            connection_name='pg_conn_3'
        )

        assert conn_id3 is not None


class TestConnectionManagerReconnection:
    """Test automatic reconnection."""

    @pytest.mark.asyncio
    async def test_automatic_reconnection_on_failure(self, connection_manager, docker_services):
        """Test automatic reconnection when connection is lost."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config,
            auto_reconnect=True
        )

        connection = connection_manager.get_connection(conn_id)

        # Simulate connection loss
        await connection.disconnect()

        # Try to execute query (should trigger reconnection)
        result = await connection.execute("SELECT 1 as value")

        assert result['rows'][0]['value'] == 1
        assert connection.is_connected()

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, connection_manager, docker_services):
        """Test retry logic on transient failures."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config,
            max_retries=3
        )

        connection = connection_manager.get_connection(conn_id)

        # Should succeed with retries
        result = await connection.execute("SELECT 1 as value")

        assert result is not None


class TestConnectionManagerHealthMonitoring:
    """Test health monitoring for connections."""

    @pytest.mark.asyncio
    async def test_health_check_all_connections(self, connection_manager, docker_services):
        """Test health check for all connections."""
        configs = [
            ('postgresql', DOCKER_CONFIGS['postgresql']),
            ('mysql', DOCKER_CONFIGS['mysql']),
            ('redis', DOCKER_CONFIGS['redis'])
        ]

        conn_ids = []
        for db_type, config in configs:
            conn_id = await connection_manager.create_connection(
                database_type=db_type,
                **config
            )
            conn_ids.append(conn_id)

        health_status = await connection_manager.check_all_health()

        assert len(health_status) == 3
        assert all(status['healthy'] for status in health_status.values())

    @pytest.mark.asyncio
    async def test_health_check_single_connection(self, connection_manager, docker_services):
        """Test health check for single connection."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        health = await connection_manager.check_connection_health(conn_id)

        assert health['healthy'] is True
        assert health['connected'] is True

    @pytest.mark.asyncio
    async def test_periodic_health_checks(self, connection_manager, docker_services):
        """Test periodic health checks."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config,
            health_check_interval=1
        )

        # Wait for health check to run
        await asyncio.sleep(1.5)

        health = await connection_manager.check_connection_health(conn_id)

        assert health['healthy'] is True


class TestConnectionManagerMetrics:
    """Test metrics collection."""

    @pytest.mark.asyncio
    async def test_collect_connection_metrics(self, connection_manager, docker_services):
        """Test collecting metrics for all connections."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        # Execute some queries
        connection = connection_manager.get_connection(conn_id)
        for _ in range(5):
            await connection.execute("SELECT 1")

        metrics = connection_manager.get_metrics(conn_id)

        assert 'query_count' in metrics or 'total_queries' in metrics
        assert metrics.get('query_count', 0) >= 5 or metrics.get('total_queries', 0) >= 5

    @pytest.mark.asyncio
    async def test_aggregate_metrics(self, connection_manager, docker_services):
        """Test aggregate metrics across all connections."""
        configs = [
            ('postgresql', DOCKER_CONFIGS['postgresql']),
            ('mysql', DOCKER_CONFIGS['mysql'])
        ]

        for db_type, config in configs:
            await connection_manager.create_connection(
                database_type=db_type,
                **config
            )

        aggregate_metrics = connection_manager.get_aggregate_metrics()

        assert 'total_connections' in aggregate_metrics
        assert aggregate_metrics['total_connections'] == 2


class TestConnectionManagerConcurrency:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_connection_creation(self, connection_manager, docker_services):
        """Test creating connections concurrently."""
        config = DOCKER_CONFIGS['postgresql']

        async def create_conn(index):
            return await connection_manager.create_connection(
                database_type='postgresql',
                **config,
                connection_name=f'pg_conn_{index}'
            )

        # Create 5 connections concurrently
        conn_ids = await asyncio.gather(*[create_conn(i) for i in range(5)])

        assert len(conn_ids) == 5
        assert len(set(conn_ids)) == 5  # All unique

    @pytest.mark.asyncio
    async def test_concurrent_queries_across_connections(self, connection_manager, docker_services):
        """Test executing concurrent queries across multiple connections."""
        config = DOCKER_CONFIGS['postgresql']

        # Create multiple connections
        conn_ids = []
        for i in range(3):
            conn_id = await connection_manager.create_connection(
                database_type='postgresql',
                **config,
                connection_name=f'pg_conn_{i}'
            )
            conn_ids.append(conn_id)

        async def execute_query(conn_id, value):
            connection = connection_manager.get_connection(conn_id)
            result = await connection.execute("SELECT $1 as value", (value,))
            return result['rows'][0]['value']

        # Execute concurrent queries
        tasks = [execute_query(conn_ids[i % 3], i) for i in range(15)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 15
        assert results == list(range(15))


class TestConnectionManagerErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_invalid_database_type(self, connection_manager):
        """Test handling invalid database type."""
        with pytest.raises(Exception) as exc_info:
            await connection_manager.create_connection(
                database_type='invalid_db',
                host='localhost',
                port=5432
            )

        assert 'invalid' in str(exc_info.value).lower() or 'unsupported' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connection_failure(self, connection_manager):
        """Test handling connection failures."""
        with pytest.raises(Exception):
            await connection_manager.create_connection(
                database_type='postgresql',
                host='192.0.2.1',  # Non-routable IP
                port=5432,
                database='test',
                username='postgres',
                password='password',
                timeout=1
            )

    @pytest.mark.asyncio
    async def test_get_nonexistent_connection(self, connection_manager):
        """Test getting non-existent connection."""
        with pytest.raises(Exception) as exc_info:
            connection_manager.get_connection('nonexistent_id')

        assert 'not found' in str(exc_info.value).lower() or 'does not exist' in str(exc_info.value).lower()


class TestConnectionManagerConnectionNaming:
    """Test connection naming functionality."""

    @pytest.mark.asyncio
    async def test_create_connection_with_name(self, connection_manager, docker_services):
        """Test creating connection with custom name."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            connection_name='my_postgres_connection',
            **config
        )

        connection_info = connection_manager.get_connection_info(conn_id)

        assert connection_info['name'] == 'my_postgres_connection'

    @pytest.mark.asyncio
    async def test_get_connection_by_name(self, connection_manager, docker_services):
        """Test retrieving connection by name."""
        config = DOCKER_CONFIGS['postgresql']

        await connection_manager.create_connection(
            database_type='postgresql',
            connection_name='named_connection',
            **config
        )

        connection = connection_manager.get_connection_by_name('named_connection')

        assert connection is not None
        assert connection.is_connected()

    @pytest.mark.asyncio
    async def test_duplicate_connection_names(self, connection_manager, docker_services):
        """Test handling duplicate connection names."""
        config = DOCKER_CONFIGS['postgresql']

        await connection_manager.create_connection(
            database_type='postgresql',
            connection_name='duplicate_name',
            **config
        )

        # Try to create another connection with same name
        with pytest.raises(Exception) as exc_info:
            await connection_manager.create_connection(
                database_type='postgresql',
                connection_name='duplicate_name',
                **config
            )

        assert 'duplicate' in str(exc_info.value).lower() or 'exists' in str(exc_info.value).lower()


class TestConnectionManagerConfiguration:
    """Test connection configuration management."""

    @pytest.mark.asyncio
    async def test_get_connection_config(self, connection_manager, docker_services):
        """Test retrieving connection configuration."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        conn_config = connection_manager.get_connection_config(conn_id)

        assert conn_config['database_type'] == 'postgresql'
        assert conn_config['host'] == config['host']
        assert conn_config['port'] == config['port']

    @pytest.mark.asyncio
    async def test_update_connection_config(self, connection_manager, docker_services):
        """Test updating connection configuration."""
        config = DOCKER_CONFIGS['postgresql']

        conn_id = await connection_manager.create_connection(
            database_type='postgresql',
            **config
        )

        # Update configuration
        await connection_manager.update_connection_config(
            conn_id,
            max_retries=5,
            timeout=30
        )

        conn_config = connection_manager.get_connection_config(conn_id)

        assert conn_config['max_retries'] == 5
        assert conn_config['timeout'] == 30
