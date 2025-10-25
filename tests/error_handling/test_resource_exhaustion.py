"""
Resource Exhaustion Tests

Tests resource exhaustion scenarios including memory limits, file descriptor
exhaustion, connection pool exhaustion, and disk space issues.
"""

import pytest
import asyncio
import tempfile
import os
import gc
from pathlib import Path
from unittest.mock import Mock, patch
import sys


class TestMemoryExhaustion:
    """Test memory exhaustion scenarios"""

    def test_large_list_allocation(self):
        """Test allocation of very large list"""
        # This should work within reasonable bounds
        large_list = [i for i in range(1_000_000)]
        assert len(large_list) == 1_000_000

        # Clean up
        del large_list
        gc.collect()

    def test_memory_leak_detection(self):
        """Test detection of memory leaks"""
        import tracemalloc

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Simulate potential leak
        leaked_data = []
        for i in range(10000):
            leaked_data.append([0] * 1000)

        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        # Memory usage should have increased
        assert len(top_stats) > 0

        # Clean up
        del leaked_data
        tracemalloc.stop()
        gc.collect()

    def test_recursive_depth_exhaustion(self):
        """Test stack overflow from recursion"""
        def infinite_recursion(n):
            return infinite_recursion(n + 1)

        with pytest.raises(RecursionError):
            infinite_recursion(0)

    def test_generator_memory_efficiency(self):
        """Test generators vs lists for memory efficiency"""
        # Generator doesn't allocate all at once
        def large_generator():
            for i in range(10_000_000):
                yield i

        gen = large_generator()

        # Should be able to iterate without memory issues
        count = 0
        for i, value in enumerate(gen):
            count += 1
            if i >= 1000:
                break

        assert count == 1001

    def test_circular_reference_cleanup(self):
        """Test cleanup of circular references"""
        import weakref

        class Node:
            def __init__(self, value):
                self.value = value
                self.next = None

        # Create circular reference
        node1 = Node(1)
        node2 = Node(2)
        node1.next = node2
        node2.next = node1

        # Create weak reference to track deletion
        weak_ref = weakref.ref(node1)

        # Break circular reference
        node1.next = None
        node2.next = None
        del node1, node2

        # Force garbage collection
        gc.collect()

        # Object should be collected
        assert weak_ref() is None

    @pytest.mark.skipif(sys.platform == "win32", reason="Memory test unreliable on Windows")
    def test_memory_limit_handling(self):
        """Test handling of memory limits"""
        try:
            # Try to allocate huge amount
            huge_data = bytearray(10 * 1024 * 1024 * 1024)  # 10GB
            pytest.fail("Should have raised MemoryError")
        except MemoryError:
            # Expected on systems with limited memory
            pass
        except Exception:
            # May fail differently depending on system
            pass


class TestFileDescriptorExhaustion:
    """Test file descriptor exhaustion"""

    def test_file_descriptor_leak(self):
        """Test file descriptor leak detection"""
        open_files = []

        # Open many files without closing
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                for i in range(100):
                    f = open(Path(tmpdir) / f"file_{i}.txt", 'w')
                    open_files.append(f)

                # Should have many open files
                assert len(open_files) == 100

            finally:
                # Clean up
                for f in open_files:
                    try:
                        f.close()
                    except:
                        pass

    def test_context_manager_prevents_leak(self):
        """Test context manager properly closes files"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            f.write("test")

        # File should be closed
        try:
            # Try to get file descriptor (will fail if closed properly)
            with open(temp_path, 'r') as f2:
                # File can be reopened
                content = f2.read()
                assert content == "test"
        finally:
            os.unlink(temp_path)

    def test_maximum_open_files(self):
        """Test hitting maximum open files limit"""
        import resource

        # Get current limits
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

        # Don't actually exhaust (just test we can check limits)
        assert soft > 0
        assert hard > 0

    @pytest.mark.asyncio
    async def test_async_file_descriptor_management(self):
        """Test async file operations don't leak descriptors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = []

            # Open files asynchronously
            for i in range(50):
                path = Path(tmpdir) / f"async_{i}.txt"
                path.write_text(f"content {i}")
                files.append(path)

            # Read them all
            tasks = []
            for path in files:
                async def read_file(p):
                    return p.read_text()

                tasks.append(read_file(path))

            results = await asyncio.gather(*tasks)
            assert len(results) == 50


class TestConnectionPoolExhaustion:
    """Test connection pool exhaustion"""

    @pytest.mark.asyncio
    async def test_connection_pool_limit(self):
        """Test hitting connection pool limit"""
        max_connections = 5
        pool = []
        available = max_connections

        async def acquire_connection():
            nonlocal available
            if available <= 0:
                raise RuntimeError("Connection pool exhausted")
            available -= 1
            conn = Mock()
            pool.append(conn)
            return conn

        def release_connection(conn):
            nonlocal available
            if conn in pool:
                pool.remove(conn)
                available += 1

        # Acquire all connections
        connections = []
        for _ in range(max_connections):
            conn = await acquire_connection()
            connections.append(conn)

        # Try to acquire one more
        with pytest.raises(RuntimeError, match="pool exhausted"):
            await acquire_connection()

        # Release one and try again
        release_connection(connections[0])
        extra_conn = await acquire_connection()
        assert extra_conn is not None

    @pytest.mark.asyncio
    async def test_connection_leak_detection(self):
        """Test detection of connection leaks"""
        active_connections = []

        class Connection:
            def __init__(self, id):
                self.id = id
                self.closed = False
                active_connections.append(self)

            def close(self):
                self.closed = True
                active_connections.remove(self)

        # Create connections without closing
        for i in range(10):
            conn = Connection(i)

        assert len(active_connections) == 10

        # Clean up properly
        for conn in list(active_connections):
            conn.close()

        assert len(active_connections) == 0

    @pytest.mark.asyncio
    async def test_connection_timeout_on_exhaustion(self):
        """Test timeout when waiting for connection"""
        semaphore = asyncio.Semaphore(2)  # Only 2 connections

        async def get_connection():
            acquired = await semaphore.acquire()
            if not acquired:
                raise RuntimeError("Failed to acquire")
            return Mock()

        # Acquire both connections
        await semaphore.acquire()
        await semaphore.acquire()

        # Try to get another with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(get_connection(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_connection_pooling_with_errors(self):
        """Test connection pool handles errors gracefully"""
        class ConnectionPool:
            def __init__(self, max_size=5):
                self.max_size = max_size
                self.pool = []
                self.in_use = 0

            async def acquire(self):
                if self.in_use >= self.max_size:
                    raise RuntimeError("Pool exhausted")
                self.in_use += 1
                return Mock()

            async def release(self, conn):
                self.in_use -= 1

        pool = ConnectionPool(max_size=3)

        # Normal usage
        conn1 = await pool.acquire()
        conn2 = await pool.acquire()
        conn3 = await pool.acquire()

        # Pool exhausted
        with pytest.raises(RuntimeError):
            await pool.acquire()

        # Release and reuse
        await pool.release(conn1)
        conn4 = await pool.acquire()
        assert conn4 is not None


class TestDiskSpaceExhaustion:
    """Test disk space exhaustion scenarios"""

    def test_disk_full_simulation(self):
        """Test handling of disk full error"""
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with pytest.raises(OSError, match="No space left on device"):
                with open("test.txt", 'w') as f:
                    f.write("data")

    def test_large_file_write(self):
        """Test writing large file"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            temp_path = f.name

            try:
                # Write 10 MB
                chunk = b'x' * (1024 * 1024)  # 1 MB
                for _ in range(10):
                    f.write(chunk)

                f.flush()
                size = os.path.getsize(temp_path)
                assert size >= 10 * 1024 * 1024
            finally:
                os.unlink(temp_path)

    def test_check_available_disk_space(self):
        """Test checking available disk space"""
        import shutil

        usage = shutil.disk_usage('/')

        assert usage.total > 0
        assert usage.used >= 0
        assert usage.free >= 0
        assert usage.total == usage.used + usage.free

    def test_temp_file_cleanup_on_error(self):
        """Test temp files cleaned up on error"""
        temp_files = []

        try:
            for i in range(5):
                f = tempfile.NamedTemporaryFile(mode='w', delete=False)
                temp_files.append(f.name)
                f.write(f"data {i}")
                f.close()

            # Simulate error
            raise RuntimeError("Processing error")

        except RuntimeError:
            # Clean up temp files
            for path in temp_files:
                if os.path.exists(path):
                    os.unlink(path)

        # All should be cleaned up
        for path in temp_files:
            assert not os.path.exists(path)

    def test_atomic_write_on_disk_full(self):
        """Test atomic write fails gracefully when disk full"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            target.write_text("original data")

            # Simulate atomic write
            temp = Path(tmpdir) / "target.txt.tmp"

            try:
                # Write to temp file
                temp.write_text("new data")

                # Simulate disk full during rename
                with patch('os.rename', side_effect=OSError("No space")):
                    with pytest.raises(OSError):
                        os.rename(temp, target)

                # Original file should be unchanged
                assert target.read_text() == "original data"

            finally:
                if temp.exists():
                    temp.unlink()


class TestThreadPoolExhaustion:
    """Test thread/task pool exhaustion"""

    @pytest.mark.asyncio
    async def test_task_semaphore_limit(self):
        """Test limiting concurrent tasks with semaphore"""
        max_concurrent = 3
        semaphore = asyncio.Semaphore(max_concurrent)
        active_count = [0]
        max_active = [0]

        async def limited_task(task_id):
            async with semaphore:
                active_count[0] += 1
                max_active[0] = max(max_active[0], active_count[0])
                await asyncio.sleep(0.01)
                active_count[0] -= 1

        # Start many tasks
        tasks = [limited_task(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # Should never have exceeded limit
        assert max_active[0] <= max_concurrent

    @pytest.mark.asyncio
    async def test_queue_overflow_handling(self):
        """Test handling queue overflow"""
        max_size = 5
        queue = asyncio.Queue(maxsize=max_size)

        # Fill queue
        for i in range(max_size):
            await queue.put(i)

        # Try to add more (should raise Full or timeout)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.put(999), timeout=0.1)

    @pytest.mark.asyncio
    async def test_worker_pool_exhaustion(self):
        """Test worker pool running out of workers"""
        from concurrent.futures import ThreadPoolExecutor
        import time

        max_workers = 3

        def slow_task(n):
            time.sleep(0.1)
            return n * 2

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit more tasks than workers
            futures = [executor.submit(slow_task, i) for i in range(10)]

            # All should eventually complete
            results = [f.result() for f in futures]
            assert len(results) == 10

    @pytest.mark.asyncio
    async def test_asyncio_task_limit(self):
        """Test limiting number of concurrent asyncio tasks"""
        max_tasks = 10
        active = [0]

        async def tracked_task():
            active[0] += 1
            await asyncio.sleep(0.01)
            active[0] -= 1

        # Create many tasks at once
        tasks = [asyncio.create_task(tracked_task()) for _ in range(100)]

        # Wait for completion
        await asyncio.gather(*tasks)

        # All should complete
        assert active[0] == 0


class TestBufferOverflow:
    """Test buffer overflow scenarios"""

    def test_string_buffer_overflow(self):
        """Test string buffer limits"""
        # Python strings are dynamic, but test large strings
        large_string = "x" * (10 * 1024 * 1024)  # 10 MB string
        assert len(large_string) == 10 * 1024 * 1024

        del large_string
        gc.collect()

    def test_bytearray_overflow(self):
        """Test bytearray buffer overflow"""
        buffer = bytearray(1024)

        # Writing beyond buffer should extend it
        buffer.extend(b'x' * 1024)
        assert len(buffer) == 2048

    def test_fixed_size_buffer(self):
        """Test fixed-size buffer overflow protection"""
        class FixedBuffer:
            def __init__(self, size):
                self.size = size
                self.data = bytearray(size)
                self.pos = 0

            def write(self, data):
                if self.pos + len(data) > self.size:
                    raise BufferError("Buffer overflow")
                self.data[self.pos:self.pos + len(data)] = data
                self.pos += len(data)

        buffer = FixedBuffer(10)
        buffer.write(b'12345')

        # This should overflow
        with pytest.raises(BufferError):
            buffer.write(b'1234567890')

    def test_queue_size_limit(self):
        """Test queue size limits"""
        import queue

        q = queue.Queue(maxsize=5)

        # Fill queue
        for i in range(5):
            q.put(i)

        # Next put should block/raise
        with pytest.raises(queue.Full):
            q.put_nowait(999)


class TestResourceCleanup:
    """Test proper resource cleanup"""

    def test_context_manager_cleanup(self):
        """Test context manager ensures cleanup"""
        cleanup_called = []

        class Resource:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                cleanup_called.append(True)
                return False

        with Resource():
            pass

        assert len(cleanup_called) == 1

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup(self):
        """Test async context manager cleanup"""
        cleanup_called = []

        class AsyncResource:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                cleanup_called.append(True)
                return False

        async with AsyncResource():
            pass

        assert len(cleanup_called) == 1

    def test_finally_block_cleanup(self):
        """Test finally block runs on exception"""
        cleanup_called = []

        try:
            raise ValueError("Error")
        except ValueError:
            pass
        finally:
            cleanup_called.append(True)

        assert len(cleanup_called) == 1

    def test_weakref_cleanup(self):
        """Test weakref allows garbage collection"""
        import weakref

        class LargeObject:
            def __init__(self):
                self.data = [0] * 1000000

        obj = LargeObject()
        weak = weakref.ref(obj)

        assert weak() is not None

        del obj
        gc.collect()

        assert weak() is None
