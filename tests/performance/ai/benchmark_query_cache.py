"""Performance benchmarks for Query Cache System.

Measures:
- Cache hit/miss performance
- Cache size impact on performance
- TTL expiration overhead
- Compression performance
- Pattern invalidation speed
"""

import unittest
import time
import random
import string
from statistics import mean, stdev
import json


class BenchmarkQueryCache(unittest.TestCase):
    """Benchmark query cache performance."""

    def setUp(self):
        """Set up benchmark fixtures."""
        self.iterations = 1000
        self.cache_sizes = [100, 1000, 10000]

    def generate_random_query(self, size=100):
        """Generate random query string."""
        return "SELECT * FROM " + "".join(random.choices(string.ascii_letters, k=size))

    def generate_large_result(self, rows=100, cols=10):
        """Generate large result set."""
        return {
            "results": [
                {f"col_{j}": f"value_{i}_{j}" for j in range(cols)} for i in range(rows)
            ],
            "count": rows,
        }

    def test_cache_set_performance(self):
        """Benchmark cache SET operations."""
        from src.performance.cache import QueryCache

        cache = QueryCache(backend="memory", ttl=300)

        times = []
        for _ in range(self.iterations):
            key = self.generate_random_query()
            data = {"result": "test"}

            start = time.perf_counter()
            cache.set(key, data)
            end = time.perf_counter()

            times.append((end - start) * 1000)  # Convert to ms

        avg_time = mean(times)
        std_time = stdev(times)

        print(f"\n=== Cache SET Performance ===")
        print(f"Iterations: {self.iterations}")
        print(f"Average time: {avg_time:.4f}ms")
        print(f"Std deviation: {std_time:.4f}ms")
        print(f"Min/Max: {min(times):.4f}ms / {max(times):.4f}ms")

        # Should be very fast (< 1ms)
        self.assertLess(avg_time, 1.0)

    def test_cache_get_hit_performance(self):
        """Benchmark cache GET operations (cache hits)."""
        from src.performance.cache import QueryCache

        cache = QueryCache(backend="memory", ttl=300)

        # Pre-populate cache
        test_key = "SELECT * FROM users"
        test_data = {"result": "cached"}
        cache.set(test_key, test_data)

        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = cache.get(test_key)
            end = time.perf_counter()

            times.append((end - start) * 1000)
            self.assertIsNotNone(result)

        avg_time = mean(times)
        std_time = stdev(times)

        print(f"\n=== Cache GET (Hit) Performance ===")
        print(f"Iterations: {self.iterations}")
        print(f"Average time: {avg_time:.4f}ms")
        print(f"Std deviation: {std_time:.4f}ms")

        # Cache hits should be extremely fast (< 0.1ms)
        self.assertLess(avg_time, 0.1)

    def test_cache_get_miss_performance(self):
        """Benchmark cache GET operations (cache misses)."""
        from src.performance.cache import QueryCache

        cache = QueryCache(backend="memory", ttl=300)

        times = []
        for _ in range(self.iterations):
            key = self.generate_random_query()

            start = time.perf_counter()
            result = cache.get(key)
            end = time.perf_counter()

            times.append((end - start) * 1000)
            self.assertIsNone(result)

        avg_time = mean(times)

        print(f"\n=== Cache GET (Miss) Performance ===")
        print(f"Iterations: {self.iterations}")
        print(f"Average time: {avg_time:.4f}ms")

        # Cache misses should still be fast (< 0.5ms)
        self.assertLess(avg_time, 0.5)

    def test_cache_size_impact(self):
        """Benchmark impact of cache size on performance."""
        from src.performance.cache import QueryCache

        print(f"\n=== Cache Size Impact ===")

        for size in self.cache_sizes:
            cache = QueryCache(backend="memory", ttl=300)

            # Populate cache
            keys = []
            for i in range(size):
                key = f"query_{i}"
                cache.set(key, {"data": f"result_{i}"})
                keys.append(key)

            # Benchmark random access
            times = []
            for _ in range(100):
                key = random.choice(keys)

                start = time.perf_counter()
                cache.get(key)
                end = time.perf_counter()

                times.append((end - start) * 1000)

            avg_time = mean(times)
            print(f"Cache size {size}: Average GET time = {avg_time:.4f}ms")

            # Should scale reasonably
            self.assertLess(avg_time, 1.0)

    def test_compression_performance(self):
        """Benchmark compression overhead."""
        from src.performance.cache import QueryCache

        # Large result set
        large_data = self.generate_large_result(rows=1000, cols=20)

        # Without compression
        cache_no_comp = QueryCache(backend="memory", ttl=300, compression=False)

        start = time.perf_counter()
        cache_no_comp.set("large_query", large_data)
        no_comp_set_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        cache_no_comp.get("large_query")
        no_comp_get_time = (time.perf_counter() - start) * 1000

        # With compression
        cache_comp = QueryCache(backend="memory", ttl=300, compression=True)

        start = time.perf_counter()
        cache_comp.set("large_query", large_data)
        comp_set_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        cache_comp.get("large_query")
        comp_get_time = (time.perf_counter() - start) * 1000

        print(f"\n=== Compression Performance (1000 rows x 20 cols) ===")
        print(f"No compression - SET: {no_comp_set_time:.4f}ms, GET: {no_comp_get_time:.4f}ms")
        print(f"With compression - SET: {comp_set_time:.4f}ms, GET: {comp_get_time:.4f}ms")
        print(f"SET overhead: {((comp_set_time / no_comp_set_time - 1) * 100):.2f}%")
        print(f"GET overhead: {((comp_get_time / no_comp_get_time - 1) * 100):.2f}%")

    def test_pattern_invalidation_performance(self):
        """Benchmark pattern-based cache invalidation."""
        from src.performance.cache import QueryCache

        cache = QueryCache(backend="memory", ttl=300)

        # Populate with various keys
        for i in range(1000):
            cache.set(f"users:query:{i}", {"data": i})

        for i in range(1000):
            cache.set(f"products:query:{i}", {"data": i})

        # Benchmark pattern invalidation
        start = time.perf_counter()
        cache.invalidate_pattern("users:*")
        invalidation_time = (time.perf_counter() - start) * 1000

        print(f"\n=== Pattern Invalidation Performance ===")
        print(f"Invalidated pattern: users:* (1000 keys)")
        print(f"Time: {invalidation_time:.4f}ms")

        # Verify users queries are gone
        self.assertIsNone(cache.get("users:query:0"))

        # Products should still be there
        self.assertIsNotNone(cache.get("products:query:0"))

        # Should be reasonably fast (< 50ms for 1000 keys)
        self.assertLess(invalidation_time, 50.0)

    def test_ttl_expiration_performance(self):
        """Benchmark TTL expiration checking."""
        from src.performance.cache import QueryCache

        cache = QueryCache(backend="memory", ttl=1)  # 1 second TTL

        # Add items
        for i in range(100):
            cache.set(f"key_{i}", {"data": i})

        # Wait for expiration
        time.sleep(1.1)

        # Benchmark access after expiration
        times = []
        for i in range(100):
            start = time.perf_counter()
            result = cache.get(f"key_{i}")
            end = time.perf_counter()

            times.append((end - start) * 1000)
            self.assertIsNone(result)  # Should be expired

        avg_time = mean(times)

        print(f"\n=== TTL Expiration Check Performance ===")
        print(f"Average time: {avg_time:.4f}ms")

        # Expiration check should be fast
        self.assertLess(avg_time, 0.5)

    def test_concurrent_access_simulation(self):
        """Benchmark simulated concurrent access."""
        from src.performance.cache import QueryCache
        import threading

        cache = QueryCache(backend="memory", ttl=300)

        # Pre-populate
        for i in range(100):
            cache.set(f"query_{i}", {"result": i})

        results = {"times": []}

        def access_cache(thread_id):
            """Simulate cache access."""
            times = []
            for _ in range(100):
                key = f"query_{random.randint(0, 99)}"

                start = time.perf_counter()
                cache.get(key)
                end = time.perf_counter()

                times.append((end - start) * 1000)

            results["times"].extend(times)

        # Simulate 10 concurrent threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=access_cache, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        avg_time = mean(results["times"])
        std_time = stdev(results["times"])

        print(f"\n=== Concurrent Access Performance (10 threads) ===")
        print(f"Total operations: {len(results['times'])}")
        print(f"Average time: {avg_time:.4f}ms")
        print(f"Std deviation: {std_time:.4f}ms")

        # Should handle concurrent access well
        self.assertLess(avg_time, 1.0)


class BenchmarkCacheStatistics(unittest.TestCase):
    """Benchmark cache statistics tracking."""

    def test_statistics_overhead(self):
        """Benchmark overhead of statistics tracking."""
        from src.performance.cache import QueryCache

        cache = QueryCache(backend="memory", ttl=300, track_stats=True)

        # Populate cache
        for i in range(1000):
            cache.set(f"key_{i}", {"data": i})

        # Benchmark with statistics
        start = time.perf_counter()
        for _ in range(1000):
            cache.get(f"key_{random.randint(0, 999)}")
        stats_time = (time.perf_counter() - start) * 1000

        # Get statistics
        stats = cache.get_statistics()

        print(f"\n=== Statistics Tracking Overhead ===")
        print(f"1000 operations with stats: {stats_time:.4f}ms")
        print(f"Stats: {stats}")

        # Statistics overhead should be minimal
        self.assertLess(stats_time, 100.0)


if __name__ == "__main__":
    # Run benchmarks
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
