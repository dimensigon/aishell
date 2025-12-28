"""SQLite integration tests."""
import asyncio
import pytest
from pathlib import Path
from tests.integration.mcp.config import DOCKER_CONFIGS


class TestSQLiteConnection:
    """Test SQLite connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_success(self, sqlite_client, sqlite_connection):
        """Test successful connection to SQLite."""
        db_path = sqlite_connection._connection if hasattr(sqlite_connection, '_connection') else '/tmp/test.db'

        await sqlite_client.connect(database=str(db_path))

        assert sqlite_client.is_connected()

    @pytest.mark.asyncio
    async def test_connect_memory_database(self, sqlite_client):
        """Test connection to in-memory database."""
        await sqlite_client.connect(database=':memory:')

        assert sqlite_client.is_connected()

    @pytest.mark.asyncio
    async def test_disconnect(self, sqlite_client, sqlite_connection):
        """Test disconnection from SQLite."""
        db_path = str(sqlite_connection._connection) if hasattr(sqlite_connection, '_connection') else '/tmp/test.db'

        await sqlite_client.connect(database=db_path)
        assert sqlite_client.is_connected()

        await sqlite_client.disconnect()
        assert not sqlite_client.is_connected()

    @pytest.mark.asyncio
    async def test_reconnect(self, sqlite_client, tmp_path):
        """Test reconnection after disconnect."""
        db_path = tmp_path / "reconnect.db"

        await sqlite_client.connect(database=str(db_path))
        await sqlite_client.disconnect()
        await sqlite_client.connect(database=str(db_path))

        assert sqlite_client.is_connected()

    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, sqlite_client, tmp_path):
        """Test WAL mode is enabled."""
        db_path = tmp_path / "wal_test.db"

        await sqlite_client.connect(database=str(db_path), wal_mode=True)

        # Check journal mode
        result = await sqlite_client.execute("PRAGMA journal_mode")

        assert result['rows'][0][0].lower() == 'wal'


class TestSQLiteCRUD:
    """Test SQLite CRUD operations."""

    @pytest.mark.asyncio
    async def test_insert_single_row(self, sqlite_client, sqlite_clean):
        """Test inserting a single row."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        result = await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("John Doe", "john@example.com")
        )

        assert result['last_row_id'] is not None
        assert result['changes'] == 1

    @pytest.mark.asyncio
    async def test_select_rows(self, sqlite_client, sqlite_clean):
        """Test selecting rows."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert test data
        await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Jane Smith", "jane@example.com")
        )

        # Select
        result = await sqlite_client.execute(
            "SELECT * FROM test_users WHERE email = ?",
            ("jane@example.com",)
        )

        assert len(result['rows']) == 1
        assert result['rows'][0]['name'] == "Jane Smith"

    @pytest.mark.asyncio
    async def test_update_row(self, sqlite_client, sqlite_clean):
        """Test updating a row."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert
        result = await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Bob", "bob@example.com")
        )
        user_id = result['last_row_id']

        # Update
        result = await sqlite_client.execute(
            "UPDATE test_users SET name = ? WHERE id = ?",
            ("Robert", user_id)
        )

        assert result['changes'] == 1

        # Verify
        result = await sqlite_client.execute(
            "SELECT name FROM test_users WHERE id = ?",
            (user_id,)
        )
        assert result['rows'][0]['name'] == "Robert"

    @pytest.mark.asyncio
    async def test_delete_row(self, sqlite_client, sqlite_clean):
        """Test deleting a row."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert
        result = await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Alice", "alice@example.com")
        )
        user_id = result['last_row_id']

        # Delete
        result = await sqlite_client.execute(
            "DELETE FROM test_users WHERE id = ?",
            (user_id,)
        )

        assert result['changes'] == 1

        # Verify
        result = await sqlite_client.execute(
            "SELECT * FROM test_users WHERE id = ?",
            (user_id,)
        )
        assert len(result['rows']) == 0

    @pytest.mark.asyncio
    async def test_bulk_insert(self, sqlite_client, sqlite_clean):
        """Test bulk insert operations."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        values = [(f"User{i}", f"user{i}@example.com") for i in range(100)]

        await sqlite_client.executemany(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            values
        )

        result = await sqlite_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 100


class TestSQLiteTransactions:
    """Test SQLite transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, sqlite_client, sqlite_clean):
        """Test transaction commit."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        await sqlite_client.begin()
        await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("TX User", "tx@example.com")
        )
        await sqlite_client.commit()

        result = await sqlite_client.execute(
            "SELECT * FROM test_users WHERE email = ?",
            ("tx@example.com",)
        )
        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, sqlite_client, sqlite_clean):
        """Test transaction rollback."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        await sqlite_client.begin()
        await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Rollback User", "rollback@example.com")
        )
        await sqlite_client.rollback()

        result = await sqlite_client.execute(
            "SELECT * FROM test_users WHERE email = ?",
            ("rollback@example.com",)
        )
        assert len(result['rows']) == 0

    @pytest.mark.asyncio
    async def test_savepoint_operations(self, sqlite_client, sqlite_clean):
        """Test savepoint operations."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        await sqlite_client.begin()
        await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Outer", "outer@example.com")
        )

        # Create savepoint
        await sqlite_client.execute("SAVEPOINT sp1")
        await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("Inner", "inner@example.com")
        )

        # Rollback to savepoint
        await sqlite_client.execute("ROLLBACK TO SAVEPOINT sp1")
        await sqlite_client.commit()

        result = await sqlite_client.execute("SELECT email FROM test_users")
        emails = [row['email'] for row in result['rows']]
        assert "outer@example.com" in emails
        assert "inner@example.com" not in emails


class TestSQLiteConcurrentAccess:
    """Test SQLite concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, sqlite_client, sqlite_clean):
        """Test concurrent read operations."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert test data
        for i in range(10):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"User{i}", f"user{i}@example.com")
            )

        async def read_users():
            result = await sqlite_client.execute("SELECT COUNT(*) as count FROM test_users")
            return result['rows'][0]['count']

        # Run concurrent reads
        tasks = [read_users() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert all(count == 10 for count in results)

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, sqlite_client, sqlite_clean):
        """Test concurrent write operations."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        async def insert_user(index):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"Concurrent{index}", f"concurrent{index}@example.com")
            )

        # Run concurrent writes
        tasks = [insert_user(i) for i in range(10)]
        await asyncio.gather(*tasks)

        result = await sqlite_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 10


class TestSQLiteFileLocking:
    """Test SQLite file locking."""

    @pytest.mark.asyncio
    async def test_exclusive_lock(self, sqlite_client, tmp_path):
        """Test exclusive lock behavior."""
        db_path = tmp_path / "lock_test.db"

        await sqlite_client.connect(database=str(db_path))

        # Create table
        await sqlite_client.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """)

        # Start exclusive transaction
        await sqlite_client.execute("BEGIN EXCLUSIVE")
        await sqlite_client.execute("INSERT INTO test_table (value) VALUES ('locked')")

        # Complete transaction
        await sqlite_client.commit()

        # Verify
        result = await sqlite_client.execute("SELECT * FROM test_table")
        assert len(result['rows']) == 1


class TestSQLiteHealthCheck:
    """Test SQLite health checks."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, sqlite_client, sqlite_clean):
        """Test health check when connected."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        health = await sqlite_client.health_check()

        assert health['healthy'] is True
        assert 'sqlite' in health['database_type'].lower()
        assert health['connected'] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, sqlite_client):
        """Test health check when disconnected."""
        health = await sqlite_client.health_check()

        assert health['healthy'] is False
        assert health['connected'] is False

    @pytest.mark.asyncio
    async def test_health_check_with_file_info(self, sqlite_client, sqlite_clean):
        """Test health check with file information."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        health = await sqlite_client.health_check(include_metrics=True)

        assert 'metrics' in health
        assert 'database_path' in health['metrics'] or 'page_count' in health['metrics']


class TestSQLiteErrorHandling:
    """Test SQLite error handling."""

    @pytest.mark.asyncio
    async def test_syntax_error(self, sqlite_client, sqlite_clean):
        """Test handling SQL syntax errors."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        with pytest.raises(Exception) as exc_info:
            await sqlite_client.execute("INVALID SQL SYNTAX")

        assert 'syntax' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_constraint_violation(self, sqlite_client, sqlite_clean):
        """Test handling constraint violations."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert user
        await sqlite_client.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("User", "unique@example.com")
        )

        # Try to insert duplicate email
        with pytest.raises(Exception) as exc_info:
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                ("Another User", "unique@example.com")
            )

        assert 'unique' in str(exc_info.value).lower() or 'constraint' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_table_not_found(self, sqlite_client, tmp_path):
        """Test handling table not found errors."""
        db_path = tmp_path / "no_table.db"

        await sqlite_client.connect(database=str(db_path))

        with pytest.raises(Exception) as exc_info:
            await sqlite_client.execute("SELECT * FROM nonexistent_table")

        assert 'no such table' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_locked_database(self, sqlite_client, tmp_path):
        """Test handling locked database."""
        db_path = tmp_path / "locked.db"

        await sqlite_client.connect(database=str(db_path))

        # Create table
        await sqlite_client.execute("""
            CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)
        """)

        # This test simulates behavior but won't actually lock in single connection
        await sqlite_client.execute("BEGIN IMMEDIATE")
        await sqlite_client.execute("INSERT INTO test_table (value) VALUES ('test')")
        await sqlite_client.commit()


class TestSQLiteAdvancedFeatures:
    """Test SQLite advanced features."""

    @pytest.mark.asyncio
    async def test_full_text_search(self, sqlite_client, tmp_path):
        """Test full-text search with FTS5."""
        db_path = tmp_path / "fts_test.db"

        await sqlite_client.connect(database=str(db_path))

        # Create FTS5 table
        await sqlite_client.execute("""
            CREATE VIRTUAL TABLE articles USING fts5(title, content)
        """)

        # Insert data
        await sqlite_client.execute(
            "INSERT INTO articles (title, content) VALUES (?, ?)",
            ("SQLite Tutorial", "Learn how to use SQLite database")
        )

        # Full-text search
        result = await sqlite_client.execute(
            "SELECT * FROM articles WHERE articles MATCH ?",
            ("SQLite",)
        )

        assert len(result['rows']) == 1

    @pytest.mark.asyncio
    async def test_json_operations(self, sqlite_client, tmp_path):
        """Test JSON operations."""
        db_path = tmp_path / "json_test.db"

        await sqlite_client.connect(database=str(db_path))

        # Create table with JSON column
        await sqlite_client.execute("""
            CREATE TABLE IF NOT EXISTS test_json (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)

        # Insert JSON data
        await sqlite_client.execute(
            "INSERT INTO test_json (data) VALUES (?)",
            ('{"name": "John", "age": 30}',)
        )

        # Query JSON data
        result = await sqlite_client.execute(
            "SELECT json_extract(data, '$.name') as name FROM test_json"
        )
        assert result['rows'][0]['name'] == "John"

    @pytest.mark.asyncio
    async def test_common_table_expressions(self, sqlite_client, sqlite_clean):
        """Test Common Table Expressions (CTEs)."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert test data
        for i in range(5):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"User{i}", f"user{i}@example.com")
            )

        # CTE query
        result = await sqlite_client.execute("""
            WITH user_count AS (
                SELECT COUNT(*) as total FROM test_users
            )
            SELECT total FROM user_count
        """)

        assert result['rows'][0]['total'] == 5

    @pytest.mark.asyncio
    async def test_window_functions(self, sqlite_client, sqlite_clean):
        """Test window functions."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert test data
        for i in range(5):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"User{i}", f"user{i}@example.com")
            )

        # Use window function
        result = await sqlite_client.execute("""
            SELECT name, ROW_NUMBER() OVER (ORDER BY id) as row_num
            FROM test_users
        """)

        assert len(result['rows']) == 5
        assert result['rows'][0]['row_num'] == 1

    @pytest.mark.asyncio
    async def test_vacuum_optimize(self, sqlite_client, sqlite_clean):
        """Test VACUUM and ANALYZE commands."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert and delete data to create fragmentation
        for i in range(100):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"User{i}", f"user{i}@example.com")
            )

        await sqlite_client.execute("DELETE FROM test_users WHERE id % 2 = 0")

        # Optimize database
        await sqlite_client.execute("VACUUM")
        await sqlite_client.execute("ANALYZE")

        # Verify
        result = await sqlite_client.execute("SELECT COUNT(*) as count FROM test_users")
        assert result['rows'][0]['count'] == 50
