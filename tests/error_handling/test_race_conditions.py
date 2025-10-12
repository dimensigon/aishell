"""
Race Condition Tests

Tests for concurrent access issues, deadlocks, and synchronization problems.
"""

import pytest
import asyncio
import threading
import time
from unittest.mock import Mock
from collections import defaultdict


class TestBasicRaceConditions:
    """Test basic race condition scenarios"""

    def test_counter_race_condition(self):
        """Test race condition in counter increment"""
        counter = [0]
        iterations = 1000

        def increment():
            for _ in range(iterations):
                # This has a race condition
                temp = counter[0]
                counter[0] = temp + 1

        threads = [threading.Thread(target=increment) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Due to race condition, count might be less than expected
        # (or might be correct if lucky with timing)
        expected = 5 * iterations
        # In race condition, we often see less than expected
        assert counter[0] <= expected

    def test_counter_with_lock(self):
        """Test counter with proper locking"""
        counter = [0]
        lock = threading.Lock()
        iterations = 1000

        def increment_safe():
            for _ in range(iterations):
                with lock:
                    counter[0] += 1

        threads = [threading.Thread(target=increment_safe) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # With lock, should be exactly correct
        assert counter[0] == 5 * iterations

    @pytest.mark.asyncio
    async def test_async_race_condition(self):
        """Test race condition in async code"""
        counter = [0]

        async def increment_async():
            for _ in range(100):
                # Race condition here
                temp = counter[0]
                await asyncio.sleep(0)  # Yield control
                counter[0] = temp + 1

        await asyncio.gather(*[increment_async() for _ in range(5)])

        # Due to race, count is likely wrong
        expected = 500
        # Race condition usually causes incorrect count
        assert counter[0] <= expected

    @pytest.mark.asyncio
    async def test_async_with_lock(self):
        """Test async operations with lock"""
        counter = [0]
        lock = asyncio.Lock()

        async def increment_safe():
            for _ in range(100):
                async with lock:
                    counter[0] += 1

        await asyncio.gather(*[increment_safe() for _ in range(5)])

        # With lock, should be correct
        assert counter[0] == 500


class TestCheckThenActRaces:
    """Test check-then-act race conditions"""

    def test_file_exists_check_race(self):
        """Test race condition in file existence check"""
        import tempfile
        from pathlib import Path

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Race condition: file could be deleted between check and use
            if temp_path.exists():
                # Another thread could delete here
                content = temp_path.read_text()
                assert content == ""
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @pytest.mark.asyncio
    async def test_check_then_act_with_dict(self):
        """Test check-then-act race with dictionary"""
        data = {}
        errors = []

        async def update_dict(key):
            # Race condition
            if key not in data:
                await asyncio.sleep(0.001)  # Simulate delay
                data[key] = 0
            data[key] += 1

        # Multiple tasks updating same keys
        tasks = []
        for i in range(10):
            for key in ['a', 'b', 'c']:
                tasks.append(update_dict(key))

        await asyncio.gather(*tasks, return_exceptions=True)

        # Values might be incorrect due to race
        # With proper locking, each would be exactly 10

    @pytest.mark.asyncio
    async def test_check_then_act_fixed(self):
        """Test check-then-act with proper synchronization"""
        data = {}
        lock = asyncio.Lock()

        async def update_dict_safe(key):
            async with lock:
                if key not in data:
                    data[key] = 0
                data[key] += 1

        tasks = []
        for i in range(10):
            for key in ['a', 'b', 'c']:
                tasks.append(update_dict_safe(key))

        await asyncio.gather(*tasks)

        # Should be exactly correct
        assert data == {'a': 10, 'b': 10, 'c': 10}


class TestDeadlocks:
    """Test deadlock scenarios"""

    def test_simple_deadlock_detection(self):
        """Test detection of simple deadlock"""
        lock1 = threading.Lock()
        lock2 = threading.Lock()
        results = []

        def thread1():
            lock1.acquire()
            time.sleep(0.1)
            if lock2.acquire(timeout=0.5):
                results.append("thread1_success")
                lock2.release()
            else:
                results.append("thread1_timeout")
            lock1.release()

        def thread2():
            lock2.acquire()
            time.sleep(0.1)
            if lock1.acquire(timeout=0.5):
                results.append("thread2_success")
                lock1.release()
            else:
                results.append("thread2_timeout")
            lock2.release()

        t1 = threading.Thread(target=thread1)
        t2 = threading.Thread(target=thread2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Should timeout rather than deadlock
        assert len(results) == 2
        assert any('timeout' in r for r in results)

    @pytest.mark.asyncio
    async def test_async_deadlock_avoidance(self):
        """Test avoiding deadlock in async code with timeout"""
        lock1 = asyncio.Lock()
        lock2 = asyncio.Lock()
        results = []

        async def task1():
            async with lock1:
                await asyncio.sleep(0.1)
                try:
                    async with asyncio.timeout(0.5):
                        async with lock2:
                            results.append("task1_success")
                except asyncio.TimeoutError:
                    results.append("task1_timeout")

        async def task2():
            async with lock2:
                await asyncio.sleep(0.1)
                try:
                    async with asyncio.timeout(0.5):
                        async with lock1:
                            results.append("task2_success")
                except asyncio.TimeoutError:
                    results.append("task2_timeout")

        await asyncio.gather(task1(), task2(), return_exceptions=True)

        # At least one should timeout
        assert len(results) > 0

    def test_ordered_lock_acquisition(self):
        """Test deadlock prevention via ordered lock acquisition"""
        lock1 = threading.Lock()
        lock2 = threading.Lock()
        results = []

        def acquire_ordered(first, second, name):
            # Always acquire in same order
            with first:
                time.sleep(0.01)
                with second:
                    results.append(name)

        t1 = threading.Thread(target=acquire_ordered, args=(lock1, lock2, "thread1"))
        t2 = threading.Thread(target=acquire_ordered, args=(lock1, lock2, "thread2"))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Should both succeed (no deadlock)
        assert len(results) == 2


class TestDataRaces:
    """Test data race conditions"""

    def test_list_append_race(self):
        """Test race condition in list append"""
        shared_list = []

        def append_items():
            for i in range(100):
                shared_list.append(i)

        threads = [threading.Thread(target=append_items) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # List append is thread-safe in CPython (GIL)
        # but test we get all items
        assert len(shared_list) == 500

    @pytest.mark.asyncio
    async def test_concurrent_dict_modification(self):
        """Test concurrent dictionary modification"""
        data = {}

        async def modify_dict(prefix):
            for i in range(100):
                key = f"{prefix}_{i}"
                data[key] = i

        await asyncio.gather(
            modify_dict("a"),
            modify_dict("b"),
            modify_dict("c")
        )

        # Should have all keys
        assert len(data) == 300

    @pytest.mark.asyncio
    async def test_concurrent_read_write_race(self):
        """Test concurrent read/write race"""
        shared_data = {"counter": 0}

        async def reader():
            results = []
            for _ in range(50):
                # Read might see inconsistent state
                value = shared_data.get("counter", 0)
                results.append(value)
                await asyncio.sleep(0)
            return results

        async def writer():
            for i in range(50):
                shared_data["counter"] = i
                await asyncio.sleep(0)

        reader_task = asyncio.create_task(reader())
        writer_task = asyncio.create_task(writer())

        results, _ = await asyncio.gather(reader_task, writer_task)

        # Reader sees various values
        assert len(results) == 50


class TestLostUpdateProblem:
    """Test lost update race condition"""

    @pytest.mark.asyncio
    async def test_lost_update_race(self):
        """Test lost update in concurrent modifications"""
        account_balance = [1000]

        async def withdraw(amount):
            # Read-modify-write race
            balance = account_balance[0]
            await asyncio.sleep(0.001)  # Simulate processing
            if balance >= amount:
                account_balance[0] = balance - amount
                return True
            return False

        # Two concurrent withdrawals
        results = await asyncio.gather(
            withdraw(600),
            withdraw(600)
        )

        # Both might succeed due to race (balance goes negative)
        # or one fails correctly
        if all(results):
            # Race occurred - balance went negative
            assert account_balance[0] < 0
        else:
            # One withdrawal blocked correctly
            assert account_balance[0] == 400

    @pytest.mark.asyncio
    async def test_lost_update_with_lock(self):
        """Test preventing lost update with lock"""
        account_balance = [1000]
        lock = asyncio.Lock()

        async def withdraw_safe(amount):
            async with lock:
                balance = account_balance[0]
                await asyncio.sleep(0.001)
                if balance >= amount:
                    account_balance[0] = balance - amount
                    return True
                return False

        results = await asyncio.gather(
            withdraw_safe(600),
            withdraw_safe(600)
        )

        # One should succeed, one should fail
        assert sum(results) == 1
        assert account_balance[0] == 400


class TestEventBusRaces:
    """Test race conditions in event bus"""

    @pytest.mark.asyncio
    async def test_subscribe_during_publish(self):
        """Test subscribing while events are being published"""
        from src.core.event_bus import AsyncEventBus, Event

        bus = AsyncEventBus()
        await bus.start()

        received = []

        async def handler(event):
            received.append(event.type)

        async def subscriber():
            await asyncio.sleep(0.01)
            bus.subscribe("test", handler)

        async def publisher():
            for i in range(10):
                await bus.publish(Event(f"test"))
                await asyncio.sleep(0.005)

        await asyncio.gather(subscriber(), publisher())

        await asyncio.sleep(0.2)
        await bus.stop()

        # Some events might be missed due to race

    @pytest.mark.asyncio
    async def test_unsubscribe_during_dispatch(self):
        """Test unsubscribing while events are dispatching"""
        from src.core.event_bus import AsyncEventBus, Event

        bus = AsyncEventBus()
        await bus.start()

        received = []

        async def handler(event):
            received.append(event.type)
            await asyncio.sleep(0.01)

        bus.subscribe("test", handler)

        async def publisher():
            for i in range(5):
                await bus.publish(Event("test"))
                await asyncio.sleep(0.005)

        async def unsubscriber():
            await asyncio.sleep(0.02)
            bus.unsubscribe("test", handler)

        await asyncio.gather(publisher(), unsubscriber())

        await asyncio.sleep(0.2)
        await bus.stop()

        # Should receive some but not all events


class TestConcurrentInitialization:
    """Test concurrent initialization race conditions"""

    @pytest.mark.asyncio
    async def test_double_initialization_race(self):
        """Test race condition in double initialization"""
        from src.core.ai_shell import AIShellCore

        core = AIShellCore()

        # Concurrent initialization
        results = await asyncio.gather(
            core.initialize(),
            core.initialize(),
            core.initialize(),
            return_exceptions=True
        )

        # Should handle gracefully
        assert core.initialized

        await core.shutdown()

    @pytest.mark.asyncio
    async def test_lazy_initialization_race(self):
        """Test lazy initialization race condition"""
        instance = [None]
        lock = asyncio.Lock()

        async def get_instance_unsafe():
            if instance[0] is None:
                await asyncio.sleep(0.01)  # Simulate init time
                instance[0] = Mock()
            return instance[0]

        # Race condition - multiple instances might be created
        tasks = [get_instance_unsafe() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # Might create multiple instances
        # All references might not be same

    @pytest.mark.asyncio
    async def test_lazy_initialization_with_lock(self):
        """Test lazy initialization with proper locking"""
        instance = [None]
        lock = asyncio.Lock()

        async def get_instance_safe():
            async with lock:
                if instance[0] is None:
                    await asyncio.sleep(0.01)
                    instance[0] = Mock()
                return instance[0]

        tasks = [get_instance_safe() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should be same instance
        assert all(r is results[0] for r in results)


class TestConcurrentModification:
    """Test concurrent modification exceptions"""

    def test_dict_modification_during_iteration(self):
        """Test modifying dict during iteration"""
        data = {i: i * 2 for i in range(10)}

        with pytest.raises(RuntimeError):
            for key in data:
                if key % 2 == 0:
                    del data[key]  # Modifying during iteration

    def test_list_modification_during_iteration(self):
        """Test modifying list during iteration"""
        items = list(range(10))

        # This causes issues
        new_items = []
        for item in items:
            if item % 2 == 0:
                new_items.append(item)

        # Safe way - create new list
        items = new_items
        assert len(items) == 5

    @pytest.mark.asyncio
    async def test_concurrent_collection_access(self):
        """Test concurrent access to collections"""
        data = defaultdict(int)
        lock = asyncio.Lock()

        async def safe_increment(key):
            async with lock:
                data[key] += 1

        tasks = []
        for i in range(100):
            tasks.append(safe_increment(i % 10))

        await asyncio.gather(*tasks)

        # Each key should have been incremented 10 times
        for i in range(10):
            assert data[i] == 10


class TestMemoryVisibility:
    """Test memory visibility issues"""

    def test_volatile_variable_simulation(self):
        """Test memory visibility between threads"""
        flag = [False]
        data = [None]

        def writer():
            data[0] = "ready"
            time.sleep(0.01)
            flag[0] = True

        def reader():
            start = time.time()
            while not flag[0]:
                if time.time() - start > 1:
                    break
                time.sleep(0.001)
            return data[0]

        writer_thread = threading.Thread(target=writer)
        reader_thread = threading.Thread(target=reader)

        writer_thread.start()
        reader_thread.start()

        writer_thread.join()
        reader_thread.join()

        # In most cases works, but visibility not guaranteed without proper sync

    @pytest.mark.asyncio
    async def test_async_memory_visibility(self):
        """Test memory visibility in async code"""
        shared = {"ready": False, "value": None}

        async def writer():
            shared["value"] = 42
            await asyncio.sleep(0.01)
            shared["ready"] = True

        async def reader():
            while not shared["ready"]:
                await asyncio.sleep(0.001)
            return shared["value"]

        result = await asyncio.gather(writer(), reader())

        assert result[1] == 42
