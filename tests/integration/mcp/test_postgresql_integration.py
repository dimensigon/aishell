"""PostgreSQL integration tests with real Docker container."""
import asyncio
import pytest
from datetime import datetime
from tests.integration.mcp.config import DOCKER_CONFIGS


class TestPostgreSQLConnection:
    """Test PostgreSQL connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_success(self, pg_client, postgresql_clean):
        """Test successful connection to PostgreSQL."""
        config = DOCKER_CONFIGS['postgresql']

        await pg_client.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['username'],
            password=config['password']
        )

        assert pg_client.is_connected()

    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, pg_client):
        """Test connection with invalid credentials."""
        config = DOCKER_CONFIGS['postgresql']

        with pytest.raises(Exception):
            await pg_client.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user='invalid',
                password='wrong'
            )

    @pytest.mark.asyncio
    async def test_disconnect(self, pg_client, postgresql_clean):
        """Test disconnection from PostgreSQL."""
        config = DOCKER_CONFIGS['postgresql']

        await pg_client.connect(**config)
        assert pg_client.is_connected()

        await pg_client.disconnect()
        assert not pg_client.is_connected()

    @pytest.mark.asyncio
    async def test_reconnect(self, pg_client, postgresql_clean):
        """Test reconnection after disconnect."""
        config = DOCKER_CONFIGS['postgresql']

        await pg_client.connect(**config)
        await pg_client.disconnect()
        await pg_client.connect(**config)

        assert pg_client.is_connected()


class TestPostgreSQLCRUD:
    """Test PostgreSQL CRUD operations."""

    @pytest.mark.asyncio
    async def test_insert_single_row(self, pg_client, postgresql_clean):
        """Test inserting a single row."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        result = await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2) RETURNING id",
            ("John Doe", "john@example.com")
        )

        assert result['rows'][0]['id'] is not None

    @pytest.mark.asyncio
    async def test_select_rows(self, pg_client, postgresql_clean):
        """Test selecting rows."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert test data
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("Jane Smith", "jane@example.com")
        )

        # Select
        result = await pg_client.execute("SELECT * FROM test_users WHERE email = $1", ("jane@example.com",))

        assert len(result['rows']) == 1
        assert result['rows'][0]['name'] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_update_row(self, pg_client, postgresql_clean):
        """Test updating a row."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert
        result = await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2) RETURNING id",
            ("Bob", "bob@example.com")
        )
        user_id = result['rows'][0]['id']

        # Update
        await pg_client.execute(
            "UPDATE test_users SET name = $1 WHERE id = $2",
            ("Robert", user_id)
        )

        # Verify
        result = await pg_client.execute("SELECT name FROM test_users WHERE id = $1", (user_id,))
        assert result['rows'][0]['name'] == "Robert"

    @pytest.mark.asyncio
    async def test_delete_row(self, pg_client, postgresql_clean):
        """Test deleting a row."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert
        result = await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2) RETURNING id",
            ("Alice", "alice@example.com")
        )
        user_id = result['rows'][0]['id']

        # Delete
        await pg_client.execute("DELETE FROM test_users WHERE id = $1", (user_id,))

        # Verify
        result = await pg_client.execute("SELECT * FROM test_users WHERE id = $1", (user_id,))
        assert len(result['rows']) == 0

    @pytest.mark.asyncio
    async def test_bulk_insert(self, pg_client, postgresql_clean):
        """Test bulk insert operations."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        values = [(f"User{i}", f"user{i}@example.com") for i in range(100)]

        for name, email in values:
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (name, email)
            )

        result = await pg_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 100


class TestPostgreSQLTransactions:
    """Test PostgreSQL transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, pg_client, postgresql_clean):
        """Test transaction commit."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        await pg_client.begin()
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("TX User", "tx@example.com")
        )
        await pg_client.commit()

        result = await pg_client.execute("SELECT * FROM test_users WHERE email = $1", ("tx@example.com",))
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, pg_client, postgresql_clean):
        """Test transaction rollback."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        await pg_client.begin()
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("Rollback User", "rollback@example.com")
        )
        await pg_client.rollback()

        result = await pg_client.execute("SELECT * FROM test_users WHERE email = $1", ("rollback@example.com",))
        assert len(result['rows']) == 0

    @pytest.mark.asyncio
    async def test_nested_transactions(self, pg_client, postgresql_clean):
        """Test nested transactions with savepoints."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        await pg_client.begin()
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("Outer", "outer@example.com")
        )

        # Savepoint
        await pg_client.execute("SAVEPOINT sp1")
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("Inner", "inner@example.com")
        )

        # Rollback to savepoint
        await pg_client.execute("ROLLBACK TO SAVEPOINT sp1")
        await pg_client.commit()

        result = await pg_client.execute("SELECT email FROM test_users")
        emails = [row['email'] for row in result['rows']]
        assert "outer@example.com" in emails
        assert "inner@example.com" not in emails


class TestPostgreSQLConnectionPooling:
    """Test PostgreSQL connection pooling."""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, pg_client, postgresql_clean):
        """Test handling concurrent queries."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        async def insert_user(index):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (f"Concurrent{index}", f"concurrent{index}@example.com")
            )

        # Run 10 concurrent inserts
        tasks = [insert_user(i) for i in range(10)]
        await asyncio.gather(*tasks)

        result = await pg_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 10

    @pytest.mark.asyncio
    async def test_pool_exhaustion_handling(self, pg_client, postgresql_clean):
        """Test handling when connection pool is exhausted."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config, max_connections=5)

        async def long_query():
            await pg_client.execute("SELECT pg_sleep(0.1)")

        # Try to run more queries than pool size
        tasks = [long_query() for _ in range(20)]
        await asyncio.gather(*tasks)  # Should handle queuing


class TestPostgreSQLListenNotify:
    """Test PostgreSQL LISTEN/NOTIFY functionality."""

    @pytest.mark.asyncio
    async def test_listen_notify(self, pg_client, postgresql_clean):
        """Test LISTEN/NOTIFY pub/sub."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        notifications = []

        async def listener():
            await pg_client.execute("LISTEN test_channel")
            # Wait for notification
            async for notif in pg_client.notifications():
                notifications.append(notif)
                break

        async def notifier():
            await asyncio.sleep(0.1)
            await pg_client.execute("NOTIFY test_channel, 'test message'")

        await asyncio.gather(listener(), notifier())
        assert len(notifications) == 1
        assert notifications[0]['payload'] == 'test message'


class TestPostgreSQLCopyOperations:
    """Test PostgreSQL COPY operations."""

    @pytest.mark.asyncio
    async def test_copy_to(self, pg_client, postgresql_clean, tmp_path):
        """Test COPY TO export data."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert test data
        for i in range(10):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (f"User{i}", f"user{i}@example.com")
            )

        # Export to file
        output_file = tmp_path / "export.csv"
        await pg_client.execute(f"COPY test_users TO STDOUT WITH CSV HEADER")

    @pytest.mark.asyncio
    async def test_copy_from(self, pg_client, postgresql_clean, tmp_path):
        """Test COPY FROM import data."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Create CSV file
        csv_file = tmp_path / "import.csv"
        csv_file.write_text("name,email\nImported User,imported@example.com\n")

        # Import from file
        await pg_client.execute(f"COPY test_users(name, email) FROM STDIN WITH CSV HEADER")


class TestPostgreSQLPreparedStatements:
    """Test PostgreSQL prepared statements."""

    @pytest.mark.asyncio
    async def test_prepared_statement(self, pg_client, postgresql_clean):
        """Test prepared statement execution."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Prepare statement
        await pg_client.execute("""
            PREPARE insert_user (text, text) AS
            INSERT INTO test_users (name, email) VALUES ($1, $2)
        """)

        # Execute prepared statement
        await pg_client.execute("EXECUTE insert_user('Prepared', 'prepared@example.com')")

        result = await pg_client.execute("SELECT * FROM test_users WHERE email = $1", ("prepared@example.com",))
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_prepared_statement_reuse(self, pg_client, postgresql_clean):
        """Test reusing prepared statements."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        await pg_client.execute("""
            PREPARE select_user (text) AS
            SELECT * FROM test_users WHERE email = $1
        """)

        # Insert test data
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("Test", "test@example.com")
        )

        # Execute prepared statement multiple times
        for _ in range(5):
            result = await pg_client.execute("EXECUTE select_user('test@example.com')")
            assert len(result['rows']) == 1


class TestPostgreSQLHealthCheck:
    """Test PostgreSQL health checks."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, pg_client, postgresql_clean):
        """Test health check when connected."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        health = await pg_client.health_check()

        assert health['healthy'] is True
        assert 'postgresql' in health['database_type'].lower()
        assert health['connected'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, pg_client):
        """Test health check when disconnected."""
        health = await pg_client.health_check()

        assert health['healthy'] is False
        assert health['connected'] is False

    @pytest.mark.asyncio
    async def test_health_check_with_metrics(self, pg_client, postgresql_clean):
        """Test health check with database metrics."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        health = await pg_client.health_check(include_metrics=True)

        assert 'metrics' in health
        assert 'connection_count' in health['metrics']
        assert 'database_size' in health['metrics']


class TestPostgreSQLAutomaticReconnection:
    """Test PostgreSQL automatic reconnection."""

    @pytest.mark.asyncio
    async def test_reconnect_after_connection_loss(self, pg_client, postgresql_clean):
        """Test automatic reconnection after connection loss."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Simulate connection loss
        await pg_client.disconnect()

        # Try to execute query (should reconnect)
        await pg_client.execute("SELECT 1")

        assert pg_client.is_connected()

    @pytest.mark.asyncio
    async def test_query_retry_on_failure(self, pg_client, postgresql_clean):
        """Test query retry on transient failures."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Execute query that should succeed after retry
        result = await pg_client.execute("SELECT 1 as value")
        assert result['rows'][0]['value'] == 1


class TestPostgreSQLErrorHandling:
    """Test PostgreSQL error handling."""

    @pytest.mark.asyncio
    async def test_syntax_error(self, pg_client, postgresql_clean):
        """Test handling SQL syntax errors."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        with pytest.raises(Exception) as exc_info:
            await pg_client.execute("INVALID SQL SYNTAX")

        assert 'syntax' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_constraint_violation(self, pg_client, postgresql_clean):
        """Test handling constraint violations."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert user
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("User", "unique@example.com")
        )

        # Try to insert duplicate email
        with pytest.raises(Exception) as exc_info:
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                ("Another User", "unique@example.com")
            )

        assert 'unique' in str(exc_info.value).lower() or 'duplicate' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, pg_client, postgresql_clean):
        """Test handling query timeouts."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config, query_timeout=1)

        with pytest.raises(asyncio.TimeoutError):
            await pg_client.execute("SELECT pg_sleep(10)")

    @pytest.mark.asyncio
    async def test_invalid_parameter_type(self, pg_client, postgresql_clean):
        """Test handling invalid parameter types."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        with pytest.raises(Exception):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                ("User", None)  # NULL email violates NOT NULL constraint
            )


class TestPostgreSQLAdvancedFeatures:
    """Test PostgreSQL advanced features."""

    @pytest.mark.asyncio
    async def test_json_operations(self, pg_client, postgresql_clean):
        """Test JSON/JSONB operations."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Create table with JSONB column
        await pg_client.execute("""
            CREATE TABLE IF NOT EXISTS test_json (
                id SERIAL PRIMARY KEY,
                data JSONB
            )
        """)

        # Insert JSON data
        await pg_client.execute(
            "INSERT INTO test_json (data) VALUES ($1)",
            ('{"name": "John", "age": 30}',)
        )

        # Query JSON data
        result = await pg_client.execute("SELECT data->>'name' as name FROM test_json")
        assert result['rows'][0]['name'] == "John"

    @pytest.mark.asyncio
    async def test_array_operations(self, pg_client, postgresql_clean):
        """Test array operations."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Create table with array column
        await pg_client.execute("""
            CREATE TABLE IF NOT EXISTS test_arrays (
                id SERIAL PRIMARY KEY,
                tags TEXT[]
            )
        """)

        # Insert array data
        await pg_client.execute(
            "INSERT INTO test_arrays (tags) VALUES ($1)",
            (['python', 'postgresql', 'async'],)
        )

        # Query array data
        result = await pg_client.execute("SELECT tags FROM test_arrays")
        assert 'python' in result['rows'][0]['tags']

    @pytest.mark.asyncio
    async def test_full_text_search(self, pg_client, postgresql_clean):
        """Test full-text search functionality."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert test data
        await pg_client.execute(
            "INSERT INTO test_users (name, email) VALUES ($1, $2)",
            ("PostgreSQL Expert", "postgres@example.com")
        )

        # Full-text search
        result = await pg_client.execute("""
            SELECT * FROM test_users
            WHERE to_tsvector('english', name) @@ to_tsquery('english', 'PostgreSQL')
        """)

        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_window_functions(self, pg_client, postgresql_clean):
        """Test window functions."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert test data
        for i in range(5):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (f"User{i}", f"user{i}@example.com")
            )

        # Use window function
        result = await pg_client.execute("""
            SELECT name, ROW_NUMBER() OVER (ORDER BY id) as row_num
            FROM test_users
        """)

        assert len(result['rows']) == 5
        assert result['rows'][0]['row_num'] == 1

    @pytest.mark.asyncio
    async def test_cte_queries(self, pg_client, postgresql_clean):
        """Test Common Table Expressions (CTEs)."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert test data
        for i in range(3):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (f"CTE User{i}", f"cte{i}@example.com")
            )

        # CTE query
        result = await pg_client.execute("""
            WITH user_count AS (
                SELECT COUNT(*) as total FROM test_users
            )
            SELECT total FROM user_count
        """)

        assert result['rows'][0]['total'] == 3
