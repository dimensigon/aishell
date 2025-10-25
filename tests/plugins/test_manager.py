"""Comprehensive tests for plugin manager module."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import json

from src.plugins.plugin_manager import (
    PluginManager, BasePlugin, PluginMetadata,
    PluginError, PluginLoadError, PluginValidationError
)


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    @classmethod
    def get_name(cls):
        return "mock_plugin"

    @classmethod
    def get_version(cls):
        return "1.0.0"

    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="mock_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            homepage="https://example.com",
            license="MIT",
            tags=["test"],
            dependencies=[],
            entry_point="mock:MockPlugin"
        )


class TestPluginMetadata:
    """Test suite for PluginMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Description",
            homepage="https://example.com",
            license="MIT",
            tags=["tag1", "tag2"],
            dependencies=["dep1"],
            entry_point="module:Class"
        )

        assert metadata.name == "test"
        assert metadata.version == "1.0.0"
        assert len(metadata.tags) == 2
        assert len(metadata.dependencies) == 1

    def test_metadata_with_config_schema(self):
        """Test metadata with configuration schema."""
        schema = {
            "type": "object",
            "properties": {
                "timeout": {"type": "number"}
            }
        }

        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author",
            description="Desc",
            homepage="",
            license="MIT",
            tags=[],
            dependencies=[],
            entry_point="module:Class",
            config_schema=schema
        )

        assert metadata.config_schema is not None
        assert "properties" in metadata.config_schema


class TestPluginErrors:
    """Test suite for plugin exception classes."""

    def test_plugin_error(self):
        """Test PluginError exception."""
        with pytest.raises(PluginError, match="Test error"):
            raise PluginError("Test error")

    def test_plugin_load_error(self):
        """Test PluginLoadError exception."""
        with pytest.raises(PluginLoadError, match="Load failed"):
            raise PluginLoadError("Load failed")

    def test_plugin_validation_error(self):
        """Test PluginValidationError exception."""
        with pytest.raises(PluginValidationError, match="Invalid"):
            raise PluginValidationError("Invalid")

    def test_error_inheritance(self):
        """Test that specific errors inherit from PluginError."""
        assert issubclass(PluginLoadError, PluginError)
        assert issubclass(PluginValidationError, PluginError)


class TestBasePlugin:
    """Test suite for BasePlugin base class."""

    def test_base_plugin_instantiation_fails(self):
        """Test that BasePlugin cannot be instantiated directly."""
        with pytest.raises(NotImplementedError):
            plugin = BasePlugin({})
            plugin.get_name()

    def test_base_plugin_with_mock(self):
        """Test BasePlugin with proper subclass."""
        plugin = MockPlugin({"key": "value"})

        assert plugin.config == {"key": "value"}
        assert plugin.get_name() == "mock_plugin"
        assert plugin.get_version() == "1.0.0"

    @pytest.mark.asyncio
    async def test_base_plugin_lifecycle_methods(self):
        """Test base plugin lifecycle methods."""
        plugin = MockPlugin({})

        # Default implementations should not raise
        await plugin.initialize()
        await plugin.start()
        await plugin.stop()
        await plugin.cleanup()

    def test_base_plugin_validate_config(self):
        """Test default config validation."""
        plugin = MockPlugin({})

        # Default validation always returns True
        assert plugin.validate_config({}) is True
        assert plugin.validate_config({"any": "config"}) is True


class TestPluginManager:
    """Test suite for PluginManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a plugin manager with temp directory."""
        return PluginManager(plugin_dirs=[tmp_path], hot_reload=False)

    @pytest.fixture
    def plugin_dir(self, tmp_path):
        """Create a plugin directory structure."""
        plugin_path = tmp_path / "test_plugin"
        plugin_path.mkdir()

        # Create plugin.json
        metadata = {
            "name": "test_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Test plugin",
            "homepage": "https://example.com",
            "license": "MIT",
            "tags": ["test"],
            "dependencies": [],
            "entry_point": "plugin:TestPlugin"
        }

        (plugin_path / "plugin.json").write_text(json.dumps(metadata))

        # Create plugin.py
        (plugin_path / "plugin.py").write_text("""
from src.plugins.plugin_manager import BasePlugin, PluginMetadata

class TestPlugin(BasePlugin):
    @classmethod
    def get_name(cls):
        return "test_plugin"

    @classmethod
    def get_version(cls):
        return "1.0.0"

    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test plugin",
            homepage="https://example.com",
            license="MIT",
            tags=["test"],
            dependencies=[],
            entry_point="plugin:TestPlugin"
        )
""")

        return plugin_path

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert len(manager.plugins) == 0
        assert len(manager.plugin_classes) == 0
        assert len(manager.metadata) == 0

    def test_manager_default_plugin_dirs(self):
        """Test manager with default plugin directories."""
        manager = PluginManager()

        assert len(manager.plugin_dirs) >= 2
        # Should include home directory and project directory
        assert any(".ai-shell" in str(p) for p in manager.plugin_dirs)

    def test_discover_plugins_empty(self, manager):
        """Test discovering plugins in empty directory."""
        discovered = manager.discover_plugins()

        assert discovered == []

    def test_discover_plugins_with_plugin(self, manager, plugin_dir):
        """Test discovering plugins."""
        discovered = manager.discover_plugins()

        assert len(discovered) == 1
        assert discovered[0].name == "test_plugin"
        assert discovered[0].version == "1.0.0"

    def test_load_plugin_metadata(self, manager, plugin_dir):
        """Test loading plugin metadata from plugin.json."""
        plugin_json = plugin_dir / "plugin.json"
        metadata = manager._load_plugin_metadata(plugin_json)

        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.entry_point == "plugin:TestPlugin"

    def test_register_plugin(self, manager):
        """Test registering a plugin instance."""
        plugin = MockPlugin({})
        manager.register_plugin("mock", plugin)

        assert "mock" in manager.plugins
        assert manager.plugins["mock"] == plugin

    def test_activate_plugin(self, manager):
        """Test activating a registered plugin."""
        plugin = Mock()
        plugin.activate = Mock(return_value=True)

        manager.register_plugin("test", plugin)
        result = manager.activate_plugin("test")

        assert result is True
        plugin.activate.assert_called_once()

    def test_activate_plugin_not_found(self, manager):
        """Test activating non-existent plugin."""
        result = manager.activate_plugin("nonexistent")

        assert result is False

    def test_deactivate_plugin(self, manager):
        """Test deactivating a plugin."""
        plugin = Mock()
        plugin.deactivate = Mock()

        manager.register_plugin("test", plugin)
        manager.activate_plugin("test")
        result = manager.deactivate_plugin("test")

        assert result is True
        plugin.deactivate.assert_called_once()

    def test_deactivate_plugin_not_found(self, manager):
        """Test deactivating non-existent plugin."""
        result = manager.deactivate_plugin("nonexistent")

        assert result is False

    def test_activate_all_plugins(self, manager):
        """Test activating all plugins."""
        plugin1 = Mock()
        plugin1.activate = Mock(return_value=True)
        plugin1.dependencies = []

        plugin2 = Mock()
        plugin2.activate = Mock(return_value=True)
        plugin2.dependencies = []

        manager.register_plugin("plugin1", plugin1)
        manager.register_plugin("plugin2", plugin2)

        activation_order = manager.activate_all_plugins()

        assert len(activation_order) == 2
        assert "plugin1" in activation_order
        assert "plugin2" in activation_order

    def test_activate_all_plugins_with_dependencies(self, manager):
        """Test activating plugins respecting dependencies."""
        plugin_a = Mock()
        plugin_a.activate = Mock(return_value=True)
        plugin_a.dependencies = []

        plugin_b = Mock()
        plugin_b.activate = Mock(return_value=True)
        plugin_b.dependencies = ["plugin_a"]

        manager.register_plugin("plugin_a", plugin_a)
        manager.register_plugin("plugin_b", plugin_b)

        activation_order = manager.activate_all_plugins()

        # plugin_a should be activated before plugin_b
        assert activation_order.index("plugin_a") < activation_order.index("plugin_b")

    def test_get_plugin(self, manager):
        """Test getting a loaded plugin."""
        plugin = MockPlugin({})
        manager.register_plugin("mock", plugin)

        retrieved = manager.get_plugin("mock")

        assert retrieved == plugin

    def test_get_plugin_not_found(self, manager):
        """Test getting non-existent plugin."""
        retrieved = manager.get_plugin("nonexistent")

        assert retrieved is None

    def test_list_plugins_empty(self, manager):
        """Test listing plugins when none are loaded."""
        plugins = manager.list_plugins()

        assert plugins == []

    def test_list_plugins_with_plugins(self, manager):
        """Test listing loaded plugins."""
        plugin = MockPlugin({})
        manager.plugins["mock"] = plugin
        manager.metadata["mock"] = MockPlugin.get_metadata()

        plugins = manager.list_plugins()

        assert len(plugins) == 1
        assert plugins[0]["name"] == "mock_plugin"
        assert plugins[0]["version"] == "1.0.0"
        assert plugins[0]["status"] == "loaded"

    def test_unload_plugin(self, manager):
        """Test unloading a plugin."""
        plugin = MockPlugin({})
        manager.plugins["mock"] = plugin
        manager.plugin_classes["mock"] = MockPlugin
        manager.metadata["mock"] = MockPlugin.get_metadata()

        manager.unload_plugin("mock")

        assert "mock" not in manager.plugins
        assert "mock" not in manager.plugin_classes
        assert "mock" not in manager.metadata

    def test_unload_plugin_not_loaded(self, manager):
        """Test unloading plugin that isn't loaded."""
        # Should not raise error
        manager.unload_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_start_plugin(self, manager):
        """Test starting a plugin."""
        plugin = MockPlugin({})
        plugin.initialize = AsyncMock()
        plugin.start = AsyncMock()

        manager.plugins["mock"] = plugin

        await manager.start_plugin("mock")

        plugin.initialize.assert_called_once()
        plugin.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_plugin_not_loaded(self, manager):
        """Test starting plugin that isn't loaded."""
        with pytest.raises(PluginError, match="not loaded"):
            await manager.start_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_start_plugin_error(self, manager):
        """Test error during plugin start."""
        plugin = MockPlugin({})
        plugin.initialize = AsyncMock(side_effect=RuntimeError("Start error"))

        manager.plugins["mock"] = plugin

        with pytest.raises(RuntimeError):
            await manager.start_plugin("mock")

    @pytest.mark.asyncio
    async def test_stop_plugin(self, manager):
        """Test stopping a plugin."""
        plugin = MockPlugin({})
        plugin.stop = AsyncMock()
        plugin.cleanup = AsyncMock()

        manager.plugins["mock"] = plugin

        await manager.stop_plugin("mock")

        plugin.stop.assert_called_once()
        plugin.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_plugin_not_loaded(self, manager):
        """Test stopping plugin that isn't loaded."""
        with pytest.raises(PluginError, match="not loaded"):
            await manager.stop_plugin("nonexistent")

    @pytest.mark.asyncio
    async def test_reload_plugin(self, manager):
        """Test reloading a plugin."""
        plugin = MockPlugin({})
        plugin.stop = AsyncMock()
        plugin.cleanup = AsyncMock()
        plugin.initialize = AsyncMock()
        plugin.start = AsyncMock()

        manager.plugins["mock"] = plugin
        manager.plugin_classes["mock"] = MockPlugin
        manager.metadata["mock"] = MockPlugin.get_metadata()

        with patch.object(manager, 'load_plugin', return_value=plugin):
            await manager.reload_plugin("mock", {"new": "config"})

        plugin.stop.assert_called_once()
        plugin.cleanup.assert_called_once()


class TestPluginManagerDependencies:
    """Test plugin dependency management."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager instance."""
        return PluginManager(plugin_dirs=[tmp_path])

    def test_check_dependencies_missing(self, manager):
        """Test checking missing dependencies."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Test",
            description="Test",
            homepage="",
            license="MIT",
            tags=[],
            dependencies=["missing_plugin"],
            entry_point="test:Test"
        )

        with pytest.raises(PluginLoadError, match="Missing dependency"):
            manager._check_dependencies(metadata)

    def test_check_dependencies_satisfied(self, manager):
        """Test checking satisfied dependencies."""
        # Register dependency first
        dep_plugin = MockPlugin({})
        manager.plugins["mock_plugin"] = dep_plugin

        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Test",
            description="Test",
            homepage="",
            license="MIT",
            tags=[],
            dependencies=["mock_plugin"],
            entry_point="test:Test"
        )

        # Should not raise
        manager._check_dependencies(metadata)


class TestPluginManagerEdgeCases:
    """Test edge cases in plugin management."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager instance."""
        return PluginManager(plugin_dirs=[tmp_path])

    def test_concurrent_plugin_registration(self, manager):
        """Test concurrent plugin registrations."""
        import concurrent.futures

        plugins = [MockPlugin({}) for _ in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(manager.register_plugin, f"plugin_{i}", p)
                      for i, p in enumerate(plugins)]
            [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(manager.plugins) == 10

    @pytest.mark.asyncio
    async def test_concurrent_plugin_start(self, manager):
        """Test concurrent plugin starts."""
        plugins = []
        for i in range(5):
            plugin = MockPlugin({})
            plugin.initialize = AsyncMock()
            plugin.start = AsyncMock()
            manager.plugins[f"plugin_{i}"] = plugin
            plugins.append(plugin)

        # Start all concurrently
        await asyncio.gather(*[
            manager.start_plugin(f"plugin_{i}")
            for i in range(5)
        ])

        # All should have been initialized and started
        for plugin in plugins:
            plugin.initialize.assert_called_once()
            plugin.start.assert_called_once()

    def test_plugin_with_hot_reload(self, tmp_path):
        """Test manager with hot reload enabled."""
        manager = PluginManager(plugin_dirs=[tmp_path], hot_reload=True)

        assert manager.hot_reload is True

    def test_discover_plugins_invalid_json(self, manager, tmp_path):
        """Test discovering plugins with invalid JSON."""
        plugin_path = tmp_path / "bad_plugin"
        plugin_path.mkdir()

        # Create invalid plugin.json
        (plugin_path / "plugin.json").write_text("{invalid json")

        discovered = manager.discover_plugins()

        # Should skip invalid plugins
        assert discovered == []

    def test_get_global_plugin_manager(self):
        """Test getting global plugin manager instance."""
        from src.plugins.plugin_manager import get_plugin_manager

        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        # Should return same instance
        assert manager1 is manager2
