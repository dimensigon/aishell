"""
Comprehensive Docker Integration Tests for MCP Clients

Tests all database clients with Docker containers:
- PostgreSQL with enhanced features
- MySQL with enhanced features
- MongoDB with enhanced features
- Redis with enhanced features
- SQLite (no Docker needed)

Includes tests for:
- Connection pooling
- Health checks
- Automatic reconnection
- Retry logic
- Advanced features
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any

from src.mcp_clients.base import ConnectionConfig
from src.mcp_clients.postgresql_enhanced import PostgreSQLEnhancedClient
from src.mcp_clients.mysql_enhanced import MySQLEnhancedClient
from src.mcp_clients.mongodb_enhanced import MongoDBEnhancedClient
from src.mcp_clients.redis_enhanced import RedisEnhancedClient
from src.mcp_clients.sqlite_client import SQLiteClient
from src.mcp_clients.docker_integration import DockerIntegrationHelper
from src.mcp_clients.enhanced_manager import EnhancedConnectionManager


# Pytest fixtures

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def wait_for_databases():
    """Wait for all Docker databases to be ready"""
    # Wait for PostgreSQL
    await DockerIntegrationHelper.wait_for_database('postgresql', max_wait_time=30)

    # Wait for MySQL
    await DockerIntegrationHelper.wait_for_database('mysql', max_wait_time=60, port=3306)

    # Wait for MongoDB
    await DockerIntegrationHelper.wait_for_database('mongodb', max_wait_time=60, port=27017)

    # Wait for Redis
    await DockerIntegrationHelper.wait_for_database('redis', max_wait_time=30, port=6379)

    yield True


# PostgreSQL Tests

@pytest.mark.asyncio
async def test_postgresql_basic_connection(wait_for_databases):
    """Test basic PostgreSQL connection"""
    config = ConnectionConfig(
        host='localhost',
        port=5432,
        database='postgres',
        username='postgres',
        password='MyPostgresPass123'
    )

    client = PostgreSQLEnhancedClient()

    try:
        await client.connect(config)
        assert client.is_connected

        # Test simple query
        result = await client.execute_query("SELECT 1 as test")
        assert result.rows == [(1,)]

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_postgresql_retry_logic(wait_for_databases):
    """Test PostgreSQL retry with exponential backoff"""
    config = ConnectionConfig(
        host='localhost',
        port=5432,
        database='postgres',
        username='postgres',
        password='MyPostgresPass123'
    )

    client = PostgreSQLEnhancedClient()
    client.configure_retry(max_retries=3, base_delay=0.1, max_delay=1.0)

    try:
        await client.connect(config)

        # Test query with retry
        result = await client.execute_query_with_retry(
            "SELECT pg_sleep(0.1); SELECT 'success' as status"
        )
        assert result.rows is not None

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_postgresql_listen_notify(wait_for_databases):
    """Test PostgreSQL LISTEN/NOTIFY"""
    config = ConnectionConfig(
        host='localhost',
        port=5432,
        database='postgres',
        username='postgres',
        password='MyPostgresPass123'
    )

    client = PostgreSQLEnhancedClient()

    try:
        await client.connect(config)

        # Set up notification handler
        received_notifications = []

        async def handler(channel, payload):
            received_notifications.append({'channel': channel, 'payload': payload})

        await client.listen('test_channel', handler)

        # Send notification
        await client.notify('test_channel', 'test_message')

        # Wait for notification
        await asyncio.sleep(0.5)

        notifications = client.get_notifications('test_channel')
        assert len(notifications) > 0

        await client.unlisten('test_channel')

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_postgresql_health_check(wait_for_databases):
    """Test PostgreSQL detailed health check"""
    config = ConnectionConfig(
        host='localhost',
        port=5432,
        database='postgres',
        username='postgres',
        password='MyPostgresPass123'
    )

    client = PostgreSQLEnhancedClient()

    try:
        await client.connect(config)

        health = await client.health_check_detailed()

        assert health['connected'] is True
        assert health['ping_successful'] is True
        assert 'metrics' in health
        assert 'active_connections' in health

    finally:
        await client.disconnect()


# MySQL Tests

@pytest.mark.asyncio
async def test_mysql_basic_connection(wait_for_databases):
    """Test basic MySQL connection"""
    config = ConnectionConfig(
        host='localhost',
        port=3306,
        database='test_integration_db',
        username='root',
        password='MyMySQLPass123'
    )

    client = MySQLEnhancedClient()

    try:
        await client.connect(config)
        assert client.is_connected

        result = await client.execute_query("SELECT 1 as test")
        assert result.rows == [(1,)]

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_mysql_prepared_statements(wait_for_databases):
    """Test MySQL prepared statements"""
    config = ConnectionConfig(
        host='localhost',
        port=3306,
        database='test_integration_db',
        username='root',
        password='MyMySQLPass123'
    )

    client = MySQLEnhancedClient()

    try:
        await client.connect(config)

        # Create test table
        await client.execute_ddl("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INT PRIMARY KEY,
                name VARCHAR(100)
            )
        """)

        # Prepare statement
        await client.prepare('insert_user', 'INSERT INTO test_users (id, name) VALUES (?, ?)')

        # Execute prepared statement
        await client.execute_prepared('insert_user', (1, 'Test User'))

        # Verify
        result = await client.execute_query('SELECT * FROM test_users WHERE id = 1')
        assert len(result.rows) == 1

        # Cleanup
        await client.execute_ddl('DROP TABLE test_users')

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_mysql_transactions(wait_for_databases):
    """Test MySQL transaction support"""
    config = ConnectionConfig(
        host='localhost',
        port=3306,
        database='test_integration_db',
        username='root',
        password='MyMySQLPass123'
    )

    client = MySQLEnhancedClient()

    try:
        await client.connect(config)

        # Create test table
        await client.execute_ddl("""
            CREATE TABLE IF NOT EXISTS test_transactions (
                id INT PRIMARY KEY,
                value VARCHAR(100)
            )
        """)

        # Test transaction commit
        await client.begin_transaction()
        await client.execute_query("INSERT INTO test_transactions VALUES (1, 'committed')")
        await client.commit()

        result = await client.execute_query("SELECT * FROM test_transactions WHERE id = 1")
        assert len(result.rows) == 1

        # Test transaction rollback
        await client.begin_transaction()
        await client.execute_query("INSERT INTO test_transactions VALUES (2, 'rolled_back')")
        await client.rollback()

        result = await client.execute_query("SELECT * FROM test_transactions WHERE id = 2")
        assert len(result.rows) == 0

        # Cleanup
        await client.execute_ddl('DROP TABLE test_transactions')

    finally:
        await client.disconnect()


# MongoDB Tests

@pytest.mark.asyncio
async def test_mongodb_basic_connection(wait_for_databases):
    """Test basic MongoDB connection"""
    config = ConnectionConfig(
        host='localhost',
        port=27017,
        database='test_integration_db',
        username='admin',
        password='MyMongoPass123'
    )

    client = MongoDBEnhancedClient()

    try:
        await client.connect(config)
        assert client.is_connected

        # Test insert
        query = {
            'operation': 'insert_one',
            'collection': 'test_collection',
            'document': {'name': 'test', 'value': 123}
        }

        result = await client._execute_query_impl(str(query), None)
        assert result['rowcount'] > 0

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_mongodb_gridfs(wait_for_databases):
    """Test MongoDB GridFS file storage"""
    config = ConnectionConfig(
        host='localhost',
        port=27017,
        database='test_integration_db',
        username='admin',
        password='MyMongoPass123'
    )

    client = MongoDBEnhancedClient()

    try:
        await client.connect(config)

        # Upload file
        test_data = b"This is test file content"
        file_id = await client.gridfs_upload('test_file.txt', test_data)

        assert file_id is not None

        # Download file
        downloaded = await client.gridfs_download(file_id)
        assert downloaded == test_data

        # List files
        files = await client.gridfs_list()
        assert len(files) > 0

        # Delete file
        await client.gridfs_delete(file_id)

    finally:
        await client.disconnect()


# Redis Tests

@pytest.mark.asyncio
async def test_redis_basic_connection(wait_for_databases):
    """Test basic Redis connection"""
    config = ConnectionConfig(
        host='localhost',
        port=6379,
        database='0',
        username='',
        password='MyRedisPass123'
    )

    client = RedisEnhancedClient()

    try:
        await client.connect(config)
        assert client.is_connected

        # Test set/get
        await client.cache_set('test_key', 'test_value')
        value = await client.cache_get('test_key')
        assert value == 'test_value'

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_redis_streams(wait_for_databases):
    """Test Redis Streams"""
    config = ConnectionConfig(
        host='localhost',
        port=6379,
        database='0',
        username='',
        password='MyRedisPass123'
    )

    client = RedisEnhancedClient()

    try:
        await client.connect(config)

        # Add to stream
        message_id = await client.xadd('test_stream', {'field1': 'value1', 'field2': 'value2'})
        assert message_id is not None

        # Read from stream
        messages = await client.xread({'test_stream': '0'}, count=10)
        assert len(messages) > 0

        # Get stream length
        length = await client.xlen('test_stream')
        assert length > 0

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_redis_lua_scripts(wait_for_databases):
    """Test Redis Lua scripts"""
    config = ConnectionConfig(
        host='localhost',
        port=6379,
        database='0',
        username='',
        password='MyRedisPass123'
    )

    client = RedisEnhancedClient()

    try:
        await client.connect(config)

        # Register script
        script = """
        local key = KEYS[1]
        local value = ARGV[1]
        redis.call('SET', key, value)
        return redis.call('GET', key)
        """

        await client.register_script('test_script', script)

        # Execute script
        result = await client.execute_script('test_script', keys=['lua_test_key'], args=['lua_test_value'])
        assert result == 'lua_test_value'

    finally:
        await client.disconnect()


# SQLite Tests (No Docker needed)

@pytest.mark.asyncio
async def test_sqlite_basic_operations():
    """Test basic SQLite operations"""
    db_path = '/tmp/test_sqlite.db'

    config = ConnectionConfig(
        host=db_path,
        port=0,
        database='sqlite',
        username='',
        password=''
    )

    client = SQLiteClient()

    try:
        await client.connect(config)
        assert client.is_connected

        # Create table
        await client.execute_ddl("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        # Insert data
        await client.execute_query(
            "INSERT INTO test_table (id, name) VALUES (?, ?)",
            (1, 'Test Name')
        )

        # Query data
        result = await client.execute_query("SELECT * FROM test_table WHERE id = ?", (1,))
        assert len(result.rows) == 1
        assert result.rows[0][1] == 'Test Name'

        # Get database stats
        stats = await client.get_database_stats()
        assert stats['table_count'] > 0

    finally:
        await client.disconnect()
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_sqlite_wal_mode():
    """Test SQLite WAL mode"""
    db_path = '/tmp/test_wal.db'

    config = ConnectionConfig(
        host=db_path,
        port=0,
        database='sqlite',
        username='',
        password=''
    )

    client = SQLiteClient()

    try:
        await client.connect(config)

        # Check WAL mode is enabled
        stats = await client.get_database_stats()
        assert stats['journal_mode'] == 'wal'

    finally:
        await client.disconnect()
        Path(db_path).unlink(missing_ok=True)


# Enhanced Manager Tests

@pytest.mark.asyncio
async def test_enhanced_manager_health_monitoring(wait_for_databases):
    """Test enhanced manager with health monitoring"""
    manager = EnhancedConnectionManager(
        max_connections=10,
        health_check_interval=5,
        auto_reconnect=True
    )

    try:
        # Create PostgreSQL connection
        pg_config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        conn_id = await manager.create_connection('test_pg', 'postgresql', pg_config)
        assert conn_id == 'test_pg'

        # Get connection health
        health = await manager.get_connection_health('test_pg')
        assert health['connected'] is True

        # Start health monitoring
        await manager.start_health_monitoring()

        # Wait a bit
        await asyncio.sleep(1)

        # Stop health monitoring
        await manager.stop_health_monitoring()

        # Get pool stats
        stats = manager.get_pool_stats()
        assert stats['current_connections'] == 1
        assert stats['auto_reconnect_enabled'] is True

    finally:
        await manager.close_all()


@pytest.mark.asyncio
async def test_enhanced_manager_multiple_databases(wait_for_databases):
    """Test managing multiple database types"""
    manager = EnhancedConnectionManager(max_connections=20)

    try:
        # PostgreSQL
        pg_config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )
        await manager.create_connection('pg', 'postgresql', pg_config)

        # MySQL
        mysql_config = ConnectionConfig(
            host='localhost',
            port=3306,
            database='test_integration_db',
            username='root',
            password='MyMySQLPass123'
        )
        await manager.create_connection('mysql', 'mysql', mysql_config)

        # MongoDB
        mongo_config = ConnectionConfig(
            host='localhost',
            port=27017,
            database='test_integration_db',
            username='admin',
            password='MyMongoPass123'
        )
        await manager.create_connection('mongo', 'mongodb', mongo_config)

        # Redis
        redis_config = ConnectionConfig(
            host='localhost',
            port=6379,
            database='0',
            username='',
            password='MyRedisPass123'
        )
        await manager.create_connection('redis', 'redis', redis_config)

        # Get all connections
        connections = manager.list_connections()
        assert len(connections) == 4

        # Health check all
        health_status = await manager.health_check_all()
        assert len(health_status) == 4
        assert all(h.get('connected', False) for h in health_status.values())

    finally:
        await manager.close_all()


@pytest.mark.asyncio
async def test_connection_pooling(wait_for_databases):
    """Test connection pool limits and stats"""
    manager = EnhancedConnectionManager(max_connections=3)

    try:
        # Create connections up to limit
        for i in range(3):
            config = ConnectionConfig(
                host='localhost',
                port=5432,
                database='postgres',
                username='postgres',
                password='MyPostgresPass123'
            )
            await manager.create_connection(f'pg_{i}', 'postgresql', config)

        stats = manager.get_stats()
        assert stats['total_connections'] == 3
        assert stats['utilization'] == 1.0

        # Try to exceed limit
        with pytest.raises(Exception):
            config = ConnectionConfig(
                host='localhost',
                port=5432,
                database='postgres',
                username='postgres',
                password='MyPostgresPass123'
            )
            await manager.create_connection('pg_exceed', 'postgresql', config)

        # Resize pool
        await manager.resize_pool(5)

        stats = manager.get_pool_stats()
        assert stats['max_connections'] == 5

    finally:
        await manager.close_all()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
