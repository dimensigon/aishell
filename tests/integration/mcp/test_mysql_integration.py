"""MySQL integration tests with real Docker container."""
import asyncio
import pytest
from tests.integration.mcp.config import DOCKER_CONFIGS


class TestMySQLConnection:
    """Test MySQL connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mysql_client, mysql_clean):
        """Test successful connection to MySQL."""
        config = DOCKER_CONFIGS['mysql']

        await mysql_client.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['username'],
            password=config['password']
        )

        assert mysql_client.is_connected()

    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, mysql_client):
        """Test connection with invalid credentials."""
        config = DOCKER_CONFIGS['mysql']

        with pytest.raises(Exception):
            await mysql_client.connect(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user='invalid',
                password='wrong'
            )

    @pytest.mark.asyncio
    async def test_disconnect(self, mysql_client, mysql_clean):
        """Test disconnection from MySQL."""
        config = DOCKER_CONFIGS['mysql']

        await mysql_client.connect(**config)
        assert mysql_client.is_connected()

        await mysql_client.disconnect()
        assert not mysql_client.is_connected()

    @pytest.mark.asyncio
    async def test_reconnect(self, mysql_client, mysql_clean):
        """Test reconnection after disconnect."""
        config = DOCKER_CONFIGS['mysql']

        await mysql_client.connect(**config)
        await mysql_client.disconnect()
        await mysql_client.connect(**config)

        assert mysql_client.is_connected()

    @pytest.mark.asyncio
    async def test_connection_timeout(self, mysql_client):
        """Test connection timeout handling."""
        with pytest.raises(Exception):
            await mysql_client.connect(
                host='192.0.2.1',  # Non-routable IP
                port=3306,
                database='test',
                user='root',
                password='pass',
                timeout=1
            )


class TestMySQLCRUD:
    """Test MySQL CRUD operations."""

    @pytest.mark.asyncio
    async def test_insert_single_row(self, mysql_client, mysql_clean):
        """Test inserting a single row."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        result = await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("John Doe", "john@example.com")
        )

        assert result['affected_rows'] == 1
        assert result['last_insert_id'] > 0

    @pytest.mark.asyncio
    async def test_select_rows(self, mysql_client, mysql_clean):
        """Test selecting rows."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Insert test data
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Jane Smith", "jane@example.com")
        )

        # Select
        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE email = %s",
            ("jane@example.com",)
        )

        assert len(result['rows']) == 1
        assert result['rows'][0]['name'] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_update_row(self, mysql_client, mysql_clean):
        """Test updating a row."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Insert
        result = await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Bob", "bob@example.com")
        )
        user_id = result['last_insert_id']

        # Update
        result = await mysql_client.execute(
            "UPDATE test_users SET name = %s WHERE id = %s",
            ("Robert", user_id)
        )

        assert result['affected_rows'] == 1

        # Verify
        result = await mysql_client.execute(
            "SELECT name FROM test_users WHERE id = %s",
            (user_id,)
        )
        assert result['rows'][0]['name'] == "Robert"

    @pytest.mark.asyncio
    async def test_delete_row(self, mysql_client, mysql_clean):
        """Test deleting a row."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Insert
        result = await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Alice", "alice@example.com")
        )
        user_id = result['last_insert_id']

        # Delete
        result = await mysql_client.execute(
            "DELETE FROM test_users WHERE id = %s",
            (user_id,)
        )

        assert result['affected_rows'] == 1

        # Verify
        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE id = %s",
            (user_id,)
        )
        assert len(result['rows']) == 0

    @pytest.mark.asyncio
    async def test_bulk_insert(self, mysql_client, mysql_clean):
        """Test bulk insert operations."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        values = [(f"User{i}", f"user{i}@example.com") for i in range(100)]

        for name, email in values:
            await mysql_client.execute(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                (name, email)
            )

        result = await mysql_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 100

    @pytest.mark.asyncio
    async def test_insert_with_auto_increment(self, mysql_client, mysql_clean):
        """Test insert with auto-increment ID."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        result1 = await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User1", "user1@example.com")
        )
        result2 = await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User2", "user2@example.com")
        )

        assert result2['last_insert_id'] > result1['last_insert_id']


class TestMySQLTransactions:
    """Test MySQL transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, mysql_client, mysql_clean):
        """Test transaction commit."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        await mysql_client.begin()
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("TX User", "tx@example.com")
        )
        await mysql_client.commit()

        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE email = %s",
            ("tx@example.com",)
        )
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, mysql_client, mysql_clean):
        """Test transaction rollback."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        await mysql_client.begin()
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Rollback User", "rollback@example.com")
        )
        await mysql_client.rollback()

        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE email = %s",
            ("rollback@example.com",)
        )
        assert len(result['rows']) == 0

    @pytest.mark.asyncio
    async def test_transaction_isolation_levels(self, mysql_client, mysql_clean):
        """Test different transaction isolation levels."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Test READ COMMITTED
        await mysql_client.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        await mysql_client.begin()
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("ISO User", "iso@example.com")
        )
        await mysql_client.commit()

        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE email = %s",
            ("iso@example.com",)
        )
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_savepoint_operations(self, mysql_client, mysql_clean):
        """Test savepoint operations."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        await mysql_client.begin()
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Outer", "outer@example.com")
        )

        # Create savepoint
        await mysql_client.execute("SAVEPOINT sp1")
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Inner", "inner@example.com")
        )

        # Rollback to savepoint
        await mysql_client.execute("ROLLBACK TO SAVEPOINT sp1")
        await mysql_client.commit()

        result = await mysql_client.execute("SELECT email FROM test_users")
        emails = [row['email'] for row in result['rows']]
        assert "outer@example.com" in emails
        assert "inner@example.com" not in emails


class TestMySQLConnectionPooling:
    """Test MySQL connection pooling."""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, mysql_client, mysql_clean):
        """Test handling concurrent queries."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        async def insert_user(index):
            await mysql_client.execute(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                (f"Concurrent{index}", f"concurrent{index}@example.com")
            )

        # Run 10 concurrent inserts
        tasks = [insert_user(i) for i in range(10)]
        await asyncio.gather(*tasks)

        result = await mysql_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 10

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self, mysql_client, mysql_clean):
        """Test connection pool connection reuse."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config, max_connections=3)

        # Execute multiple queries
        for i in range(10):
            result = await mysql_client.execute("SELECT %s as value", (i,))
            assert result['rows'][0]['value'] == i


class TestMySQLPreparedStatements:
    """Test MySQL prepared statements."""

    @pytest.mark.asyncio
    async def test_prepared_statement(self, mysql_client, mysql_clean):
        """Test prepared statement execution."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Prepare statement
        stmt = await mysql_client.prepare(
            "INSERT INTO test_users (name, email) VALUES (?, ?)"
        )

        # Execute prepared statement
        await stmt.execute(("Prepared", "prepared@example.com"))

        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE email = %s",
            ("prepared@example.com",)
        )
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_prepared_statement_reuse(self, mysql_client, mysql_clean):
        """Test reusing prepared statements."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        stmt = await mysql_client.prepare(
            "SELECT * FROM test_users WHERE email = ?"
        )

        # Insert test data
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("Test", "test@example.com")
        )

        # Execute prepared statement multiple times
        for _ in range(5):
            result = await stmt.execute(("test@example.com",))
            assert len(result['rows']) == 1


class TestMySQLStoredProcedures:
    """Test MySQL stored procedures."""

    @pytest.mark.asyncio
    async def test_create_stored_procedure(self, mysql_client, mysql_clean):
        """Test creating stored procedure."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create procedure
        await mysql_client.execute("""
            CREATE PROCEDURE IF NOT EXISTS insert_test_user(
                IN p_name VARCHAR(255),
                IN p_email VARCHAR(255)
            )
            BEGIN
                INSERT INTO test_users (name, email) VALUES (p_name, p_email);
            END
        """)

    @pytest.mark.asyncio
    async def test_call_stored_procedure(self, mysql_client, mysql_clean):
        """Test calling stored procedure."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create procedure
        await mysql_client.execute("""
            DROP PROCEDURE IF EXISTS insert_test_user
        """)
        await mysql_client.execute("""
            CREATE PROCEDURE insert_test_user(
                IN p_name VARCHAR(255),
                IN p_email VARCHAR(255)
            )
            BEGIN
                INSERT INTO test_users (name, email) VALUES (p_name, p_email);
            END
        """)

        # Call procedure
        await mysql_client.execute(
            "CALL insert_test_user(%s, %s)",
            ("Proc User", "proc@example.com")
        )

        # Verify
        result = await mysql_client.execute(
            "SELECT * FROM test_users WHERE email = %s",
            ("proc@example.com",)
        )
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_stored_procedure_with_out_parameter(self, mysql_client, mysql_clean):
        """Test stored procedure with OUT parameter."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create procedure with OUT parameter
        await mysql_client.execute("""
            DROP PROCEDURE IF EXISTS count_users
        """)
        await mysql_client.execute("""
            CREATE PROCEDURE count_users(OUT user_count INT)
            BEGIN
                SELECT COUNT(*) INTO user_count FROM test_users;
            END
        """)

        # Insert test data
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User1", "user1@example.com")
        )

        # Call procedure
        await mysql_client.execute("CALL count_users(@count)")
        result = await mysql_client.execute("SELECT @count as count")

        assert result['rows'][0]['count'] == 1


class TestMySQLMultipleResultSets:
    """Test MySQL multiple result sets."""

    @pytest.mark.asyncio
    async def test_multiple_result_sets(self, mysql_client, mysql_clean):
        """Test handling multiple result sets."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Insert test data
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User1", "user1@example.com")
        )

        # Execute multiple queries
        result = await mysql_client.execute_multi("""
            SELECT * FROM test_users;
            SELECT COUNT(*) as count FROM test_users;
        """)

        assert len(result) == 2
        assert len(result[0]['rows']) == 1
        assert result[1]['rows'][0]['count'] == 1


class TestMySQLHealthCheck:
    """Test MySQL health checks."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, mysql_client, mysql_clean):
        """Test health check when connected."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        health = await mysql_client.health_check()

        assert health['healthy'] is True
        assert 'mysql' in health['database_type'].lower()
        assert health['connected'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, mysql_client):
        """Test health check when disconnected."""
        health = await mysql_client.health_check()

        assert health['healthy'] is False
        assert health['connected'] is False

    @pytest.mark.asyncio
    async def test_health_check_with_metrics(self, mysql_client, mysql_clean):
        """Test health check with database metrics."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        health = await mysql_client.health_check(include_metrics=True)

        assert 'metrics' in health
        assert 'connection_count' in health['metrics'] or 'threads_connected' in health['metrics']


class TestMySQLAutomaticReconnection:
    """Test MySQL automatic reconnection."""

    @pytest.mark.asyncio
    async def test_reconnect_after_connection_loss(self, mysql_client, mysql_clean):
        """Test automatic reconnection after connection loss."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Simulate connection loss
        await mysql_client.disconnect()

        # Try to execute query (should reconnect)
        await mysql_client.execute("SELECT 1")

        assert mysql_client.is_connected()

    @pytest.mark.asyncio
    async def test_query_retry_on_failure(self, mysql_client, mysql_clean):
        """Test query retry on transient failures."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Execute query that should succeed after retry
        result = await mysql_client.execute("SELECT 1 as value")
        assert result['rows'][0]['value'] == 1


class TestMySQLErrorHandling:
    """Test MySQL error handling."""

    @pytest.mark.asyncio
    async def test_syntax_error(self, mysql_client, mysql_clean):
        """Test handling SQL syntax errors."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        with pytest.raises(Exception) as exc_info:
            await mysql_client.execute("INVALID SQL SYNTAX")

        assert 'syntax' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_constraint_violation(self, mysql_client, mysql_clean):
        """Test handling constraint violations."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Insert user
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User", "unique@example.com")
        )

        # Try to insert duplicate email
        with pytest.raises(Exception) as exc_info:
            await mysql_client.execute(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                ("Another User", "unique@example.com")
            )

        assert 'duplicate' in str(exc_info.value).lower() or 'unique' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_deadlock_handling(self, mysql_client, mysql_clean):
        """Test handling deadlock situations."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Insert test data
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User1", "user1@example.com")
        )
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("User2", "user2@example.com")
        )

        # Simulate potential deadlock scenario (simplified)
        await mysql_client.begin()
        await mysql_client.execute(
            "UPDATE test_users SET name = %s WHERE email = %s",
            ("Updated1", "user1@example.com")
        )
        await mysql_client.commit()


class TestMySQLAdvancedFeatures:
    """Test MySQL advanced features."""

    @pytest.mark.asyncio
    async def test_json_operations(self, mysql_client, mysql_clean):
        """Test JSON operations."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create table with JSON column
        await mysql_client.execute("""
            CREATE TABLE IF NOT EXISTS test_json (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data JSON
            )
        """)

        # Insert JSON data
        await mysql_client.execute(
            "INSERT INTO test_json (data) VALUES (%s)",
            ('{"name": "John", "age": 30}',)
        )

        # Query JSON data
        result = await mysql_client.execute(
            "SELECT JSON_EXTRACT(data, '$.name') as name FROM test_json"
        )
        assert 'John' in str(result['rows'][0]['name'])

    @pytest.mark.asyncio
    async def test_full_text_search(self, mysql_client, mysql_clean):
        """Test full-text search functionality."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create fulltext index
        await mysql_client.execute("""
            CREATE FULLTEXT INDEX idx_name ON test_users(name)
        """)

        # Insert test data
        await mysql_client.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ("MySQL Expert", "mysql@example.com")
        )

        # Full-text search
        result = await mysql_client.execute("""
            SELECT * FROM test_users
            WHERE MATCH(name) AGAINST('MySQL')
        """)

        assert len(result['rows']) >= 1

    @pytest.mark.asyncio
    async def test_partition_tables(self, mysql_client, mysql_clean):
        """Test partitioned tables."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create partitioned table
        await mysql_client.execute("""
            CREATE TABLE IF NOT EXISTS test_partitioned (
                id INT,
                created_year INT,
                data VARCHAR(255)
            )
            PARTITION BY RANGE (created_year) (
                PARTITION p2020 VALUES LESS THAN (2021),
                PARTITION p2021 VALUES LESS THAN (2022),
                PARTITION p2022 VALUES LESS THAN (2023)
            )
        """)

        # Insert data
        await mysql_client.execute(
            "INSERT INTO test_partitioned (id, created_year, data) VALUES (%s, %s, %s)",
            (1, 2021, "Test data")
        )

        # Query
        result = await mysql_client.execute("SELECT * FROM test_partitioned")
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_generated_columns(self, mysql_client, mysql_clean):
        """Test generated/virtual columns."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        # Create table with generated column
        await mysql_client.execute("""
            CREATE TABLE IF NOT EXISTS test_generated (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                full_name VARCHAR(101) GENERATED ALWAYS AS (CONCAT(first_name, ' ', last_name))
            )
        """)

        # Insert data
        await mysql_client.execute(
            "INSERT INTO test_generated (first_name, last_name) VALUES (%s, %s)",
            ("John", "Doe")
        )

        # Query
        result = await mysql_client.execute("SELECT full_name FROM test_generated")
        assert result['rows'][0]['full_name'] == "John Doe"
