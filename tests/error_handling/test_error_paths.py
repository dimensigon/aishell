"""
Error path tests for database clients and core functionality.
Tests connection failures, timeouts, retries, and error recovery.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
from datetime import datetime


class TestConnectionErrors:
    """Test connection failure scenarios"""

    async def test_connection_timeout(self):
        """Test connection timeout handling"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='unreachable-host.local',
            database='test',
            user='postgres',
            password='password',
            timeout=0.001
        )

        with pytest.raises((asyncio.TimeoutError, ConnectionError)):
            await client.connect()

    async def test_connection_refused(self):
        """Test connection refused error"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            port=9999,  # Non-existent port
            database='test',
            user='postgres',
            password='password'
        )

        with pytest.raises(ConnectionError):
            await client.connect()

    async def test_invalid_credentials(self):
        """Test authentication failure"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        with patch('asyncpg.create_pool') as mock_pool:
            mock_pool.side_effect = Exception("authentication failed")

            client = PostgreSQLClient(
                host='localhost',
                database='test',
                user='invalid',
                password='wrong'
            )

            with pytest.raises(Exception, match="authentication"):
                await client.connect()

    async def test_database_not_exist(self):
        """Test connecting to non-existent database"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        with patch('asyncpg.create_pool') as mock_pool:
            mock_pool.side_effect = Exception("database does not exist")

            client = PostgreSQLClient(
                host='localhost',
                database='nonexistent',
                user='postgres',
                password='password'
            )

            with pytest.raises(Exception, match="does not exist"):
                await client.connect()

    async def test_network_partition_during_query(self):
        """Test network failure during query execution"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.fetch = AsyncMock(
            side_effect=ConnectionError("Network unreachable")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(ConnectionError, match="Network unreachable"):
            await client.execute("SELECT * FROM table")

    async def test_connection_pool_exhaustion(self):
        """Test connection pool exhaustion"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password',
            max_pool_size=2
        )

        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            side_effect=asyncio.TimeoutError("Pool exhausted")
        )

        with pytest.raises(asyncio.TimeoutError, match="Pool exhausted"):
            await client.execute("SELECT 1")

    async def test_automatic_reconnection(self):
        """Test automatic reconnection after connection loss"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password',
            auto_reconnect=True
        )

        conn = AsyncMock()
        # First call fails, second succeeds
        conn.fetch = AsyncMock(
            side_effect=[
                ConnectionError("Connection lost"),
                [{'result': 1}]
            ]
        )

        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        # Should retry and succeed
        result = await client.execute_with_retry("SELECT 1", max_retries=2)
        assert result[0]['result'] == 1


class TestQueryErrors:
    """Test query execution errors"""

    async def test_syntax_error(self):
        """Test SQL syntax error"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.fetch = AsyncMock(
            side_effect=Exception("syntax error at or near")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="syntax error"):
            await client.execute("SLECT * FROM table")

    async def test_table_not_exist(self):
        """Test query on non-existent table"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.fetch = AsyncMock(
            side_effect=Exception("relation does not exist")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="does not exist"):
            await client.execute("SELECT * FROM nonexistent_table")

    async def test_column_not_exist(self):
        """Test query referencing non-existent column"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.fetch = AsyncMock(
            side_effect=Exception("column does not exist")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="column does not exist"):
            await client.execute("SELECT invalid_column FROM table")

    async def test_permission_denied(self):
        """Test query without sufficient permissions"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='readonly_user',
            password='password'
        )

        conn = AsyncMock()
        conn.execute = AsyncMock(
            side_effect=Exception("permission denied")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="permission denied"):
            await client.execute("DROP TABLE important_table")

    async def test_deadlock_detected(self):
        """Test deadlock detection and handling"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.execute = AsyncMock(
            side_effect=Exception("deadlock detected")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="deadlock"):
            await client.execute("UPDATE table SET value = 1 WHERE id = 1")

    async def test_query_timeout(self):
        """Test query execution timeout"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password',
            query_timeout=0.1
        )

        conn = AsyncMock()

        async def slow_query(*args, **kwargs):
            await asyncio.sleep(1)
            return []

        conn.fetch = slow_query
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(asyncio.TimeoutError):
            await client.execute_with_timeout(
                "SELECT pg_sleep(10)",
                timeout=0.1
            )


class TestTransactionErrors:
    """Test transaction error scenarios"""

    async def test_transaction_rollback_on_error(self):
        """Test transaction rollback on error"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.execute = AsyncMock(
            side_effect=[
                None,  # BEGIN
                None,  # First statement succeeds
                Exception("constraint violation"),  # Second fails
                None   # ROLLBACK
            ]
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="constraint violation"):
            async with client.transaction():
                await conn.execute("INSERT INTO table VALUES (1)")
                await conn.execute("INSERT INTO table VALUES (1)")  # Duplicate

        # Verify rollback was called
        calls = [str(call) for call in conn.execute.call_args_list]
        assert any('ROLLBACK' in str(call) for call in calls)

    async def test_nested_transaction_savepoint(self):
        """Test nested transaction savepoints"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        savepoint_count = 0

        def execute_mock(query):
            nonlocal savepoint_count
            if 'SAVEPOINT' in query:
                savepoint_count += 1
            return AsyncMock()

        conn.execute = execute_mock
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        async with client.transaction():
            async with client.transaction():  # Nested - should use savepoint
                pass

        assert savepoint_count > 0

    async def test_transaction_timeout(self):
        """Test transaction timeout"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password',
            transaction_timeout=0.1
        )

        conn = AsyncMock()

        async def long_transaction(*args, **kwargs):
            await asyncio.sleep(1)

        conn.execute = long_transaction
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(asyncio.TimeoutError):
            async with client.transaction(timeout=0.1):
                await conn.execute("SELECT pg_sleep(10)")


class TestResourceExhaustion:
    """Test resource exhaustion scenarios"""

    async def test_memory_exhaustion_large_result(self):
        """Test handling memory exhaustion from large results"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.fetch = AsyncMock(
            side_effect=MemoryError("Cannot allocate memory")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(MemoryError):
            await client.execute("SELECT * FROM huge_table")

    async def test_disk_space_exhaustion(self):
        """Test handling disk space exhaustion"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        conn.execute = AsyncMock(
            side_effect=Exception("No space left on device")
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        with pytest.raises(Exception, match="No space left"):
            await client.execute("INSERT INTO table SELECT * FROM huge_table")

    async def test_too_many_connections(self):
        """Test max_connections limit"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        with patch('asyncpg.create_pool') as mock_pool:
            mock_pool.side_effect = Exception("too many connections")

            client = PostgreSQLClient(
                host='localhost',
                database='test',
                user='postgres',
                password='password'
            )

            with pytest.raises(Exception, match="too many connections"):
                await client.connect()

    async def test_statement_timeout_recovery(self):
        """Test recovery from statement timeout"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password'
        )

        conn = AsyncMock()
        # First call times out, second succeeds
        conn.fetch = AsyncMock(
            side_effect=[
                Exception("statement timeout"),
                [{'result': 1}]
            ]
        )
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        # Should retry after timeout
        result = await client.execute_with_retry(
            "SELECT * FROM slow_table",
            max_retries=2
        )
        assert result[0]['result'] == 1


class TestGracefulDegradation:
    """Test graceful degradation scenarios"""

    async def test_fallback_to_readonly_replica(self):
        """Test falling back to read-only replica on primary failure"""
        from src.mcp_clients.manager_extended import MCPClientManager

        manager = MCPClientManager()

        primary_client = AsyncMock()
        primary_client.execute = AsyncMock(
            side_effect=ConnectionError("Primary unavailable")
        )

        replica_client = AsyncMock()
        replica_client.execute = AsyncMock(return_value=[{'result': 1}])

        manager.primary_client = primary_client
        manager.replica_client = replica_client

        # Should fallback to replica
        result = await manager.execute_with_fallback("SELECT * FROM table")
        assert result[0]['result'] == 1

    async def test_cache_fallback_on_database_error(self):
        """Test using cache when database is unavailable"""
        from src.performance.cache_extended import CacheFallback

        cache = CacheFallback()
        cache.set("SELECT 1", [{'result': 'cached'}])

        async def failing_query():
            raise ConnectionError("Database unavailable")

        # Should return cached result
        result = await cache.execute_with_fallback(
            "SELECT 1",
            failing_query,
            use_cache=True
        )
        assert result[0]['result'] == 'cached'

    async def test_partial_result_on_timeout(self):
        """Test returning partial results on timeout"""
        from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended as PostgreSQLClient

        client = PostgreSQLClient(
            host='localhost',
            database='test',
            user='postgres',
            password='password',
            partial_results=True
        )

        conn = AsyncMock()
        partial_data = [{'id': i} for i in range(100)]

        async def partial_fetch(*args, **kwargs):
            await asyncio.sleep(0.05)
            return partial_data

        conn.fetch = partial_fetch
        client.pool = AsyncMock()
        client.pool.acquire = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn))
        )

        # Should return partial results even if timeout occurs
        result = await client.execute_with_partial_results(
            "SELECT * FROM large_table",
            timeout=0.1
        )
        assert len(result) > 0
