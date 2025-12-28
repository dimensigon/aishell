"""Performance benchmark tests for MCP database clients."""
import asyncio
import time
import pytest
from tests.integration.mcp.config import DOCKER_CONFIGS, BENCHMARK_CONFIGS


class TestPostgreSQLPerformance:
    """PostgreSQL performance benchmarks."""

    @pytest.mark.asyncio
    async def test_query_execution_time(self, pg_client, postgresql_clean):
        """Test PostgreSQL query execution time."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        start_time = time.time()

        for _ in range(BENCHMARK_CONFIGS['query_count']):
            await pg_client.execute("SELECT 1")

        duration = time.time() - start_time

        # Should execute 1000 queries in reasonable time (< 5 seconds)
        assert duration < 5.0

        queries_per_second = BENCHMARK_CONFIGS['query_count'] / duration
        print(f"\nPostgreSQL: {queries_per_second:.2f} queries/second")

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, pg_client, postgresql_clean):
        """Test PostgreSQL bulk insert performance."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        rows_to_insert = BENCHMARK_CONFIGS['bulk_insert_rows']

        start_time = time.time()

        for i in range(rows_to_insert):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (f"User{i}", f"user{i}@example.com")
            )

        duration = time.time() - start_time

        # Should insert 5000 rows in reasonable time (< 10 seconds)
        assert duration < 10.0

        rows_per_second = rows_to_insert / duration
        print(f"\nPostgreSQL bulk insert: {rows_per_second:.2f} rows/second")

    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, pg_client, postgresql_clean):
        """Test PostgreSQL concurrent query performance."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        concurrent_count = BENCHMARK_CONFIGS['concurrent_connections']

        async def execute_queries():
            for _ in range(100):
                await pg_client.execute("SELECT 1")

        start_time = time.time()

        # Run concurrent queries
        await asyncio.gather(*[execute_queries() for _ in range(concurrent_count)])

        duration = time.time() - start_time

        total_queries = concurrent_count * 100
        queries_per_second = total_queries / duration

        print(f"\nPostgreSQL concurrent: {queries_per_second:.2f} queries/second ({concurrent_count} connections)")

    @pytest.mark.asyncio
    async def test_large_result_set_performance(self, pg_client, postgresql_clean):
        """Test PostgreSQL large result set handling."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config)

        # Insert large dataset
        rows = BENCHMARK_CONFIGS['large_result_rows']
        for i in range(rows):
            await pg_client.execute(
                "INSERT INTO test_users (name, email) VALUES ($1, $2)",
                (f"User{i}", f"user{i}@example.com")
            )

        start_time = time.time()

        # Fetch all rows
        result = await pg_client.execute("SELECT * FROM test_users")

        duration = time.time() - start_time

        assert len(result['rows']) == rows
        print(f"\nPostgreSQL large result set ({rows} rows): {duration:.2f} seconds")


class TestMySQLPerformance:
    """MySQL performance benchmarks."""

    @pytest.mark.asyncio
    async def test_query_execution_time(self, mysql_client, mysql_clean):
        """Test MySQL query execution time."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        start_time = time.time()

        for _ in range(BENCHMARK_CONFIGS['query_count']):
            await mysql_client.execute("SELECT 1")

        duration = time.time() - start_time

        assert duration < 5.0

        queries_per_second = BENCHMARK_CONFIGS['query_count'] / duration
        print(f"\nMySQL: {queries_per_second:.2f} queries/second")

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, mysql_client, mysql_clean):
        """Test MySQL bulk insert performance."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        rows_to_insert = BENCHMARK_CONFIGS['bulk_insert_rows']

        start_time = time.time()

        for i in range(rows_to_insert):
            await mysql_client.execute(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                (f"User{i}", f"user{i}@example.com")
            )

        duration = time.time() - start_time

        assert duration < 10.0

        rows_per_second = rows_to_insert / duration
        print(f"\nMySQL bulk insert: {rows_per_second:.2f} rows/second")

    @pytest.mark.asyncio
    async def test_transaction_performance(self, mysql_client, mysql_clean):
        """Test MySQL transaction performance."""
        config = DOCKER_CONFIGS['mysql']
        await mysql_client.connect(**config)

        transaction_count = 100

        start_time = time.time()

        for i in range(transaction_count):
            await mysql_client.begin()
            await mysql_client.execute(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                (f"TxUser{i}", f"txuser{i}@example.com")
            )
            await mysql_client.commit()

        duration = time.time() - start_time

        transactions_per_second = transaction_count / duration
        print(f"\nMySQL transactions: {transactions_per_second:.2f} transactions/second")


class TestMongoDBPerformance:
    """MongoDB performance benchmarks."""

    @pytest.mark.asyncio
    async def test_insert_performance(self, mongo_client, mongodb_clean):
        """Test MongoDB insert performance."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        docs_to_insert = BENCHMARK_CONFIGS['bulk_insert_rows']

        start_time = time.time()

        for i in range(docs_to_insert):
            await mongo_client.insert_one(
                collection='users',
                document={'name': f'User{i}', 'email': f'user{i}@example.com', 'age': 20 + (i % 50)}
            )

        duration = time.time() - start_time

        assert duration < 10.0

        docs_per_second = docs_to_insert / duration
        print(f"\nMongoDB insert: {docs_per_second:.2f} documents/second")

    @pytest.mark.asyncio
    async def test_query_performance(self, mongo_client, mongodb_clean):
        """Test MongoDB query performance."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(1000):
            await mongo_client.insert_one(
                collection='users',
                document={'name': f'User{i}', 'age': 20 + (i % 50), 'category': f'cat{i % 10}'}
            )

        query_count = BENCHMARK_CONFIGS['query_count']

        start_time = time.time()

        for i in range(query_count):
            await mongo_client.find(
                collection='users',
                filter={'category': f'cat{i % 10}'}
            )

        duration = time.time() - start_time

        queries_per_second = query_count / duration
        print(f"\nMongoDB query: {queries_per_second:.2f} queries/second")

    @pytest.mark.asyncio
    async def test_aggregation_performance(self, mongo_client, mongodb_clean):
        """Test MongoDB aggregation performance."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        # Insert test data
        for i in range(5000):
            await mongo_client.insert_one(
                collection='orders',
                document={'product': f'Product{i % 100}', 'amount': 10 + i, 'quantity': 1 + (i % 10)}
            )

        pipeline = [
            {'$group': {
                '_id': '$product',
                'total_amount': {'$sum': '$amount'},
                'total_quantity': {'$sum': '$quantity'}
            }},
            {'$sort': {'total_amount': -1}},
            {'$limit': 10}
        ]

        start_time = time.time()

        for _ in range(100):
            await mongo_client.aggregate(collection='orders', pipeline=pipeline)

        duration = time.time() - start_time

        aggregations_per_second = 100 / duration
        print(f"\nMongoDB aggregation: {aggregations_per_second:.2f} aggregations/second")

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, mongo_client, mongodb_clean):
        """Test MongoDB bulk insert performance."""
        config = DOCKER_CONFIGS['mongodb']
        await mongo_client.connect(**config)

        docs_count = BENCHMARK_CONFIGS['bulk_insert_rows']
        documents = [
            {'name': f'User{i}', 'email': f'user{i}@example.com', 'age': 20 + (i % 50)}
            for i in range(docs_count)
        ]

        start_time = time.time()

        await mongo_client.insert_many(collection='users', documents=documents)

        duration = time.time() - start_time

        docs_per_second = docs_count / duration
        print(f"\nMongoDB bulk insert: {docs_per_second:.2f} documents/second")


class TestRedisPerformance:
    """Redis performance benchmarks."""

    @pytest.mark.asyncio
    async def test_get_set_performance(self, redis_mcp_client, redis_clean):
        """Test Redis GET/SET performance."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        operations = BENCHMARK_CONFIGS['query_count']

        start_time = time.time()

        for i in range(operations):
            await redis_mcp_client.set(f'key{i}', f'value{i}')

        duration = time.time() - start_time

        ops_per_second = operations / duration
        print(f"\nRedis SET: {ops_per_second:.2f} operations/second")

        start_time = time.time()

        for i in range(operations):
            await redis_mcp_client.get(f'key{i}')

        duration = time.time() - start_time

        ops_per_second = operations / duration
        print(f"\nRedis GET: {ops_per_second:.2f} operations/second")

    @pytest.mark.asyncio
    async def test_hash_operations_performance(self, redis_mcp_client, redis_clean):
        """Test Redis hash operations performance."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        operations = BENCHMARK_CONFIGS['query_count']

        start_time = time.time()

        for i in range(operations):
            await redis_mcp_client.hset(f'hash{i}', 'field1', f'value{i}')

        duration = time.time() - start_time

        ops_per_second = operations / duration
        print(f"\nRedis HSET: {ops_per_second:.2f} operations/second")

    @pytest.mark.asyncio
    async def test_list_operations_performance(self, redis_mcp_client, redis_clean):
        """Test Redis list operations performance."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        operations = BENCHMARK_CONFIGS['query_count']

        start_time = time.time()

        for i in range(operations):
            await redis_mcp_client.lpush('mylist', f'item{i}')

        duration = time.time() - start_time

        ops_per_second = operations / duration
        print(f"\nRedis LPUSH: {ops_per_second:.2f} operations/second")

    @pytest.mark.asyncio
    async def test_pipeline_performance(self, redis_mcp_client, redis_clean):
        """Test Redis pipeline performance."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        operations = BENCHMARK_CONFIGS['query_count']

        start_time = time.time()

        pipeline = redis_mcp_client.pipeline()

        for i in range(operations):
            pipeline.set(f'pipe_key{i}', f'pipe_value{i}')

        await pipeline.execute()

        duration = time.time() - start_time

        ops_per_second = operations / duration
        print(f"\nRedis pipeline: {ops_per_second:.2f} operations/second")


class TestSQLitePerformance:
    """SQLite performance benchmarks."""

    @pytest.mark.asyncio
    async def test_insert_performance(self, sqlite_client, sqlite_clean):
        """Test SQLite insert performance."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        rows_to_insert = BENCHMARK_CONFIGS['bulk_insert_rows']

        start_time = time.time()

        for i in range(rows_to_insert):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"User{i}", f"user{i}@example.com")
            )

        duration = time.time() - start_time

        rows_per_second = rows_to_insert / duration
        print(f"\nSQLite insert: {rows_per_second:.2f} rows/second")

    @pytest.mark.asyncio
    async def test_query_performance(self, sqlite_client, sqlite_clean):
        """Test SQLite query performance."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        # Insert test data
        for i in range(1000):
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"User{i}", f"user{i}@example.com")
            )

        query_count = BENCHMARK_CONFIGS['query_count']

        start_time = time.time()

        for i in range(query_count):
            await sqlite_client.execute(
                "SELECT * FROM test_users WHERE id = ?",
                (i % 1000 + 1,)
            )

        duration = time.time() - start_time

        queries_per_second = query_count / duration
        print(f"\nSQLite query: {queries_per_second:.2f} queries/second")

    @pytest.mark.asyncio
    async def test_transaction_performance(self, sqlite_client, sqlite_clean):
        """Test SQLite transaction performance."""
        await sqlite_client.connect(database=str(sqlite_clean._connection))

        transaction_count = 100

        start_time = time.time()

        for i in range(transaction_count):
            await sqlite_client.begin()
            await sqlite_client.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                (f"TxUser{i}", f"txuser{i}@example.com")
            )
            await sqlite_client.commit()

        duration = time.time() - start_time

        transactions_per_second = transaction_count / duration
        print(f"\nSQLite transactions: {transactions_per_second:.2f} transactions/second")


class TestConnectionPoolPerformance:
    """Connection pool performance benchmarks."""

    @pytest.mark.asyncio
    async def test_postgresql_pool_performance(self, pg_client, postgresql_clean):
        """Test PostgreSQL connection pool performance."""
        config = DOCKER_CONFIGS['postgresql']
        await pg_client.connect(**config, max_connections=10)

        concurrent_tasks = BENCHMARK_CONFIGS['concurrent_connections']

        async def execute_queries():
            for _ in range(100):
                await pg_client.execute("SELECT 1")

        start_time = time.time()

        await asyncio.gather(*[execute_queries() for _ in range(concurrent_tasks)])

        duration = time.time() - start_time

        total_queries = concurrent_tasks * 100
        queries_per_second = total_queries / duration

        print(f"\nPostgreSQL pool ({concurrent_tasks} concurrent): {queries_per_second:.2f} queries/second")

    @pytest.mark.asyncio
    async def test_redis_pool_performance(self, redis_mcp_client, redis_clean):
        """Test Redis connection pool performance."""
        config = DOCKER_CONFIGS['redis']
        await redis_mcp_client.connect(**config)

        concurrent_tasks = BENCHMARK_CONFIGS['concurrent_connections']

        async def execute_operations():
            for i in range(100):
                await redis_mcp_client.set(f'pool_key_{i}', f'pool_value_{i}')

        start_time = time.time()

        await asyncio.gather(*[execute_operations() for _ in range(concurrent_tasks)])

        duration = time.time() - start_time

        total_operations = concurrent_tasks * 100
        ops_per_second = total_operations / duration

        print(f"\nRedis pool ({concurrent_tasks} concurrent): {ops_per_second:.2f} operations/second")


class TestComparativePerformance:
    """Comparative performance tests across databases."""

    @pytest.mark.asyncio
    async def test_simple_query_comparison(self, pg_client, mysql_client, mongodb_clean, redis_mcp_client, postgresql_clean, mysql_clean, redis_clean):
        """Compare simple query performance across databases."""
        results = {}

        # PostgreSQL
        await pg_client.connect(**DOCKER_CONFIGS['postgresql'])
        start = time.time()
        for _ in range(1000):
            await pg_client.execute("SELECT 1")
        results['PostgreSQL'] = 1000 / (time.time() - start)

        # MySQL
        await mysql_client.connect(**DOCKER_CONFIGS['mysql'])
        start = time.time()
        for _ in range(1000):
            await mysql_client.execute("SELECT 1")
        results['MySQL'] = 1000 / (time.time() - start)

        # Redis
        await redis_mcp_client.connect(**DOCKER_CONFIGS['redis'])
        start = time.time()
        for _ in range(1000):
            await redis_mcp_client.get('nonexistent')
        results['Redis'] = 1000 / (time.time() - start)

        print("\n=== Simple Query Performance Comparison ===")
        for db, qps in sorted(results.items(), key=lambda x: x[1], reverse=True):
            print(f"{db}: {qps:.2f} queries/second")
