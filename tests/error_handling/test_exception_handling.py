"""
Comprehensive Exception Handling Tests

Tests all exception types and error paths across modules.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict

from src.core.ai_shell import AIShellCore, handle_error
from src.core.event_bus import AsyncEventBus, Event, EventPriority
from src.llm.manager import LocalLLMManager, IntentType
from src.security.error_handler import (
    SecureErrorHandler,
    SecurityError,
    secure_exception_handler,
)


class TestAIShellCoreExceptions:
    """Test exception handling in AIShellCore"""

    @pytest.mark.asyncio
    async def test_double_initialization_warning(self, caplog):
        """Test warning on double initialization"""
        import logging

        core = AIShellCore()
        await core.initialize()

        with caplog.at_level(logging.WARNING):
            await core.initialize()
            assert "already initialized" in caplog.text

        await core.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_before_init(self):
        """Test shutdown before initialization doesn't crash"""
        core = AIShellCore()
        # Should handle gracefully
        await core.shutdown()
        assert not core.initialized

    def test_register_module_without_name(self):
        """Test registering module without name attribute raises ValueError"""
        core = AIShellCore()
        module = Mock(spec=[])  # No 'name' attribute

        with pytest.raises(ValueError, match="must have 'name' attribute"):
            core.register_module(module)

    def test_register_duplicate_module(self):
        """Test registering duplicate module raises KeyError"""
        core = AIShellCore()
        module1 = Mock(name="test_module")
        module2 = Mock(name="test_module")

        core.register_module(module1)

        with pytest.raises(KeyError, match="already registered"):
            core.register_module(module2)

    def test_unregister_nonexistent_module(self):
        """Test unregistering nonexistent module raises KeyError"""
        core = AIShellCore()

        with pytest.raises(KeyError, match="not found"):
            core.unregister_module("nonexistent")

    def test_get_nonexistent_module(self):
        """Test getting nonexistent module raises KeyError"""
        core = AIShellCore()

        with pytest.raises(KeyError, match="not found"):
            core.get_module("nonexistent")

    def test_handle_error_with_various_exceptions(self):
        """Test handle_error with different exception types"""
        exceptions = [
            ValueError("Test value error"),
            KeyError("missing_key"),
            RuntimeError("Runtime failure"),
            TypeError("Type mismatch"),
            Exception("Generic exception"),
        ]

        for exc in exceptions:
            result = handle_error(exc)

            assert result['status'] == 'error'
            assert result['error'] == type(exc).__name__
            assert result['message'] == str(exc)
            assert 'traceback' in result
            assert len(result['traceback']) > 0

    def test_handle_error_with_nested_exception(self):
        """Test handle_error with nested exception chain"""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError as exc:
            result = handle_error(exc)

            assert result['error'] == 'RuntimeError'
            assert 'ValueError' in result['traceback']


class TestEventBusExceptions:
    """Test exception handling in AsyncEventBus"""

    @pytest.mark.asyncio
    async def test_start_already_running(self, caplog):
        """Test starting already running event bus"""
        import logging

        bus = AsyncEventBus()
        await bus.start()

        with caplog.at_level(logging.WARNING):
            await bus.start()
            assert "already running" in caplog.text

        await bus.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running(self, caplog):
        """Test stopping non-running event bus"""
        import logging

        bus = AsyncEventBus()

        with caplog.at_level(logging.WARNING):
            await bus.stop()
            assert "not running" in caplog.text

    @pytest.mark.asyncio
    async def test_publish_to_full_queue(self):
        """Test publishing to full queue drops non-critical events"""
        bus = AsyncEventBus(max_queue_size=2)
        await bus.start()

        # Fill queue
        event1 = Event("test1", priority=EventPriority.NORMAL)
        event2 = Event("test2", priority=EventPriority.NORMAL)
        await bus.publish(event1)
        await bus.publish(event2)

        # This should raise QueueFull
        event3 = Event("test3", priority=EventPriority.NORMAL, critical=False)
        with pytest.raises(asyncio.QueueFull):
            await bus.publish(event3)

        assert bus.stats['events_dropped'] == 1

        await bus.stop()

    @pytest.mark.asyncio
    async def test_critical_event_bypasses_queue_limit(self):
        """Test critical events are added even when queue is full"""
        bus = AsyncEventBus(max_queue_size=1)
        await bus.start()

        # Fill queue
        event1 = Event("test1", priority=EventPriority.NORMAL)
        await bus.publish(event1)

        # Critical event should still be added
        critical_event = Event("critical", priority=EventPriority.CRITICAL, critical=True)
        await bus.publish(critical_event)  # Should not raise

        await bus.stop()

    @pytest.mark.asyncio
    async def test_handler_exception_doesnt_stop_processing(self):
        """Test exception in handler doesn't stop event processing"""
        bus = AsyncEventBus()
        await bus.start()

        errors = []

        async def failing_handler(event):
            errors.append("handler_called")
            raise ValueError("Handler failed")

        bus.subscribe("test", failing_handler)

        event = Event("test", {"data": "value"})
        await bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.1)

        assert len(errors) == 1
        assert bus.stats['events_processed'] >= 1

        await bus.stop()

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing handler that wasn't subscribed"""
        bus = AsyncEventBus()

        async def handler(event):
            pass

        # Should not raise, just do nothing
        bus.unsubscribe("test", handler)

    @pytest.mark.asyncio
    async def test_event_with_no_subscribers(self):
        """Test publishing event with no subscribers"""
        bus = AsyncEventBus()
        await bus.start()

        event = Event("no_subscribers", {"test": "data"})
        await bus.publish(event)

        await asyncio.sleep(0.1)

        assert bus.stats['events_published'] >= 1

        await bus.stop()


class TestLLMManagerExceptions:
    """Test exception handling in LocalLLMManager"""

    def test_operations_before_initialization(self):
        """Test operations before initialization raise RuntimeError"""
        manager = LocalLLMManager()

        operations = [
            lambda: manager.analyze_intent("SELECT * FROM users"),
            lambda: manager.generate_embeddings(["test"]),
            lambda: manager.find_similar_queries("test", ["query1"]),
            lambda: manager.explain_query("SELECT 1"),
            lambda: manager.suggest_optimization("SELECT *"),
        ]

        for op in operations:
            with pytest.raises(RuntimeError, match="not initialized"):
                op()

    def test_initialize_with_unknown_provider(self):
        """Test initialization with unknown provider"""
        manager = LocalLLMManager()

        with pytest.raises(ValueError, match="Unknown provider type"):
            manager.initialize(provider_type="unknown_provider")

    def test_initialize_with_failing_provider(self):
        """Test initialization when provider fails"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = False

        manager = LocalLLMManager(provider=mock_provider)
        result = manager.initialize()

        assert result is False
        assert manager.initialized is False

    def test_analyze_intent_with_llm_failure(self):
        """Test intent analysis when LLM fails"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider.generate.side_effect = Exception("LLM failed")

        manager = LocalLLMManager(provider=mock_provider)
        manager.embedding_model = Mock()
        manager.embedding_model.initialize.return_value = True
        manager.initialize()

        # Should fall back to rule-based
        result = manager.analyze_intent("SOME WEIRD QUERY")

        assert result['intent'] == 'unknown'
        assert result['confidence'] >= 0

    def test_analyze_intent_with_invalid_json_response(self):
        """Test intent analysis with invalid JSON from LLM"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider.generate.return_value = "not valid json"

        manager = LocalLLMManager(provider=mock_provider)
        manager.embedding_model = Mock()
        manager.embedding_model.initialize.return_value = True
        manager.initialize()

        # Should handle gracefully
        result = manager.analyze_intent("complex query without keywords")

        assert 'intent' in result
        assert 'confidence' in result

    def test_explain_query_failure(self):
        """Test query explanation when LLM fails"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider.generate.side_effect = Exception("Generation failed")

        manager = LocalLLMManager(provider=mock_provider)
        manager.embedding_model = Mock()
        manager.embedding_model.initialize.return_value = True
        manager.initialize()

        result = manager.explain_query("SELECT 1")

        assert "Unable to generate explanation" in result

    def test_suggest_optimization_failure(self):
        """Test optimization suggestion when LLM fails"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider.generate.side_effect = Exception("Generation failed")

        manager = LocalLLMManager(provider=mock_provider)
        manager.embedding_model = Mock()
        manager.embedding_model.initialize.return_value = True
        manager.initialize()

        result = manager.suggest_optimization("SELECT *")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_suggest_optimization_with_malformed_json(self):
        """Test optimization with malformed JSON response"""
        mock_provider = Mock()
        mock_provider.initialize.return_value = True
        mock_provider.generate.return_value = "malformed [json"

        manager = LocalLLMManager(provider=mock_provider)
        manager.embedding_model = Mock()
        manager.embedding_model.initialize.return_value = True
        manager.initialize()

        result = manager.suggest_optimization("SELECT *")

        assert isinstance(result, list)

    def test_anonymize_with_complex_patterns(self):
        """Test anonymization with edge case patterns"""
        manager = LocalLLMManager()

        test_cases = [
            ("SELECT * FROM users WHERE email = 'test@example.com'", "EMAIL"),
            ("UPDATE users SET ssn = '123-45-6789'", "SSN"),
            ("INSERT INTO contacts VALUES ('John Doe', '555-1234567890')", "NAME"),
        ]

        for query, expected_type in test_cases:
            anonymized, mapping = manager.anonymize_query(query)

            assert query != anonymized
            assert len(mapping) > 0
            assert any(expected_type in key for key in mapping.keys())


class TestSecureErrorHandler:
    """Test security error handler"""

    def test_sanitize_sensitive_keywords(self):
        """Test sanitization of sensitive keywords"""
        test_cases = [
            ("password=secret123", "password=***"),
            ("token=abc123", "token=***"),
            ("api_key=xyz789", "api_key=***"),
            ("No sensitive data here", "No sensitive data here"),
        ]

        for input_msg, expected in test_cases:
            result = SecureErrorHandler.sanitize_error_message(input_msg)
            assert result == expected

    @patch.dict('os.environ', {'PRODUCTION': 'true', 'DEBUG': 'false'})
    def test_production_mode_hides_details(self):
        """Test production mode hides error details"""
        from importlib import reload
        from src.security import error_handler
        reload(error_handler)

        error = ValueError("Sensitive information here")
        result = error_handler.SecureErrorHandler.format_error_for_user(error)

        assert result == "An error occurred"
        assert "Sensitive information" not in result

    @patch.dict('os.environ', {'PRODUCTION': 'false', 'DEBUG': 'true'})
    def test_debug_mode_shows_details(self):
        """Test debug mode shows error details"""
        from importlib import reload
        from src.security import error_handler
        reload(error_handler)

        error = ValueError("Detailed error message")
        result = error_handler.SecureErrorHandler.format_error_for_user(error)

        assert "Detailed error message" in result

    def test_log_error_with_context(self, caplog):
        """Test error logging with context"""
        with caplog.at_level(logging.ERROR):
            error = ValueError("Test error")
            SecureErrorHandler.log_error(error, context="test_operation")

            assert "test_operation" in caplog.text
            assert "ValueError" in caplog.text

    def test_log_security_error(self, caplog):
        """Test logging of security errors"""
        with caplog.at_level(logging.ERROR):
            error = SecurityError("Security violation")
            SecureErrorHandler.log_error(error)

            assert "SECURITY ERROR" in caplog.text

    def test_handle_exception_with_raise(self):
        """Test handle_exception with raise_error=True"""
        error = ValueError("Test error")

        with pytest.raises(ValueError):
            SecureErrorHandler.handle_exception(
                error,
                raise_error=True,
                default_message="Custom error"
            )

    def test_handle_exception_without_raise(self):
        """Test handle_exception returns message"""
        error = ValueError("Test error")

        result = SecureErrorHandler.handle_exception(
            error,
            raise_error=False,
            default_message="Custom error"
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_secure_exception_handler_decorator_async(self):
        """Test secure exception handler decorator on async function"""

        @secure_exception_handler(default_message="Operation failed")
        async def failing_async_func():
            raise ValueError("Async failure")

        with pytest.raises(ValueError):
            await failing_async_func()

    def test_secure_exception_handler_decorator_sync(self):
        """Test secure exception handler decorator on sync function"""

        @secure_exception_handler(default_message="Operation failed")
        def failing_sync_func():
            raise ValueError("Sync failure")

        with pytest.raises(ValueError):
            failing_sync_func()


class TestEdgeCaseExceptions:
    """Test edge case exception scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_initialization_race(self):
        """Test concurrent initialization doesn't cause issues"""
        core = AIShellCore()

        # Start multiple initializations concurrently
        results = await asyncio.gather(
            core.initialize(),
            core.initialize(),
            core.initialize(),
            return_exceptions=True
        )

        # All should complete without exceptions
        assert all(r is None for r in results if not isinstance(r, Exception))
        assert core.initialized

        await core.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_during_initialization(self):
        """Test shutdown called during initialization"""
        core = AIShellCore()

        # Start initialization and shutdown concurrently
        init_task = asyncio.create_task(core.initialize())
        await asyncio.sleep(0.01)  # Let init start
        shutdown_task = asyncio.create_task(core.shutdown())

        # Both should complete
        await asyncio.gather(init_task, shutdown_task, return_exceptions=True)

    def test_module_lifecycle_edge_cases(self):
        """Test module lifecycle edge cases"""
        core = AIShellCore()

        module = Mock(name="test")

        # Register, unregister, register again
        core.register_module(module)
        core.unregister_module("test")
        core.register_module(module)  # Should work

        # Clean up
        core.unregister_module("test")

    @pytest.mark.asyncio
    async def test_event_bus_rapid_start_stop(self):
        """Test rapid start/stop cycles"""
        bus = AsyncEventBus()

        for _ in range(5):
            await bus.start()
            await bus.stop()

        # Should still be functional
        await bus.start()
        event = Event("test")
        await bus.publish(event)
        await bus.stop()

    def test_llm_manager_cleanup_multiple_times(self):
        """Test calling cleanup multiple times"""
        manager = LocalLLMManager()
        mock_provider = Mock()
        manager.provider = mock_provider

        # Multiple cleanups should be safe
        manager.cleanup()
        manager.cleanup()
        manager.cleanup()

        assert not manager.initialized

    @pytest.mark.asyncio
    async def test_null_event_data(self):
        """Test event with None data"""
        bus = AsyncEventBus()
        await bus.start()

        # Event with None data should work
        event = Event("test", data=None)
        await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

    def test_empty_string_operations(self):
        """Test operations with empty strings"""
        manager = LocalLLMManager()

        # Empty query
        anonymized, mapping = manager.anonymize_query("")
        assert anonymized == ""
        assert len(mapping) == 0

        # Deanonymize empty
        result = manager.deanonymize_result("", {})
        assert result == ""
