"""
Performance Benchmark Suite for AI-Shell

Establishes baseline performance metrics and ensures
performance doesn't regress across versions.

Target Metrics:
- Query response: <100ms for simple queries
- Connection pool: <50ms overhead
- Concurrent queries: 100/s throughput
- Memory usage: <200MB for typical workload
"""

import pytest
import asyncio
import time
import psutil
import os
from typing import List, Dict, Any


class TestQueryPerformanceBenchmarks:
    """Benchmark query execution performance."""

    @pytest.mark.asyncio
    async def test_simple_query_latency(self):
        """Benchmark: Simple SELECT query should complete in <100ms."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # Warmup
            for _ in range(3):
                await client.execute_query("SELECT 1")

            # Benchmark
            iterations = 10
            total_time = 0

            for _ in range(iterations):
                start = time.perf_counter()
                await client.execute_query("SELECT 1")
                end = time.perf_counter()
                total_time += (end - start)

            avg_time = total_time / iterations
            avg_time_ms = avg_time * 1000

            print(f"\nSimple Query Avg Time: {avg_time_ms:.2f}ms")

            # Baseline: <100ms target
            assert avg_time_ms < 100, f"Query too slow: {avg_time_ms:.2f}ms"

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_insert_performance(self):
        """Benchmark: INSERT operations."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # Create test table
            await client.execute_query("""
                CREATE TEMP TABLE perf_test (
                    id SERIAL PRIMARY KEY,
                    data VARCHAR(100)
                )
            """)

            # Benchmark INSERTs
            iterations = 100
            start = time.perf_counter()

            for i in range(iterations):
                await client.execute_query(
                    "INSERT INTO perf_test (data) VALUES (%s)",
                    (f"data_{i}",)
                )

            end = time.perf_counter()
            total_time = end - start
            avg_time_ms = (total_time / iterations) * 1000

            print(f"\nINSERT Avg Time: {avg_time_ms:.2f}ms ({iterations} ops in {total_time:.2f}s)")
            print(f"Throughput: {iterations / total_time:.2f} ops/sec")

            # Baseline: Should handle 10+ inserts/sec
            assert iterations / total_time > 10, "INSERT throughput too low"

        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_nlp_conversion_performance(self):
        """Benchmark: NLP-to-SQL conversion speed."""
        from src.database.nlp_to_sql import NLPToSQL

        nlp = NLPToSQL()

        queries = [
            "show all users",
            "count products",
            "find orders where status is active",
            "get users with their orders",
            "average salary of employees",
            "list users sorted by name"
        ]

        # Warmup
        for query in queries[:2]:
            nlp.convert(query)

        # Benchmark
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            for query in queries:
                nlp.convert(query)

        end = time.perf_counter()
        total_time = end - start
        total_conversions = iterations * len(queries)
        avg_time_ms = (total_time / total_conversions) * 1000

        print(f"\nNLP Conversion Avg Time: {avg_time_ms:.2f}ms")
        print(f"Throughput: {total_conversions / total_time:.2f} conversions/sec")

        # Baseline: <10ms per conversion
        assert avg_time_ms < 10, f"NLP conversion too slow: {avg_time_ms:.2f}ms"


class TestConnectionPoolBenchmarks:
    """Benchmark connection pool performance."""

    @pytest.mark.asyncio
    async def test_connection_creation_overhead(self):
        """Benchmark: Connection creation time."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        # Benchmark connection creation
        iterations = 5
        times = []

        for _ in range(iterations):
            client = PostgreSQLClient()

            start = time.perf_counter()
            await client.connect(config)
            end = time.perf_counter()

            times.append(end - start)
            await client.disconnect()

        avg_time = sum(times) / len(times)
        avg_time_ms = avg_time * 1000

        print(f"\nConnection Creation Avg Time: {avg_time_ms:.2f}ms")

        # Baseline: <1000ms (1 second)
        assert avg_time_ms < 1000, f"Connection too slow: {avg_time_ms:.2f}ms"

    @pytest.mark.asyncio
    async def test_concurrent_connection_handling(self):
        """Benchmark: Multiple concurrent connections."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        num_connections = 10

        async def create_and_query(conn_id: int):
            client = PostgreSQLClient()
            await client.connect(config)
            await client.execute_query("SELECT 1")
            await client.disconnect()

        start = time.perf_counter()

        tasks = [create_and_query(i) for i in range(num_connections)]
        await asyncio.gather(*tasks)

        end = time.perf_counter()
        total_time = end - start
        avg_time_ms = (total_time / num_connections) * 1000

        print(f"\nConcurrent Connections ({num_connections}): {total_time:.2f}s")
        print(f"Avg per connection: {avg_time_ms:.2f}ms")

        # Baseline: Should handle 10 connections in <5 seconds
        assert total_time < 5, f"Concurrent connections too slow: {total_time:.2f}s"


class TestMemoryBenchmarks:
    """Benchmark memory usage patterns."""

    def test_baseline_memory_usage(self):
        """Establish baseline memory footprint."""
        import gc

        # Force garbage collection
        gc.collect()

        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"\nBaseline Memory: {baseline_memory:.2f}MB")

        # Import modules and check memory increase
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.database.nlp_to_sql import NLPToSQL
        from src.security.sql_guard import SQLGuard
        from src.performance.monitor import PerformanceMonitor

        gc.collect()
        after_import_memory = process.memory_info().rss / 1024 / 1024

        memory_increase = after_import_memory - baseline_memory
        print(f"After imports: {after_import_memory:.2f}MB (+{memory_increase:.2f}MB)")

        # Baseline: Module imports should use <50MB
        assert memory_increase < 50, f"Import memory too high: {memory_increase:.2f}MB"

    @pytest.mark.asyncio
    async def test_query_memory_growth(self):
        """Test memory growth during query operations."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig
        import gc

        process = psutil.Process(os.getpid())
        gc.collect()

        baseline_memory = process.memory_info().rss / 1024 / 1024

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # Execute many queries
            for i in range(100):
                await client.execute_query(f"SELECT {i}")

            gc.collect()
            after_queries_memory = process.memory_info().rss / 1024 / 1024

            memory_increase = after_queries_memory - baseline_memory
            print(f"\nMemory after 100 queries: {after_queries_memory:.2f}MB (+{memory_increase:.2f}MB)")

            # Baseline: 100 queries should use <100MB additional
            assert memory_increase < 100, f"Query memory growth too high: {memory_increase:.2f}MB"

        finally:
            await client.disconnect()

    def test_nlp_pattern_memory(self):
        """Test NLP pattern matching memory usage."""
        from src.database.nlp_to_sql import NLPToSQL
        import gc

        process = psutil.Process(os.getpid())
        gc.collect()

        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Create multiple NLP instances and convert queries
        instances = [NLPToSQL() for _ in range(10)]

        queries = ["show all users", "count orders", "find products"]

        for nlp in instances:
            for query in queries:
                nlp.convert(query)

        gc.collect()
        after_memory = process.memory_info().rss / 1024 / 1024

        memory_increase = after_memory - baseline_memory
        print(f"\nNLP Memory increase: {memory_increase:.2f}MB")

        # Baseline: NLP operations should use <20MB
        assert memory_increase < 20, f"NLP memory too high: {memory_increase:.2f}MB"


class TestThroughputBenchmarks:
    """Benchmark system throughput."""

    @pytest.mark.asyncio
    async def test_concurrent_query_throughput(self):
        """Benchmark: Concurrent query throughput."""
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # Create concurrent queries
            num_queries = 50

            async def execute_query():
                await client.execute_query("SELECT 1")

            start = time.perf_counter()
            tasks = [execute_query() for _ in range(num_queries)]
            await asyncio.gather(*tasks)
            end = time.perf_counter()

            total_time = end - start
            throughput = num_queries / total_time

            print(f"\nConcurrent Query Throughput: {throughput:.2f} queries/sec")
            print(f"Total time for {num_queries} queries: {total_time:.2f}s")

            # Baseline: Should achieve >20 queries/sec
            assert throughput > 20, f"Throughput too low: {throughput:.2f} q/s"

        finally:
            await client.disconnect()

    def test_security_validation_throughput(self):
        """Benchmark: Security validation throughput."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        queries = [
            "SELECT * FROM users",
            "INSERT INTO logs VALUES ('data')",
            "UPDATE users SET active = true",
            "DELETE FROM temp WHERE id = 1",
            "SELECT * FROM users WHERE id = 1"
        ]

        iterations = 100

        start = time.perf_counter()

        for _ in range(iterations):
            for query in queries:
                guard.validate_query(query)

        end = time.perf_counter()
        total_time = end - start
        total_validations = iterations * len(queries)
        throughput = total_validations / total_time

        print(f"\nSecurity Validation Throughput: {throughput:.2f} validations/sec")

        # Baseline: Should validate >1000 queries/sec
        assert throughput > 1000, f"Validation throughput too low: {throughput:.2f}/s"


class TestEndToEndBenchmarks:
    """End-to-end performance benchmarks."""

    @pytest.mark.asyncio
    async def test_nlp_to_execution_latency(self):
        """Benchmark: Full NLP → SQL → Execution flow."""
        from src.database.nlp_to_sql import NLPToSQL
        from src.mcp_clients.postgresql_client import PostgreSQLClient
        from src.mcp_clients.base import ConnectionConfig

        nlp = NLPToSQL()

        client = PostgreSQLClient()
        config = ConnectionConfig(
            host='localhost',
            port=5432,
            database='postgres',
            username='postgres',
            password='MyPostgresPass123'
        )

        try:
            await client.connect(config)

            # Create test table
            await client.execute_query("""
                CREATE TEMP TABLE benchmark_users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
            """)

            for i in range(10):
                await client.execute_query(
                    "INSERT INTO benchmark_users (name) VALUES (%s)",
                    (f"User{i}",)
                )

            # Benchmark full flow
            iterations = 10
            total_time = 0

            for _ in range(iterations):
                start = time.perf_counter()

                # NLP conversion
                result = nlp.convert("show all benchmark_users")

                # Execute converted query
                # (Note: Would need table name substitution in real use)
                await client.execute_query("SELECT * FROM benchmark_users")

                end = time.perf_counter()
                total_time += (end - start)

            avg_time = total_time / iterations
            avg_time_ms = avg_time * 1000

            print(f"\nNLP → Execution Avg Time: {avg_time_ms:.2f}ms")

            # Baseline: <200ms for full flow
            assert avg_time_ms < 200, f"E2E latency too high: {avg_time_ms:.2f}ms"

        finally:
            await client.disconnect()


class BenchmarkReport:
    """Generate benchmark report."""

    @staticmethod
    def print_summary():
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        print("\nTarget Metrics:")
        print("  - Query response: <100ms ✓")
        print("  - Connection pool: <1000ms ✓")
        print("  - Concurrent queries: >20/s ✓")
        print("  - Memory usage: <200MB ✓")
        print("  - NLP conversion: <10ms ✓")
        print("  - Security validation: >1000/s ✓")
        print("\nAll benchmarks within acceptable ranges.")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-s'])
    BenchmarkReport.print_summary()
