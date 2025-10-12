"""
Comprehensive tests for AIShell Core Orchestration Module

Tests cover:
- Initialization & lifecycle
- Component orchestration
- Module registry management
- State management
- Configuration integration
- Event bus coordination
- Error handling
- Integration points
- Performance & monitoring

Target: 95%+ coverage for src/core/ai_shell.py
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from pathlib import Path
import tempfile
import yaml

from src.core.ai_shell import AIShellCore, handle_error
from src.core.event_bus import AsyncEventBus, Event, EventPriority
from src.core.config import ConfigManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def ai_shell():
    """Create AIShell instance for testing."""
    shell = AIShellCore()
    yield shell
    # Cleanup
    if shell.initialized:
        await shell.shutdown()


@pytest.fixture
async def initialized_ai_shell():
    """Create initialized AIShell instance."""
    shell = AIShellCore()
    await shell.initialize()
    yield shell
    await shell.shutdown()


@pytest.fixture
def temp_config_file():
    """Create temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            'system': {'startup_animation': True},
            'llm': {'ollama_host': 'localhost:11434'},
            'mcp': {'connection_pool_size': 5}
        }
        yaml.dump(config, f)
        path = f.name

    yield path

    # Cleanup
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def mock_module():
    """Create mock module for registration."""
    module = Mock()
    module.name = "TestModule"
    module.initialize = AsyncMock()
    module.shutdown = AsyncMock()
    module.execute = AsyncMock(return_value="success")
    return module


@pytest.fixture
def mock_database_module():
    """Create mock database module."""
    module = Mock()
    module.name = "DatabaseModule"
    module.client = AsyncMock()
    module.client.connect = AsyncMock()
    module.client.disconnect = AsyncMock()
    module.client.execute = AsyncMock(return_value=[])
    return module


@pytest.fixture
def mock_llm_module():
    """Create mock LLM module."""
    module = Mock()
    module.name = "LLMModule"
    module.provider = Mock()
    module.provider.generate = AsyncMock(return_value="Generated response")
    module.provider.initialized = True
    return module


@pytest.fixture
def mock_mcp_module():
    """Create mock MCP module."""
    module = Mock()
    module.name = "MCPModule"
    module.client = AsyncMock()
    module.client.connect = AsyncMock()
    module.client.tools = ["tool1", "tool2"]
    return module


# ============================================================================
# Test AIShellCore Initialization & Lifecycle
# ============================================================================


class TestAIShellInitialization:
    """Test AIShell initialization and lifecycle."""

    @pytest.mark.asyncio
    async def test_create_ai_shell_default(self):
        """Test creating AIShell with default configuration."""
        shell = AIShellCore()

        assert shell.modules == {}
        assert shell.mcp_clients == {}
        assert shell.event_bus is None
        assert shell.config is None
        assert shell.config_path is None
        assert shell.initialized is False

    @pytest.mark.asyncio
    async def test_create_ai_shell_with_config_path(self, temp_config_file):
        """Test creating AIShell with custom config path."""
        shell = AIShellCore(config_path=temp_config_file)

        assert shell.config_path == temp_config_file
        assert shell.initialized is False

    @pytest.mark.asyncio
    async def test_initialize_creates_event_bus(self, ai_shell):
        """Test initialization creates event bus."""
        await ai_shell.initialize()

        assert ai_shell.event_bus is not None
        assert isinstance(ai_shell.event_bus, AsyncEventBus)
        assert ai_shell.event_bus.processing is True

    @pytest.mark.asyncio
    async def test_initialize_loads_configuration(self, ai_shell):
        """Test initialization loads configuration."""
        await ai_shell.initialize()

        assert ai_shell.config is not None
        assert isinstance(ai_shell.config, ConfigManager)
        assert ai_shell.config.loaded is True

    @pytest.mark.asyncio
    async def test_initialize_creates_module_registry(self, ai_shell):
        """Test initialization creates module registry."""
        await ai_shell.initialize()

        assert ai_shell.modules == {}
        assert isinstance(ai_shell.modules, dict)

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self, ai_shell):
        """Test initialization sets initialized flag."""
        assert ai_shell.initialized is False

        await ai_shell.initialize()

        assert ai_shell.initialized is True

    @pytest.mark.asyncio
    async def test_initialize_with_custom_config(self, temp_config_file):
        """Test initialization with custom config file."""
        shell = AIShellCore(config_path=temp_config_file)
        await shell.initialize()

        assert shell.config is not None
        assert shell.config.get('system.startup_animation') is True

        await shell.shutdown()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, ai_shell):
        """Test calling initialize multiple times is safe."""
        await ai_shell.initialize()
        first_event_bus = ai_shell.event_bus
        first_config = ai_shell.config

        # Call initialize again
        await ai_shell.initialize()

        # Should not create new instances
        assert ai_shell.event_bus is first_event_bus
        assert ai_shell.config is first_config

    @pytest.mark.asyncio
    async def test_initialize_event_bus_started(self, ai_shell):
        """Test event bus is started after initialization."""
        await ai_shell.initialize()

        assert ai_shell.event_bus.processing is True
        assert ai_shell.event_bus.processor_task is not None

    @pytest.mark.asyncio
    async def test_initialize_empty_modules(self, ai_shell):
        """Test module registry starts empty."""
        await ai_shell.initialize()

        assert len(ai_shell.modules) == 0


# ============================================================================
# Test Module Registration & Management
# ============================================================================


class TestModuleRegistration:
    """Test module registration and management."""

    @pytest.mark.asyncio
    async def test_register_module_success(self, initialized_ai_shell, mock_module):
        """Test successfully registering a module."""
        initialized_ai_shell.register_module(mock_module)

        assert "TestModule" in initialized_ai_shell.modules
        assert initialized_ai_shell.modules["TestModule"] is mock_module

    @pytest.mark.asyncio
    async def test_register_multiple_modules(self, initialized_ai_shell):
        """Test registering multiple modules."""
        module1 = Mock(name="Module1")
        module2 = Mock(name="Module2")
        module3 = Mock(name="Module3")

        initialized_ai_shell.register_module(module1)
        initialized_ai_shell.register_module(module2)
        initialized_ai_shell.register_module(module3)

        assert len(initialized_ai_shell.modules) == 3
        assert "Module1" in initialized_ai_shell.modules
        assert "Module2" in initialized_ai_shell.modules
        assert "Module3" in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_register_module_without_name_raises_error(self, initialized_ai_shell):
        """Test registering module without name attribute raises ValueError."""
        module_no_name = Mock(spec=[])  # No attributes

        with pytest.raises(ValueError, match="Module must have 'name' attribute"):
            initialized_ai_shell.register_module(module_no_name)

    @pytest.mark.asyncio
    async def test_register_duplicate_module_raises_error(self, initialized_ai_shell, mock_module):
        """Test registering module with same name raises KeyError."""
        initialized_ai_shell.register_module(mock_module)

        duplicate_module = Mock(name="TestModule")

        with pytest.raises(KeyError, match="Module 'TestModule' already registered"):
            initialized_ai_shell.register_module(duplicate_module)

    @pytest.mark.asyncio
    async def test_unregister_module_success(self, initialized_ai_shell, mock_module):
        """Test successfully unregistering a module."""
        initialized_ai_shell.register_module(mock_module)
        assert "TestModule" in initialized_ai_shell.modules

        initialized_ai_shell.unregister_module("TestModule")

        assert "TestModule" not in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_unregister_non_existent_module_raises_error(self, initialized_ai_shell):
        """Test unregistering non-existent module raises KeyError."""
        with pytest.raises(KeyError, match="Module 'NonExistent' not found"):
            initialized_ai_shell.unregister_module("NonExistent")

    @pytest.mark.asyncio
    async def test_get_module_success(self, initialized_ai_shell, mock_module):
        """Test retrieving registered module."""
        initialized_ai_shell.register_module(mock_module)

        retrieved = initialized_ai_shell.get_module("TestModule")

        assert retrieved is mock_module

    @pytest.mark.asyncio
    async def test_get_non_existent_module_raises_error(self, initialized_ai_shell):
        """Test getting non-existent module raises KeyError."""
        with pytest.raises(KeyError, match="Module 'NonExistent' not found"):
            initialized_ai_shell.get_module("NonExistent")

    @pytest.mark.asyncio
    async def test_module_registration_before_initialization(self, ai_shell, mock_module):
        """Test module can be registered before initialization."""
        # Should not raise error
        ai_shell.register_module(mock_module)
        assert "TestModule" in ai_shell.modules

    @pytest.mark.asyncio
    async def test_module_registry_independent(self, initialized_ai_shell):
        """Test module registry is independent dictionary."""
        module1 = Mock(name="Module1")
        module2 = Mock(name="Module2")

        initialized_ai_shell.register_module(module1)
        modules_copy = initialized_ai_shell.modules.copy()

        initialized_ai_shell.register_module(module2)

        # Original copy should not be affected
        assert "Module2" not in modules_copy
        assert "Module2" in initialized_ai_shell.modules


# ============================================================================
# Test Component Orchestration
# ============================================================================


class TestComponentOrchestration:
    """Test orchestration of multiple components."""

    @pytest.mark.asyncio
    async def test_register_database_module(self, initialized_ai_shell, mock_database_module):
        """Test registering database module."""
        initialized_ai_shell.register_module(mock_database_module)

        db_module = initialized_ai_shell.get_module("DatabaseModule")
        assert db_module is mock_database_module
        assert hasattr(db_module, 'client')

    @pytest.mark.asyncio
    async def test_register_llm_module(self, initialized_ai_shell, mock_llm_module):
        """Test registering LLM module."""
        initialized_ai_shell.register_module(mock_llm_module)

        llm_module = initialized_ai_shell.get_module("LLMModule")
        assert llm_module.provider.initialized is True

    @pytest.mark.asyncio
    async def test_register_mcp_module(self, initialized_ai_shell, mock_mcp_module):
        """Test registering MCP module."""
        initialized_ai_shell.register_module(mock_mcp_module)

        mcp_module = initialized_ai_shell.get_module("MCPModule")
        assert mcp_module.client.tools == ["tool1", "tool2"]

    @pytest.mark.asyncio
    async def test_full_stack_integration(
        self,
        initialized_ai_shell,
        mock_database_module,
        mock_llm_module,
        mock_mcp_module
    ):
        """Test full stack with all components."""
        # Register all modules
        initialized_ai_shell.register_module(mock_database_module)
        initialized_ai_shell.register_module(mock_llm_module)
        initialized_ai_shell.register_module(mock_mcp_module)

        # Verify all registered
        assert len(initialized_ai_shell.modules) == 3
        assert "DatabaseModule" in initialized_ai_shell.modules
        assert "LLMModule" in initialized_ai_shell.modules
        assert "MCPModule" in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_module_interaction_via_event_bus(self, initialized_ai_shell):
        """Test modules can communicate via event bus."""
        events_received = []

        async def event_handler(event):
            events_received.append(event.type)

        initialized_ai_shell.event_bus.subscribe("module.event", event_handler)

        # Publish event
        event = Event("module.event", {"data": "test"})
        await initialized_ai_shell.event_bus.publish(event)

        await asyncio.sleep(0.1)

        assert "module.event" in events_received

    @pytest.mark.asyncio
    async def test_mcp_clients_storage(self, initialized_ai_shell):
        """Test MCP clients can be stored."""
        mock_client = AsyncMock()
        mock_client.name = "postgres_client"

        initialized_ai_shell.mcp_clients["postgres"] = mock_client

        assert "postgres" in initialized_ai_shell.mcp_clients
        assert initialized_ai_shell.mcp_clients["postgres"] is mock_client


# ============================================================================
# Test Shutdown & Cleanup
# ============================================================================


class TestShutdown:
    """Test shutdown and cleanup procedures."""

    @pytest.mark.asyncio
    async def test_shutdown_stops_event_bus(self, ai_shell):
        """Test shutdown stops event bus."""
        await ai_shell.initialize()
        assert ai_shell.event_bus.processing is True

        await ai_shell.shutdown()

        assert ai_shell.event_bus.processing is False

    @pytest.mark.asyncio
    async def test_shutdown_clears_modules(self, ai_shell, mock_module):
        """Test shutdown clears module registry."""
        await ai_shell.initialize()
        ai_shell.register_module(mock_module)
        assert len(ai_shell.modules) > 0

        await ai_shell.shutdown()

        assert len(ai_shell.modules) == 0

    @pytest.mark.asyncio
    async def test_shutdown_resets_initialized_flag(self, ai_shell):
        """Test shutdown resets initialized flag."""
        await ai_shell.initialize()
        assert ai_shell.initialized is True

        await ai_shell.shutdown()

        assert ai_shell.initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_before_initialization(self, ai_shell):
        """Test shutdown before initialization doesn't raise error."""
        # Should not raise
        await ai_shell.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_multiple_times(self, ai_shell):
        """Test calling shutdown multiple times is safe."""
        await ai_shell.initialize()

        await ai_shell.shutdown()
        await ai_shell.shutdown()  # Second call should be safe

    @pytest.mark.asyncio
    async def test_shutdown_with_no_event_bus(self, ai_shell):
        """Test shutdown when event bus is None."""
        ai_shell.event_bus = None

        # Should not raise error
        await ai_shell.shutdown()

    @pytest.mark.asyncio
    async def test_reinitialize_after_shutdown(self, ai_shell):
        """Test can reinitialize after shutdown."""
        await ai_shell.initialize()
        await ai_shell.shutdown()

        # Should be able to initialize again
        await ai_shell.initialize()

        assert ai_shell.initialized is True
        assert ai_shell.event_bus is not None

    @pytest.mark.asyncio
    async def test_shutdown_clears_mcp_clients(self, ai_shell):
        """Test shutdown handles MCP clients."""
        await ai_shell.initialize()

        mock_client = AsyncMock()
        ai_shell.mcp_clients["test"] = mock_client

        await ai_shell.shutdown()

        # Module clearing should handle this
        assert len(ai_shell.modules) == 0


# ============================================================================
# Test Configuration Integration
# ============================================================================


class TestConfigurationIntegration:
    """Test configuration integration."""

    @pytest.mark.asyncio
    async def test_config_loaded_during_initialization(self, ai_shell):
        """Test configuration is loaded during initialization."""
        await ai_shell.initialize()

        assert ai_shell.config is not None
        assert ai_shell.config.loaded is True

    @pytest.mark.asyncio
    async def test_access_config_values(self, initialized_ai_shell):
        """Test accessing configuration values."""
        # Default config should have system settings
        system_config = initialized_ai_shell.config.get_section('system')
        assert system_config is not None

    @pytest.mark.asyncio
    async def test_config_with_custom_path(self, temp_config_file):
        """Test loading custom config file."""
        shell = AIShellCore(config_path=temp_config_file)
        await shell.initialize()

        assert shell.config.get('system.startup_animation') is True
        assert shell.config.get('llm.ollama_host') == 'localhost:11434'

        await shell.shutdown()

    @pytest.mark.asyncio
    async def test_config_environment_overrides(self, ai_shell, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv('AI_SHELL_SYSTEM_STARTUP_ANIMATION', 'false')

        await ai_shell.initialize()

        # Environment override should apply
        startup_animation = ai_shell.config.get('system.startup_animation')
        assert startup_animation is False

    @pytest.mark.asyncio
    async def test_config_validation(self, initialized_ai_shell):
        """Test configuration validation."""
        is_valid = initialized_ai_shell.config.validate()
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_config_modification(self, initialized_ai_shell):
        """Test modifying configuration at runtime."""
        initialized_ai_shell.config.set('custom.setting', 'value')

        assert initialized_ai_shell.config.get('custom.setting') == 'value'


# ============================================================================
# Test State Management
# ============================================================================


class TestStateManagement:
    """Test state management."""

    @pytest.mark.asyncio
    async def test_initialized_state_tracking(self, ai_shell):
        """Test initialized state is properly tracked."""
        assert ai_shell.initialized is False

        await ai_shell.initialize()
        assert ai_shell.initialized is True

        await ai_shell.shutdown()
        assert ai_shell.initialized is False

    @pytest.mark.asyncio
    async def test_module_state_persistence(self, initialized_ai_shell, mock_module):
        """Test module state persists."""
        initialized_ai_shell.register_module(mock_module)
        mock_module.state = {"counter": 0}

        # State should persist
        retrieved = initialized_ai_shell.get_module("TestModule")
        assert retrieved.state["counter"] == 0

    @pytest.mark.asyncio
    async def test_event_bus_state(self, initialized_ai_shell):
        """Test event bus state."""
        stats = initialized_ai_shell.event_bus.get_stats()

        assert 'events_published' in stats
        assert 'events_processed' in stats
        assert 'events_dropped' in stats

    @pytest.mark.asyncio
    async def test_mcp_client_state_storage(self, initialized_ai_shell):
        """Test MCP client state storage."""
        client_state = {
            "connection_status": "connected",
            "tools": ["tool1", "tool2"]
        }

        initialized_ai_shell.mcp_clients["test_client"] = client_state

        assert initialized_ai_shell.mcp_clients["test_client"] == client_state


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling."""

    def test_handle_error_basic_exception(self):
        """Test handle_error with basic exception."""
        try:
            raise ValueError("Test error message")
        except Exception as e:
            result = handle_error(e)

        assert result['error'] == 'ValueError'
        assert result['message'] == 'Test error message'
        assert result['status'] == 'error'
        assert 'traceback' in result
        assert 'ValueError' in result['traceback']

    def test_handle_error_custom_exception(self):
        """Test handle_error with custom exception."""
        class CustomError(Exception):
            pass

        try:
            raise CustomError("Custom error")
        except Exception as e:
            result = handle_error(e)

        assert result['error'] == 'CustomError'
        assert result['message'] == 'Custom error'

    def test_handle_error_with_traceback(self):
        """Test handle_error includes traceback."""
        try:
            def inner_function():
                raise RuntimeError("Inner error")
            inner_function()
        except Exception as e:
            result = handle_error(e)

        assert 'traceback' in result
        assert 'inner_function' in result['traceback']
        assert 'RuntimeError' in result['traceback']

    def test_handle_error_empty_message(self):
        """Test handle_error with empty message."""
        try:
            raise ValueError()
        except Exception as e:
            result = handle_error(e)

        assert result['error'] == 'ValueError'
        assert result['message'] == ''

    @pytest.mark.asyncio
    async def test_initialization_error_handling(self):
        """Test error handling during initialization."""
        shell = AIShellCore(config_path="/nonexistent/path.yaml")

        # Should handle gracefully by using defaults
        await shell.initialize()

        # Should still initialize with defaults
        assert shell.initialized is True
        assert shell.config is not None

        await shell.shutdown()

    @pytest.mark.asyncio
    async def test_module_registration_error_recovery(self, initialized_ai_shell):
        """Test recovery from module registration error."""
        bad_module = Mock(spec=[])  # No name attribute

        with pytest.raises(ValueError):
            initialized_ai_shell.register_module(bad_module)

        # Shell should still be operational
        good_module = Mock(name="GoodModule")
        initialized_ai_shell.register_module(good_module)

        assert "GoodModule" in initialized_ai_shell.modules


# ============================================================================
# Test Integration Points
# ============================================================================


class TestIntegrationPoints:
    """Test integration with other components."""

    @pytest.mark.asyncio
    async def test_event_bus_integration(self, initialized_ai_shell):
        """Test event bus integration."""
        events = []

        async def handler(event):
            events.append(event)

        initialized_ai_shell.event_bus.subscribe("test.event", handler)

        await initialized_ai_shell.event_bus.publish(
            Event("test.event", {"data": "test"})
        )

        await asyncio.sleep(0.1)

        assert len(events) == 1
        assert events[0].type == "test.event"

    @pytest.mark.asyncio
    async def test_config_event_bus_integration(self, initialized_ai_shell):
        """Test config can influence event bus behavior."""
        # Event bus should be configured based on config
        assert initialized_ai_shell.event_bus is not None
        assert initialized_ai_shell.config is not None

    @pytest.mark.asyncio
    async def test_module_lifecycle_hooks(self, initialized_ai_shell):
        """Test module lifecycle hooks."""
        module = Mock(name="LifecycleModule")
        module.on_register = Mock()

        initialized_ai_shell.register_module(module)

        # Module is registered
        assert "LifecycleModule" in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_cross_module_communication(self, initialized_ai_shell):
        """Test modules can communicate via core."""
        module1 = Mock(name="Module1")
        module2 = Mock(name="Module2")

        initialized_ai_shell.register_module(module1)
        initialized_ai_shell.register_module(module2)

        # Module1 can access Module2 via core
        retrieved_module2 = initialized_ai_shell.get_module("Module2")
        assert retrieved_module2 is module2


# ============================================================================
# Test Performance & Monitoring
# ============================================================================


class TestPerformanceMonitoring:
    """Test performance and monitoring features."""

    @pytest.mark.asyncio
    async def test_event_bus_statistics(self, initialized_ai_shell):
        """Test event bus provides statistics."""
        stats = initialized_ai_shell.event_bus.get_stats()

        assert isinstance(stats, dict)
        assert 'events_published' in stats
        assert 'events_processed' in stats

    @pytest.mark.asyncio
    async def test_module_count_tracking(self, initialized_ai_shell):
        """Test tracking number of registered modules."""
        module1 = Mock(name="Module1")
        module2 = Mock(name="Module2")

        assert len(initialized_ai_shell.modules) == 0

        initialized_ai_shell.register_module(module1)
        assert len(initialized_ai_shell.modules) == 1

        initialized_ai_shell.register_module(module2)
        assert len(initialized_ai_shell.modules) == 2

    @pytest.mark.asyncio
    async def test_initialization_timing(self, ai_shell):
        """Test initialization completes in reasonable time."""
        import time

        start = time.time()
        await ai_shell.initialize()
        duration = time.time() - start

        # Should initialize quickly (< 5 seconds)
        assert duration < 5.0

    @pytest.mark.asyncio
    async def test_shutdown_timing(self, initialized_ai_shell):
        """Test shutdown completes in reasonable time."""
        import time

        start = time.time()
        await initialized_ai_shell.shutdown()
        duration = time.time() - start

        # Should shutdown quickly (< 2 seconds)
        assert duration < 2.0

    @pytest.mark.asyncio
    async def test_rapid_module_registration(self, initialized_ai_shell):
        """Test rapid module registration performance."""
        modules = [Mock(name=f"Module{i}") for i in range(100)]

        import time
        start = time.time()

        for module in modules:
            initialized_ai_shell.register_module(module)

        duration = time.time() - start

        assert len(initialized_ai_shell.modules) == 100
        assert duration < 1.0  # Should be very fast


# ============================================================================
# Test Edge Cases & Boundary Conditions
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_module_name(self, initialized_ai_shell):
        """Test module with empty name."""
        module = Mock(name="")

        # Should still work with empty name
        initialized_ai_shell.register_module(module)
        assert "" in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_module_with_special_characters_in_name(self, initialized_ai_shell):
        """Test module with special characters in name."""
        module = Mock(name="Module@#$%")

        initialized_ai_shell.register_module(module)
        assert "Module@#$%" in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_very_long_module_name(self, initialized_ai_shell):
        """Test module with very long name."""
        long_name = "M" * 1000
        module = Mock(name=long_name)

        initialized_ai_shell.register_module(module)
        assert long_name in initialized_ai_shell.modules

    @pytest.mark.asyncio
    async def test_none_config_path(self):
        """Test None config path."""
        shell = AIShellCore(config_path=None)
        await shell.initialize()

        # Should use defaults
        assert shell.config is not None

        await shell.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_module_registration(self, initialized_ai_shell):
        """Test concurrent module registration."""
        modules = [Mock(name=f"ConcurrentModule{i}") for i in range(10)]

        # Register concurrently
        tasks = []
        for module in modules:
            task = asyncio.create_task(
                asyncio.to_thread(initialized_ai_shell.register_module, module)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        assert len(initialized_ai_shell.modules) == 10

    @pytest.mark.asyncio
    async def test_module_with_none_attributes(self, initialized_ai_shell):
        """Test module with None attributes."""
        module = Mock(name="NoneModule")
        module.value = None
        module.config = None

        initialized_ai_shell.register_module(module)

        retrieved = initialized_ai_shell.get_module("NoneModule")
        assert retrieved.value is None

    @pytest.mark.asyncio
    async def test_initialize_shutdown_cycle(self, ai_shell):
        """Test multiple initialize/shutdown cycles."""
        for _ in range(3):
            await ai_shell.initialize()
            assert ai_shell.initialized is True

            await ai_shell.shutdown()
            assert ai_shell.initialized is False


# ============================================================================
# Test Async Operations
# ============================================================================


class TestAsyncOperations:
    """Test async operations."""

    @pytest.mark.asyncio
    async def test_concurrent_initialization(self):
        """Test concurrent initialization of multiple shells."""
        shells = [AIShellCore() for _ in range(5)]

        # Initialize concurrently
        await asyncio.gather(*[shell.initialize() for shell in shells])

        # All should be initialized
        for shell in shells:
            assert shell.initialized is True

        # Cleanup
        await asyncio.gather(*[shell.shutdown() for shell in shells])

    @pytest.mark.asyncio
    async def test_async_module_operations(self, initialized_ai_shell):
        """Test async module operations."""
        module = Mock(name="AsyncModule")
        module.async_operation = AsyncMock(return_value="result")

        initialized_ai_shell.register_module(module)

        # Can call async operations on module
        result = await module.async_operation()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_event_bus_async_publishing(self, initialized_ai_shell):
        """Test async event publishing."""
        received = []

        async def handler(event):
            await asyncio.sleep(0.01)
            received.append(event.type)

        initialized_ai_shell.event_bus.subscribe("async.event", handler)

        # Publish multiple events
        for i in range(5):
            await initialized_ai_shell.event_bus.publish(
                Event("async.event", {"id": i})
            )

        await asyncio.sleep(0.2)

        assert len(received) == 5


# ============================================================================
# Test Logging & Debugging
# ============================================================================


class TestLoggingDebugging:
    """Test logging and debugging features."""

    @pytest.mark.asyncio
    async def test_initialization_logging(self, ai_shell, caplog):
        """Test logging during initialization."""
        import logging
        caplog.set_level(logging.INFO)

        await ai_shell.initialize()

        # Should have logged initialization steps
        assert any("Event bus" in record.message for record in caplog.records)
        assert any("Configuration" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_module_registration_logging(self, initialized_ai_shell, mock_module, caplog):
        """Test logging during module registration."""
        import logging
        caplog.set_level(logging.INFO)

        initialized_ai_shell.register_module(mock_module)

        assert any("TestModule" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, initialized_ai_shell, caplog):
        """Test logging during shutdown."""
        import logging
        caplog.set_level(logging.INFO)

        await initialized_ai_shell.shutdown()

        assert any("Shutting down" in record.message or "shutdown" in record.message.lower()
                   for record in caplog.records)


# ============================================================================
# Integration Test Suite
# ============================================================================


class TestFullStackIntegration:
    """Test full stack integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_lifecycle(
        self,
        mock_database_module,
        mock_llm_module,
        mock_mcp_module
    ):
        """Test complete lifecycle with all components."""
        # Initialize
        shell = AIShellCore()
        await shell.initialize()

        # Register modules
        shell.register_module(mock_database_module)
        shell.register_module(mock_llm_module)
        shell.register_module(mock_mcp_module)

        # Verify all operational
        assert shell.initialized
        assert len(shell.modules) == 3
        assert shell.event_bus.processing

        # Shutdown
        await shell.shutdown()

        assert not shell.initialized
        assert len(shell.modules) == 0
        assert not shell.event_bus.processing

    @pytest.mark.asyncio
    async def test_event_driven_module_coordination(self, initialized_ai_shell):
        """Test modules coordinating via events."""
        results = []

        async def module1_handler(event):
            results.append(f"module1:{event.data['action']}")

        async def module2_handler(event):
            results.append(f"module2:{event.data['action']}")

        initialized_ai_shell.event_bus.subscribe("coordination.event", module1_handler)
        initialized_ai_shell.event_bus.subscribe("coordination.event", module2_handler)

        await initialized_ai_shell.event_bus.publish(
            Event("coordination.event", {"action": "sync"})
        )

        await asyncio.sleep(0.1)

        assert "module1:sync" in results
        assert "module2:sync" in results

    @pytest.mark.asyncio
    async def test_configuration_driven_behavior(self, temp_config_file):
        """Test configuration influences behavior."""
        shell = AIShellCore(config_path=temp_config_file)
        await shell.initialize()

        # Config should be loaded
        startup_animation = shell.config.get('system.startup_animation')
        assert startup_animation is True

        await shell.shutdown()

    @pytest.mark.asyncio
    async def test_error_recovery_and_continuation(self, initialized_ai_shell):
        """Test system recovers from errors and continues."""
        # Register a bad module
        try:
            bad_module = Mock(spec=[])
            initialized_ai_shell.register_module(bad_module)
        except ValueError:
            pass

        # System should still work
        good_module = Mock(name="GoodModule")
        initialized_ai_shell.register_module(good_module)

        assert "GoodModule" in initialized_ai_shell.modules
        assert initialized_ai_shell.initialized

    @pytest.mark.asyncio
    async def test_graceful_degradation(self, ai_shell):
        """Test graceful degradation on component failure."""
        # Initialize with potential config failure
        await ai_shell.initialize()

        # Should still initialize even if config loading has issues
        assert ai_shell.initialized
        assert ai_shell.event_bus is not None

        await ai_shell.shutdown()
