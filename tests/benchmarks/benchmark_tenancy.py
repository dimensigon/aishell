"""Performance benchmarks for Multi-Tenancy System.

Measures:
- Tenant isolation overhead
- Tenant context switching
- Quota enforcement performance
- Tenant-specific query performance
- Database separation overhead
"""

import unittest
import time
import random
from statistics import mean, stdev


class BenchmarkTenantIsolation(unittest.TestCase):
    """Benchmark tenant isolation performance."""

    def test_tenant_context_creation(self):
        """Benchmark tenant context creation."""
        from src.core.tenancy import TenantContext

        times = []

        for i in range(1000):
            start = time.perf_counter()

            context = TenantContext(f"tenant_{i % 100}")

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)
        std_time = stdev(times)

        print(f"\n=== Tenant Context Creation ===")
        print(f"Iterations: 1000")
        print(f"Average: {avg_time:.4f}ms")
        print(f"Std dev: {std_time:.4f}ms")

        # Context creation should be very fast
        self.assertLess(avg_time, 0.1)

    def test_tenant_context_switching(self):
        """Benchmark switching between tenant contexts."""
        from src.core.tenancy import TenantContextManager

        manager = TenantContextManager()

        # Create multiple tenant contexts
        tenants = [f"tenant_{i}" for i in range(10)]

        times = []
        for _ in range(1000):
            tenant = random.choice(tenants)

            start = time.perf_counter()

            manager.switch_context(tenant)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Tenant Context Switching ===")
        print(f"Tenants: 10")
        print(f"Switches: 1000")
        print(f"Average: {avg_time:.4f}ms")

        # Context switching should be fast
        self.assertLess(avg_time, 0.5)

    def test_tenant_data_isolation_overhead(self):
        """Benchmark data isolation overhead."""
        from src.core.tenancy import TenantContext

        tenant_count = 10
        contexts = {f"tenant_{i}": TenantContext(f"tenant_{i}") for i in range(tenant_count)}

        # Benchmark data access with isolation
        times = []
        for _ in range(1000):
            tenant_id = f"tenant_{random.randint(0, tenant_count - 1)}"
            context = contexts[tenant_id]

            start = time.perf_counter()

            # Access tenant-specific data
            data = context.get_data("users")

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Tenant Data Isolation Overhead ===")
        print(f"Tenants: {tenant_count}")
        print(f"Average access time: {avg_time:.4f}ms")

        # Isolated access should still be fast
        self.assertLess(avg_time, 1.0)


class BenchmarkQuotaEnforcement(unittest.TestCase):
    """Benchmark quota enforcement performance."""

    def test_quota_check_latency(self):
        """Benchmark quota checking latency."""
        from src.core.tenancy import TenantQuotaManager

        quota_mgr = TenantQuotaManager()

        # Set quotas for tenants
        for i in range(100):
            quota_mgr.set_quota(f"tenant_{i}", max_queries=1000, max_storage_mb=5000)

        times = []
        for _ in range(10000):
            tenant = f"tenant_{random.randint(0, 99)}"

            start = time.perf_counter()

            can_execute = quota_mgr.check_quota(tenant, "query")

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)
        std_time = stdev(times)

        print(f"\n=== Quota Check Performance ===")
        print(f"Tenants: 100")
        print(f"Checks: 10000")
        print(f"Average: {avg_time:.4f}ms")
        print(f"Std dev: {std_time:.4f}ms")

        # Quota checks must be very fast to not impact performance
        self.assertLess(avg_time, 0.1)

    def test_quota_update_performance(self):
        """Benchmark quota update performance."""
        from src.core.tenancy import TenantQuotaManager

        quota_mgr = TenantQuotaManager()

        for i in range(100):
            quota_mgr.set_quota(f"tenant_{i}", max_queries=1000)

        times = []
        for _ in range(10000):
            tenant = f"tenant_{random.randint(0, 99)}"

            start = time.perf_counter()

            quota_mgr.increment_usage(tenant, "queries")

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Quota Update Performance ===")
        print(f"Tenants: 100")
        print(f"Updates: 10000")
        print(f"Average: {avg_time:.4f}ms")

        # Quota updates should be fast
        self.assertLess(avg_time, 0.5)

    def test_quota_enforcement_scaling(self):
        """Benchmark quota enforcement scaling with tenant count."""
        from src.core.tenancy import TenantQuotaManager

        tenant_counts = [10, 100, 500, 1000]

        print(f"\n=== Quota Enforcement Scaling ===")

        for count in tenant_counts:
            quota_mgr = TenantQuotaManager()

            # Initialize quotas
            for i in range(count):
                quota_mgr.set_quota(f"tenant_{i}", max_queries=1000)

            # Benchmark checks
            start = time.perf_counter()

            for _ in range(1000):
                tenant = f"tenant_{random.randint(0, count - 1)}"
                quota_mgr.check_quota(tenant, "query")

            total_time = (time.perf_counter() - start) * 1000
            avg_time = total_time / 1000

            print(f"{count} tenants: {avg_time:.4f}ms/check")

            # Should scale reasonably
            self.assertLess(avg_time, 1.0)


class BenchmarkTenantSpecificQueries(unittest.TestCase):
    """Benchmark tenant-specific query performance."""

    def test_tenant_filtered_query(self):
        """Benchmark queries with tenant filtering."""
        from src.database import DatabaseModule
        import tempfile
        import os

        # Create test database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        db = DatabaseModule(db_path=temp_db.name, auto_confirm=True)

        # Create schema with tenant_id
        db.execute_sql(
            """
            CREATE TABLE multi_tenant_data (
                id INTEGER PRIMARY KEY,
                tenant_id TEXT,
                data TEXT
            );
        """
        )

        # Insert test data for multiple tenants
        for tenant_id in range(10):
            for i in range(100):
                db.execute_sql(
                    f"INSERT INTO multi_tenant_data (tenant_id, data) VALUES ('tenant_{tenant_id}', 'data_{i}');"
                )

        # Benchmark tenant-filtered queries
        times = []
        for _ in range(100):
            tenant = f"tenant_{random.randint(0, 9)}"

            start = time.perf_counter()

            result = db.execute_sql(f"SELECT * FROM multi_tenant_data WHERE tenant_id = '{tenant}';")

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Tenant-Filtered Query Performance ===")
        print(f"Tenants: 10")
        print(f"Rows per tenant: 100")
        print(f"Average query time: {avg_time:.2f}ms")

        # Cleanup
        db.close()
        os.unlink(temp_db.name)

        # Filtered queries should be reasonable
        self.assertLess(avg_time, 50.0)

    def test_tenant_isolation_query_performance(self):
        """Benchmark performance impact of tenant isolation."""
        from src.database import DatabaseModule
        import tempfile
        import os

        # Test with isolation
        temp_db1 = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db1.close()

        db_isolated = DatabaseModule(db_path=temp_db1.name, auto_confirm=True)

        db_isolated.execute_sql("CREATE TABLE data (id INTEGER PRIMARY KEY, value TEXT);")
        for i in range(100):
            db_isolated.execute_sql(f"INSERT INTO data (value) VALUES ('value_{i}');")

        # Benchmark with isolation checks
        times_isolated = []
        for _ in range(100):
            start = time.perf_counter()

            # Simulate tenant check before query
            tenant_valid = True  # Tenant validation
            if tenant_valid:
                result = db_isolated.execute_sql("SELECT * FROM data;")

            end = time.perf_counter()
            times_isolated.append((end - start) * 1000)

        # Test without isolation
        temp_db2 = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db2.close()

        db_normal = DatabaseModule(db_path=temp_db2.name, auto_confirm=True)

        db_normal.execute_sql("CREATE TABLE data (id INTEGER PRIMARY KEY, value TEXT);")
        for i in range(100):
            db_normal.execute_sql(f"INSERT INTO data (value) VALUES ('value_{i}');")

        # Benchmark without isolation
        times_normal = []
        for _ in range(100):
            start = time.perf_counter()

            result = db_normal.execute_sql("SELECT * FROM data;")

            end = time.perf_counter()
            times_normal.append((end - start) * 1000)

        avg_isolated = mean(times_isolated)
        avg_normal = mean(times_normal)
        overhead = ((avg_isolated - avg_normal) / avg_normal) * 100

        print(f"\n=== Tenant Isolation Impact ===")
        print(f"With isolation: {avg_isolated:.2f}ms")
        print(f"Without isolation: {avg_normal:.2f}ms")
        print(f"Overhead: {overhead:.2f}%")

        # Cleanup
        db_isolated.close()
        db_normal.close()
        os.unlink(temp_db1.name)
        os.unlink(temp_db2.name)

        # Overhead should be minimal (< 10%)
        self.assertLess(overhead, 10.0)


class BenchmarkDatabaseSeparation(unittest.TestCase):
    """Benchmark database separation per tenant."""

    def test_connection_pool_per_tenant(self):
        """Benchmark connection pool performance per tenant."""
        from src.database.pool import ConnectionPoolManager
        import tempfile

        manager = ConnectionPoolManager()

        # Create separate databases for tenants
        tenant_dbs = {}
        for i in range(10):
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            temp_db.close()
            tenant_dbs[f"tenant_{i}"] = temp_db.name

            manager.create_pool(f"tenant_{i}", f"sqlite:///{temp_db.name}", max_connections=5)

        # Benchmark connection acquisition
        times = []
        for _ in range(1000):
            tenant = f"tenant_{random.randint(0, 9)}"

            start = time.perf_counter()

            conn = manager.get_connection(tenant)
            manager.release_connection(tenant, conn)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Per-Tenant Connection Pool Performance ===")
        print(f"Tenants: 10")
        print(f"Operations: 1000")
        print(f"Average: {avg_time:.2f}ms")

        # Cleanup
        import os

        for db_path in tenant_dbs.values():
            os.unlink(db_path)

        # Connection pooling should be efficient
        self.assertLess(avg_time, 5.0)

    def test_tenant_database_scaling(self):
        """Benchmark scaling with number of tenant databases."""
        from src.core.tenancy import TenantDatabaseManager

        tenant_counts = [5, 10, 20, 50]

        print(f"\n=== Tenant Database Scaling ===")

        for count in tenant_counts:
            db_manager = TenantDatabaseManager()

            # Create tenant databases
            start = time.perf_counter()

            for i in range(count):
                db_manager.create_tenant_database(f"tenant_{i}")

            creation_time = (time.perf_counter() - start) * 1000

            # Benchmark access
            access_times = []
            for _ in range(100):
                tenant = f"tenant_{random.randint(0, count - 1)}"

                start = time.perf_counter()
                conn = db_manager.get_connection(tenant)
                end = time.perf_counter()

                access_times.append((end - start) * 1000)

            avg_access = mean(access_times)

            print(f"{count} tenants: Creation={creation_time:.2f}ms, Avg access={avg_access:.4f}ms")

            # Should scale reasonably
            self.assertLess(avg_access, 2.0)


class BenchmarkTenantResourceUsage(unittest.TestCase):
    """Benchmark tenant resource usage tracking."""

    def test_resource_tracking_overhead(self):
        """Benchmark overhead of resource tracking."""
        from src.core.tenancy import TenantResourceTracker

        tracker = TenantResourceTracker()

        # Initialize tracking for tenants
        for i in range(100):
            tracker.initialize_tenant(f"tenant_{i}")

        times = []
        for _ in range(10000):
            tenant = f"tenant_{random.randint(0, 99)}"
            resource_type = random.choice(["cpu", "memory", "queries", "storage"])
            amount = random.uniform(0.1, 10.0)

            start = time.perf_counter()

            tracker.track_usage(tenant, resource_type, amount)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Resource Tracking Overhead ===")
        print(f"Tenants: 100")
        print(f"Tracking operations: 10000")
        print(f"Average: {avg_time:.4f}ms")

        # Tracking overhead should be minimal
        self.assertLess(avg_time, 0.1)

    def test_resource_reporting_performance(self):
        """Benchmark resource usage reporting."""
        from src.core.tenancy import TenantResourceTracker

        tracker = TenantResourceTracker()

        # Simulate resource usage
        for i in range(100):
            tracker.initialize_tenant(f"tenant_{i}")
            for _ in range(100):
                tracker.track_usage(f"tenant_{i}", "queries", 1)
                tracker.track_usage(f"tenant_{i}", "memory", random.uniform(1, 10))

        # Benchmark reporting
        times = []
        for _ in range(100):
            tenant = f"tenant_{random.randint(0, 99)}"

            start = time.perf_counter()

            report = tracker.get_usage_report(tenant)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n=== Resource Reporting Performance ===")
        print(f"Average: {avg_time:.2f}ms")

        # Reporting should be reasonably fast
        self.assertLess(avg_time, 5.0)


if __name__ == "__main__":
    # Run benchmarks
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
