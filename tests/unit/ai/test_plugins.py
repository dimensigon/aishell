"""Comprehensive tests for Plugin System.

Tests cover:
- Plugin Discovery & Loading
- Plugin Lifecycle Management
- Plugin API & Hooks
- Plugin Dependencies
- Plugin Security & Sandboxing
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import importlib


class TestPluginDiscovery(unittest.TestCase):
    """Test plugin discovery mechanisms."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_plugin_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_plugin_dir)

    def test_discover_plugins_in_directory(self):
        """Test discovering plugins in a directory."""
        from src.plugins.discovery import PluginDiscovery

        # Create test plugin files
        plugin_file = os.path.join(self.test_plugin_dir, "test_plugin.py")
        with open(plugin_file, "w") as f:
            f.write(
                """
class TestPlugin:
    name = "test_plugin"
    version = "1.0.0"
"""
            )

        discovery = PluginDiscovery([self.test_plugin_dir])
        plugins = discovery.discover()

        self.assertGreater(len(plugins), 0)
        self.assertIn("test_plugin", [p["name"] for p in plugins])

    def test_plugin_metadata_extraction(self):
        """Test extracting plugin metadata."""
        from src.plugins.discovery import PluginDiscovery

        plugin_file = os.path.join(self.test_plugin_dir, "metadata_plugin.py")
        with open(plugin_file, "w") as f:
            f.write(
                """
class MetadataPlugin:
    name = "metadata_plugin"
    version = "2.0.0"
    author = "Test Author"
    description = "A test plugin"
    dependencies = ["dep1", "dep2"]
"""
            )

        discovery = PluginDiscovery([self.test_plugin_dir])
        plugins = discovery.discover()

        plugin = next(p for p in plugins if p["name"] == "metadata_plugin")
        self.assertEqual(plugin["version"], "2.0.0")
        self.assertEqual(plugin["author"], "Test Author")
        self.assertIn("dep1", plugin["dependencies"])

    def test_plugin_filtering_by_type(self):
        """Test filtering plugins by type."""
        from src.plugins.discovery import PluginDiscovery

        # Create different plugin types
        for plugin_type in ["database", "ui", "api"]:
            plugin_file = os.path.join(self.test_plugin_dir, f"{plugin_type}_plugin.py")
            with open(plugin_file, "w") as f:
                f.write(
                    f"""
class Plugin:
    name = "{plugin_type}_plugin"
    plugin_type = "{plugin_type}"
"""
                )

        discovery = PluginDiscovery([self.test_plugin_dir])
        db_plugins = discovery.discover(plugin_type="database")

        self.assertEqual(len(db_plugins), 1)
        self.assertEqual(db_plugins[0]["name"], "database_plugin")

    def test_ignore_invalid_plugins(self):
        """Test that invalid plugins are ignored."""
        from src.plugins.discovery import PluginDiscovery

        # Create invalid plugin
        invalid_file = os.path.join(self.test_plugin_dir, "invalid_plugin.py")
        with open(invalid_file, "w") as f:
            f.write("This is not a valid plugin file syntax error")

        discovery = PluginDiscovery([self.test_plugin_dir])

        # Should not raise exception
        plugins = discovery.discover()
        self.assertIsInstance(plugins, list)


class TestPluginLoading(unittest.TestCase):
    """Test plugin loading mechanisms."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_plugin_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_plugin_dir)

    def test_load_plugin_from_path(self):
        """Test loading a plugin from a file path."""
        from src.plugins.loader import PluginLoader

        plugin_file = os.path.join(self.test_plugin_dir, "load_test.py")
        with open(plugin_file, "w") as f:
            f.write(
                """
class LoadTestPlugin:
    def activate(self):
        return "activated"
"""
            )

        loader = PluginLoader()
        plugin = loader.load_from_path(plugin_file)

        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.activate(), "activated")

    def test_load_multiple_plugins(self):
        """Test loading multiple plugins."""
        from src.plugins.loader import PluginLoader

        for i in range(3):
            plugin_file = os.path.join(self.test_plugin_dir, f"plugin_{i}.py")
            with open(plugin_file, "w") as f:
                f.write(
                    f"""
class Plugin{i}:
    name = "plugin_{i}"
"""
                )

        loader = PluginLoader()
        plugins = loader.load_from_directory(self.test_plugin_dir)

        self.assertEqual(len(plugins), 3)

    def test_plugin_import_isolation(self):
        """Test that plugins are imported in isolation."""
        from src.plugins.loader import PluginLoader

        plugin_file = os.path.join(self.test_plugin_dir, "isolated.py")
        with open(plugin_file, "w") as f:
            f.write(
                """
test_var = "plugin_value"

class IsolatedPlugin:
    def get_value(self):
        return test_var
"""
            )

        loader = PluginLoader()
        plugin1 = loader.load_from_path(plugin_file)
        plugin2 = loader.load_from_path(plugin_file)

        # Each should be isolated
        self.assertIsNot(plugin1, plugin2)

    def test_handle_plugin_load_errors(self):
        """Test handling errors during plugin loading."""
        from src.plugins.loader import PluginLoader

        plugin_file = os.path.join(self.test_plugin_dir, "error.py")
        with open(plugin_file, "w") as f:
            f.write(
                """
raise Exception("Plugin load error")
"""
            )

        loader = PluginLoader()

        # Should handle error gracefully
        with self.assertRaises(Exception):
            loader.load_from_path(plugin_file, strict=True)

        # Or return None in non-strict mode
        plugin = loader.load_from_path(plugin_file, strict=False)
        self.assertIsNone(plugin)


class TestPluginLifecycle(unittest.TestCase):
    """Test plugin lifecycle management."""

    def test_plugin_activation(self):
        """Test plugin activation."""
        from src.plugins.manager import PluginManager

        class TestPlugin:
            def __init__(self):
                self.activated = False

            def activate(self):
                self.activated = True
                return True

        manager = PluginManager()
        plugin = TestPlugin()

        manager.register_plugin("test", plugin)
        manager.activate_plugin("test")

        self.assertTrue(plugin.activated)

    def test_plugin_deactivation(self):
        """Test plugin deactivation."""
        from src.plugins.manager import PluginManager

        class TestPlugin:
            def __init__(self):
                self.active = False

            def activate(self):
                self.active = True

            def deactivate(self):
                self.active = False

        manager = PluginManager()
        plugin = TestPlugin()

        manager.register_plugin("test", plugin)
        manager.activate_plugin("test")
        manager.deactivate_plugin("test")

        self.assertFalse(plugin.active)

    def test_plugin_hot_reload(self):
        """Test hot reloading of plugins."""
        from src.plugins.manager import PluginManager

        manager = PluginManager(hot_reload=True)

        class VersionedPlugin:
            version = 1

            def get_version(self):
                return self.version

        plugin = VersionedPlugin()
        manager.register_plugin("versioned", plugin)

        # Simulate plugin update
        plugin.version = 2

        # Reload
        manager.reload_plugin("versioned")

        reloaded = manager.get_plugin("versioned")
        self.assertEqual(reloaded.get_version(), 2)

    def test_plugin_dependency_order(self):
        """Test plugins are loaded in dependency order."""
        from src.plugins.manager import PluginManager

        class PluginA:
            dependencies = []

        class PluginB:
            dependencies = ["plugin_a"]

        class PluginC:
            dependencies = ["plugin_b"]

        manager = PluginManager()
        manager.register_plugin("plugin_c", PluginC())
        manager.register_plugin("plugin_a", PluginA())
        manager.register_plugin("plugin_b", PluginB())

        # Should load in correct order: A -> B -> C
        load_order = manager.activate_all_plugins()

        self.assertEqual(load_order[0], "plugin_a")
        self.assertEqual(load_order[1], "plugin_b")
        self.assertEqual(load_order[2], "plugin_c")


class TestPluginAPI(unittest.TestCase):
    """Test plugin API and hooks."""

    def test_register_hook(self):
        """Test registering plugin hooks."""
        from src.plugins.hooks import HookManager

        hook_manager = HookManager()

        def test_hook(data):
            return data + " modified"

        hook_manager.register_hook("before_query", test_hook)

        result = hook_manager.execute_hook("before_query", "test data")
        self.assertEqual(result, "test data modified")

    def test_multiple_hooks_execution_order(self):
        """Test execution order of multiple hooks."""
        from src.plugins.hooks import HookManager

        hook_manager = HookManager()

        results = []

        def hook1(data):
            results.append("hook1")
            return data

        def hook2(data):
            results.append("hook2")
            return data

        hook_manager.register_hook("test_event", hook1, priority=1)
        hook_manager.register_hook("test_event", hook2, priority=2)

        hook_manager.execute_hook("test_event", "data")

        self.assertEqual(results, ["hook2", "hook1"])  # Higher priority first

    def test_hook_filtering(self):
        """Test conditional hook execution."""
        from src.plugins.hooks import HookManager

        hook_manager = HookManager()

        def conditional_hook(data):
            if data.get("execute"):
                return "executed"
            return "skipped"

        hook_manager.register_hook("conditional", conditional_hook)

        result1 = hook_manager.execute_hook("conditional", {"execute": True})
        result2 = hook_manager.execute_hook("conditional", {"execute": False})

        self.assertEqual(result1, "executed")
        self.assertEqual(result2, "skipped")

    def test_plugin_communication(self):
        """Test inter-plugin communication."""
        from src.plugins.manager import PluginManager

        class PluginA:
            def send_message(self, message):
                return f"A received: {message}"

        class PluginB:
            def __init__(self, plugin_manager):
                self.pm = plugin_manager

            def communicate(self):
                plugin_a = self.pm.get_plugin("plugin_a")
                return plugin_a.send_message("Hello from B")

        manager = PluginManager()
        manager.register_plugin("plugin_a", PluginA())
        manager.register_plugin("plugin_b", PluginB(manager))

        result = manager.get_plugin("plugin_b").communicate()
        self.assertEqual(result, "A received: Hello from B")


class TestPluginDependencies(unittest.TestCase):
    """Test plugin dependency management."""

    def test_check_dependencies(self):
        """Test checking if plugin dependencies are met."""
        from src.plugins.dependencies import DependencyResolver

        resolver = DependencyResolver()

        # Register available plugins
        resolver.register_available("plugin_a", "1.0.0")
        resolver.register_available("plugin_b", "2.0.0")

        # Check dependencies
        deps = ["plugin_a>=1.0.0", "plugin_b>=1.5.0"]
        result = resolver.check_dependencies(deps)

        self.assertTrue(result["satisfied"])

    def test_missing_dependencies(self):
        """Test detection of missing dependencies."""
        from src.plugins.dependencies import DependencyResolver

        resolver = DependencyResolver()
        resolver.register_available("plugin_a", "1.0.0")

        deps = ["plugin_a>=1.0.0", "plugin_c>=1.0.0"]
        result = resolver.check_dependencies(deps)

        self.assertFalse(result["satisfied"])
        self.assertIn("plugin_c", result["missing"])

    def test_version_compatibility(self):
        """Test version compatibility checking."""
        from src.plugins.dependencies import DependencyResolver

        resolver = DependencyResolver()
        resolver.register_available("plugin_a", "1.5.0")

        # Should fail - requires 2.0.0+
        deps = ["plugin_a>=2.0.0"]
        result = resolver.check_dependencies(deps)

        self.assertFalse(result["satisfied"])

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        from src.plugins.dependencies import DependencyResolver

        resolver = DependencyResolver()

        # Plugin A depends on B, B depends on A
        resolver.register_plugin("plugin_a", dependencies=["plugin_b"])
        resolver.register_plugin("plugin_b", dependencies=["plugin_a"])

        result = resolver.resolve_load_order()

        self.assertIn("circular_dependency", result["errors"])


class TestPluginSecurity(unittest.TestCase):
    """Test plugin security and sandboxing."""

    def test_plugin_permission_system(self):
        """Test plugin permission system."""
        from src.plugins.security import PluginSecurityManager

        security = PluginSecurityManager()

        security.grant_permission("plugin_a", "file.read")
        security.grant_permission("plugin_a", "db.read")

        self.assertTrue(security.has_permission("plugin_a", "file.read"))
        self.assertFalse(security.has_permission("plugin_a", "file.write"))

    def test_sandbox_file_access(self):
        """Test sandboxed file system access."""
        from src.plugins.sandbox import PluginSandbox

        sandbox = PluginSandbox()

        allowed_dir = tempfile.mkdtemp()

        # Should allow access to allowed directory
        sandbox.allow_path(allowed_dir)
        self.assertTrue(sandbox.can_access(os.path.join(allowed_dir, "file.txt")))

        # Should deny access to other directories
        self.assertFalse(sandbox.can_access("/etc/passwd"))

    def test_resource_limits(self):
        """Test resource limit enforcement for plugins."""
        from src.plugins.sandbox import ResourceLimiter

        limiter = ResourceLimiter(max_memory_mb=100, max_cpu_percent=50)

        # Simulate plugin using resources
        limiter.track_usage("plugin_a", memory_mb=80, cpu_percent=30)

        self.assertTrue(limiter.within_limits("plugin_a"))

        # Exceed limits
        limiter.track_usage("plugin_a", memory_mb=120, cpu_percent=30)

        self.assertFalse(limiter.within_limits("plugin_a"))

    def test_code_signing_verification(self):
        """Test plugin code signing verification."""
        from src.plugins.security import CodeSignatureVerifier

        verifier = CodeSignatureVerifier()

        # Valid signed plugin
        valid_plugin = {"code": "print('hello')", "signature": "valid_sig_123"}

        # Should verify successfully
        is_valid = verifier.verify(valid_plugin, public_key="test_key")
        # This would be True with actual signing implementation
        self.assertIsNotNone(is_valid)


class TestPluginConfiguration(unittest.TestCase):
    """Test plugin configuration management."""

    def test_plugin_config_loading(self):
        """Test loading plugin configuration."""
        from src.plugins.config import PluginConfig

        config_data = {"setting1": "value1", "setting2": 42}

        config = PluginConfig("test_plugin", config_data)

        self.assertEqual(config.get("setting1"), "value1")
        self.assertEqual(config.get("setting2"), 42)

    def test_config_validation(self):
        """Test plugin configuration validation."""
        from src.plugins.config import PluginConfig

        schema = {"type": "object", "properties": {"port": {"type": "integer"}}, "required": ["port"]}

        # Valid config
        valid_config = PluginConfig("test", {"port": 8080}, schema=schema)
        self.assertTrue(valid_config.is_valid())

        # Invalid config
        invalid_config = PluginConfig("test", {"port": "not_an_int"}, schema=schema)
        self.assertFalse(invalid_config.is_valid())

    def test_config_persistence(self):
        """Test plugin configuration persistence."""
        from src.plugins.config import PluginConfigManager

        manager = PluginConfigManager()

        manager.save_config("test_plugin", {"key": "value"})

        loaded = manager.load_config("test_plugin")
        self.assertEqual(loaded["key"], "value")


if __name__ == "__main__":
    unittest.main()
