"""Comprehensive tests for plugin hook system."""

import pytest
from unittest.mock import Mock, call

from src.plugins.hooks import Hook, HookManager


class TestHook:
    """Test suite for Hook class."""

    def test_hook_initialization(self):
        """Test hook initialization."""
        callback = Mock()
        hook = Hook(callback, priority=10)

        assert hook.callback == callback
        assert hook.priority == 10

    def test_hook_default_priority(self):
        """Test hook with default priority."""
        callback = Mock()
        hook = Hook(callback)

        assert hook.priority == 0


class TestHookManager:
    """Test suite for HookManager class."""

    @pytest.fixture
    def manager(self):
        """Create a hook manager instance."""
        return HookManager()

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert hasattr(manager, '_hooks')
        assert len(manager._hooks) == 0

    def test_register_hook_basic(self, manager):
        """Test basic hook registration."""
        callback = Mock()
        manager.register_hook("test_event", callback)

        assert manager.has_hooks("test_event")
        assert manager.get_hook_count("test_event") == 1

    def test_register_multiple_hooks(self, manager):
        """Test registering multiple hooks for same event."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        manager.register_hook("test_event", callback1)
        manager.register_hook("test_event", callback2)
        manager.register_hook("test_event", callback3)

        assert manager.get_hook_count("test_event") == 3

    def test_register_hooks_with_priority(self, manager):
        """Test hook registration with priorities."""
        callback_high = Mock(return_value="high")
        callback_medium = Mock(return_value="medium")
        callback_low = Mock(return_value="low")

        manager.register_hook("test_event", callback_low, priority=1)
        manager.register_hook("test_event", callback_high, priority=10)
        manager.register_hook("test_event", callback_medium, priority=5)

        # Execute and check order
        manager.execute_hook("test_event", "data")

        # Higher priority should execute first
        assert callback_high.called
        assert callback_medium.called
        assert callback_low.called

    def test_unregister_hook_success(self, manager):
        """Test successful hook unregistration."""
        callback = Mock()
        manager.register_hook("test_event", callback)

        result = manager.unregister_hook("test_event", callback)

        assert result is True
        assert manager.get_hook_count("test_event") == 0

    def test_unregister_hook_not_found(self, manager):
        """Test unregistering non-existent hook."""
        callback = Mock()

        result = manager.unregister_hook("test_event", callback)

        assert result is False

    def test_unregister_hook_wrong_event(self, manager):
        """Test unregistering hook from wrong event."""
        callback = Mock()
        manager.register_hook("event1", callback)

        result = manager.unregister_hook("event2", callback)

        assert result is False
        assert manager.get_hook_count("event1") == 1

    def test_execute_hook_no_hooks(self, manager):
        """Test executing hook with no registered hooks."""
        result = manager.execute_hook("nonexistent", "data")

        assert result == "data"

    def test_execute_hook_single(self, manager):
        """Test executing single hook."""
        callback = Mock(return_value="modified")
        manager.register_hook("test_event", callback)

        result = manager.execute_hook("test_event", "original")

        callback.assert_called_once_with("original")
        assert result == "modified"

    def test_execute_hook_chain(self, manager):
        """Test executing chain of hooks."""
        def add_prefix(data):
            return f"prefix_{data}"

        def add_suffix(data):
            return f"{data}_suffix"

        def to_upper(data):
            return data.upper()

        manager.register_hook("test_event", add_prefix)
        manager.register_hook("test_event", add_suffix)
        manager.register_hook("test_event", to_upper)

        result = manager.execute_hook("test_event", "data")

        # Should chain through all hooks
        assert "PREFIX" in result
        assert "DATA" in result
        assert "SUFFIX" in result

    def test_execute_hook_with_exception(self, manager):
        """Test hook execution with exception in callback."""
        def failing_callback(data):
            raise ValueError("Hook error")

        callback_after = Mock(return_value="after")

        manager.register_hook("test_event", failing_callback)
        manager.register_hook("test_event", callback_after)

        # Should not raise, but log error
        result = manager.execute_hook("test_event", "data")

        # Should continue to next hook
        callback_after.assert_called_once()

    def test_execute_hook_priority_order(self, manager):
        """Test that hooks execute in priority order."""
        execution_order = []

        def make_callback(name):
            def callback(data):
                execution_order.append(name)
                return data
            return callback

        manager.register_hook("test", make_callback("low"), priority=1)
        manager.register_hook("test", make_callback("high"), priority=100)
        manager.register_hook("test", make_callback("medium"), priority=50)

        manager.execute_hook("test", "data")

        assert execution_order == ["high", "medium", "low"]

    def test_execute_hooks_async_no_hooks(self, manager):
        """Test async execution with no hooks."""
        results = manager.execute_hooks_async("nonexistent", "data")

        assert results == []

    def test_execute_hooks_async_multiple(self, manager):
        """Test async execution with multiple hooks."""
        callback1 = Mock(return_value="result1")
        callback2 = Mock(return_value="result2")
        callback3 = Mock(return_value="result3")

        manager.register_hook("test", callback1)
        manager.register_hook("test", callback2)
        manager.register_hook("test", callback3)

        results = manager.execute_hooks_async("test", "data")

        assert len(results) == 3
        assert "result1" in results
        assert "result2" in results
        assert "result3" in results

    def test_execute_hooks_async_with_error(self, manager):
        """Test async execution with error in one hook."""
        callback_ok = Mock(return_value="ok")

        def failing_callback(data):
            raise RuntimeError("Async error")

        manager.register_hook("test", callback_ok)
        manager.register_hook("test", failing_callback)

        results = manager.execute_hooks_async("test", "data")

        # Should have 2 results, one None for error
        assert len(results) == 2
        assert "ok" in results
        assert None in results

    def test_has_hooks_true(self, manager):
        """Test has_hooks returns True when hooks exist."""
        callback = Mock()
        manager.register_hook("test", callback)

        assert manager.has_hooks("test") is True

    def test_has_hooks_false(self, manager):
        """Test has_hooks returns False when no hooks."""
        assert manager.has_hooks("nonexistent") is False

    def test_get_hook_count_zero(self, manager):
        """Test get_hook_count with no hooks."""
        count = manager.get_hook_count("nonexistent")
        assert count == 0

    def test_get_hook_count_multiple(self, manager):
        """Test get_hook_count with multiple hooks."""
        for i in range(5):
            manager.register_hook("test", Mock())

        count = manager.get_hook_count("test")
        assert count == 5

    def test_clear_hooks_specific_event(self, manager):
        """Test clearing hooks for specific event."""
        manager.register_hook("event1", Mock())
        manager.register_hook("event1", Mock())
        manager.register_hook("event2", Mock())

        manager.clear_hooks("event1")

        assert manager.get_hook_count("event1") == 0
        assert manager.get_hook_count("event2") == 1

    def test_clear_hooks_all_events(self, manager):
        """Test clearing all hooks."""
        manager.register_hook("event1", Mock())
        manager.register_hook("event2", Mock())
        manager.register_hook("event3", Mock())

        manager.clear_hooks()

        assert manager.get_hook_count("event1") == 0
        assert manager.get_hook_count("event2") == 0
        assert manager.get_hook_count("event3") == 0

    def test_clear_hooks_nonexistent(self, manager):
        """Test clearing hooks for non-existent event."""
        # Should not raise error
        manager.clear_hooks("nonexistent")

        assert manager.get_hook_count("nonexistent") == 0

    def test_hook_with_complex_data(self, manager):
        """Test hook execution with complex data types."""
        def modify_dict(data):
            data["modified"] = True
            return data

        manager.register_hook("test", modify_dict)

        input_data = {"value": 100, "items": [1, 2, 3]}
        result = manager.execute_hook("test", input_data)

        assert result["modified"] is True
        assert result["value"] == 100

    def test_hook_with_none_data(self, manager):
        """Test hook execution with None data."""
        callback = Mock(return_value=None)
        manager.register_hook("test", callback)

        result = manager.execute_hook("test", None)

        callback.assert_called_once_with(None)
        assert result is None

    def test_multiple_events_independent(self, manager):
        """Test that different events maintain independent hook lists."""
        callback1 = Mock()
        callback2 = Mock()

        manager.register_hook("event1", callback1)
        manager.register_hook("event2", callback2)

        manager.execute_hook("event1", "data1")

        callback1.assert_called_once()
        callback2.assert_not_called()

    def test_hook_registration_same_callback_multiple_events(self, manager):
        """Test registering same callback for multiple events."""
        callback = Mock(return_value="result")

        manager.register_hook("event1", callback)
        manager.register_hook("event2", callback)

        result1 = manager.execute_hook("event1", "data1")
        result2 = manager.execute_hook("event2", "data2")

        assert callback.call_count == 2
        assert result1 == "result"
        assert result2 == "result"

    def test_hook_priority_same_value(self, manager):
        """Test hooks with same priority value."""
        callback1 = Mock(return_value="first")
        callback2 = Mock(return_value="second")

        manager.register_hook("test", callback1, priority=10)
        manager.register_hook("test", callback2, priority=10)

        # Both should execute, order might vary
        manager.execute_hook("test", "data")

        assert callback1.called
        assert callback2.called


class TestHookManagerEdgeCases:
    """Test edge cases in hook management."""

    @pytest.fixture
    def manager(self):
        """Create a hook manager instance."""
        return HookManager()

    def test_concurrent_hook_registration(self, manager):
        """Test concurrent hook registrations."""
        import concurrent.futures

        callbacks = [Mock() for _ in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(manager.register_hook, "test", cb)
                      for cb in callbacks]
            [f.result() for f in concurrent.futures.as_completed(futures)]

        assert manager.get_hook_count("test") == 10

    def test_concurrent_hook_execution(self, manager):
        """Test concurrent hook executions."""
        import concurrent.futures

        callback = Mock(return_value="result")
        manager.register_hook("test", callback)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(manager.execute_hook, "test", f"data_{i}")
                      for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 10
        assert callback.call_count == 10

    def test_hook_with_lambda(self, manager):
        """Test registering lambda functions as hooks."""
        manager.register_hook("test", lambda x: x * 2)

        result = manager.execute_hook("test", 21)
        assert result == 42

    def test_hook_returning_different_type(self, manager):
        """Test hook that changes data type."""
        def to_string(data):
            return str(data)

        manager.register_hook("test", to_string)

        result = manager.execute_hook("test", 42)
        assert result == "42"
        assert isinstance(result, str)

    def test_unregister_during_execution(self, manager):
        """Test unregistering hook during execution."""
        callback1 = Mock(return_value="first")
        callback2 = Mock(return_value="second")

        manager.register_hook("test", callback1)
        manager.register_hook("test", callback2)

        # Execute once
        manager.execute_hook("test", "data")

        # Unregister and execute again
        manager.unregister_hook("test", callback1)
        manager.execute_hook("test", "data")

        # callback1 should have been called once, callback2 twice
        assert callback1.call_count == 1
        assert callback2.call_count == 2
