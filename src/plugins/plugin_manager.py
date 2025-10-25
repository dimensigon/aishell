"""
AI-Shell Plugin Manager

Manages plugin discovery, loading, and lifecycle for AI-Shell extensions.
"""

import importlib
import importlib.util
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
import json


logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    author: str
    description: str
    homepage: str
    license: str
    tags: List[str]
    dependencies: List[str]
    entry_point: str
    config_schema: Optional[Dict[str, Any]] = None


class PluginError(Exception):
    """Base exception for plugin errors"""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin fails to load"""
    pass


class PluginValidationError(PluginError):
    """Raised when plugin validation fails"""
    pass


class BasePlugin:
    """
    Base class for all AI-Shell plugins.

    All plugins must inherit from this class and implement
    the required methods.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin.

        Args:
            config: Plugin configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"plugin.{self.get_name()}")

    @classmethod
    def get_name(cls) -> str:
        """
        Get plugin name.

        Returns:
            Plugin name
        """
        raise NotImplementedError("Plugins must implement get_name()")

    @classmethod
    def get_version(cls) -> str:
        """
        Get plugin version.

        Returns:
            Plugin version string
        """
        raise NotImplementedError("Plugins must implement get_version()")

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """
        Get plugin metadata.

        Returns:
            PluginMetadata instance
        """
        raise NotImplementedError("Plugins must implement get_metadata()")

    async def initialize(self) -> None:
        """Initialize plugin resources. Called when plugin is loaded."""
        pass

    async def start(self) -> None:
        """Start plugin operations. Called after initialization."""
        pass

    async def stop(self) -> None:
        """Stop plugin operations. Called when plugin is being unloaded."""
        pass

    async def cleanup(self) -> None:
        """Cleanup plugin resources. Called after stop, before plugin is destroyed."""
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        return True


class PluginManager:
    """
    Manages plugin lifecycle and operations.

    Features:
    - Plugin discovery and loading
    - Dependency resolution
    - Lifecycle management
    - Configuration validation
    - Hot-reloading support
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None, hot_reload: bool = False) -> None:
        """
        Initialize plugin manager.

        Args:
            plugin_dirs: List of directories to search for plugins
            hot_reload: Enable hot-reloading support
        """
        self.plugin_dirs = plugin_dirs or [
            Path.home() / ".ai-shell" / "plugins",
            Path(__file__).parent.parent.parent / "plugins"
        ]

        self.plugins: Dict[str, Any] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.hot_reload = hot_reload
        self._active_plugins: Dict[str, bool] = {}

        self.logger = logging.getLogger("plugin_manager")

    def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover available plugins in plugin directories.

        Returns:
            List of discovered plugin metadata
        """
        discovered = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            self.logger.info(f"Scanning for plugins in: {plugin_dir}")

            # Look for plugin.json files
            for plugin_json in plugin_dir.rglob("plugin.json"):
                try:
                    metadata = self._load_plugin_metadata(plugin_json)
                    discovered.append(metadata)
                    self.logger.info(f"Discovered plugin: {metadata.name} v{metadata.version}")
                except Exception as e:
                    self.logger.error(f"Failed to load plugin metadata from {plugin_json}: {e}")

        return discovered

    def _load_plugin_metadata(self, plugin_json: Path) -> PluginMetadata:
        """Load plugin metadata from plugin.json file"""
        with open(plugin_json, 'r') as f:
            data = json.load(f)

        return PluginMetadata(
            name=data["name"],
            version=data["version"],
            author=data.get("author", "Unknown"),
            description=data.get("description", ""),
            homepage=data.get("homepage", ""),
            license=data.get("license", ""),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            entry_point=data["entry_point"],
            config_schema=data.get("config_schema")
        )

    def load_plugin(self, name: str, config: Optional[Dict[str, Any]] = None) -> BasePlugin:
        """
        Load and initialize a plugin.

        Args:
            name: Plugin name
            config: Plugin configuration

        Returns:
            Initialized plugin instance

        Raises:
            PluginLoadError: If plugin loading fails
        """
        if name in self.plugins:
            self.logger.warning(f"Plugin {name} already loaded")
            return self.plugins[name]

        try:
            # Find plugin
            metadata = self._find_plugin(name)
            if not metadata:
                raise PluginLoadError(f"Plugin not found: {name}")

            # Check dependencies
            self._check_dependencies(metadata)

            # Load plugin class
            plugin_class = self._load_plugin_class(metadata)

            # Validate configuration
            config = config or {}
            if not self._validate_config(plugin_class, config, metadata.config_schema):
                raise PluginValidationError(f"Invalid configuration for plugin: {name}")

            # Instantiate plugin
            plugin = plugin_class(config)

            # Store plugin
            self.plugins[name] = plugin
            self.plugin_classes[name] = plugin_class
            self.metadata[name] = metadata

            self.logger.info(f"Loaded plugin: {name} v{metadata.version}")

            return plugin

        except Exception as e:
            self.logger.error(f"Failed to load plugin {name}: {e}")
            raise PluginLoadError(f"Failed to load plugin {name}: {e}")

    def _find_plugin(self, name: str) -> Optional[PluginMetadata]:
        """Find plugin metadata by name"""
        for plugin_dir in self.plugin_dirs:
            plugin_json = plugin_dir / name / "plugin.json"
            if plugin_json.exists():
                return self._load_plugin_metadata(plugin_json)
        return None

    def _check_dependencies(self, metadata: PluginMetadata) -> None:
        """Check if plugin dependencies are satisfied"""
        for dep in metadata.dependencies:
            if dep not in self.plugins:
                raise PluginLoadError(
                    f"Missing dependency for plugin {metadata.name}: {dep}"
                )

    def _load_plugin_class(self, metadata: PluginMetadata) -> Type[BasePlugin]:
        """Load plugin class from entry point"""
        # Find plugin directory
        plugin_dir = None
        for search_dir in self.plugin_dirs:
            candidate = search_dir / metadata.name
            if candidate.exists():
                plugin_dir = candidate
                break

        if not plugin_dir:
            raise PluginLoadError(f"Plugin directory not found for: {metadata.name}")

        # Add to sys.path
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))

        # Parse entry point (e.g., "mymodule:MyPluginClass")
        module_name, class_name = metadata.entry_point.split(":")

        # Import module
        spec = importlib.util.spec_from_file_location(
            module_name,
            plugin_dir / f"{module_name}.py"
        )

        if not spec or not spec.loader:
            raise PluginLoadError(f"Failed to load module: {module_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Get plugin class
        plugin_class = getattr(module, class_name)

        if not issubclass(plugin_class, BasePlugin):
            raise PluginLoadError(
                f"Plugin class must inherit from BasePlugin: {class_name}"
            )

        return plugin_class

    def _validate_config(
        self,
        plugin_class: Type[BasePlugin],
        config: Dict[str, Any],
        schema: Optional[Dict[str, Any]]
    ) -> bool:
        """Validate plugin configuration"""
        # Use plugin's validation method
        temp_plugin = plugin_class(config)
        if not temp_plugin.validate_config(config):
            return False

        # Validate against JSON schema if provided
        if schema:
            try:
                import jsonschema
                jsonschema.validate(instance=config, schema=schema)
            except ImportError:
                self.logger.warning("jsonschema not installed, skipping schema validation")
            except jsonschema.ValidationError as e:
                self.logger.error(f"Configuration validation failed: {e}")
                return False

        return True

    async def start_plugin(self, name: str) -> None:
        """Start a loaded plugin.

        Args:
            name: Plugin name
        """
        if name not in self.plugins:
            raise PluginError(f"Plugin not loaded: {name}")

        plugin = self.plugins[name]

        try:
            await plugin.initialize()
            await plugin.start()
            self.logger.info(f"Started plugin: {name}")
        except Exception as e:
            self.logger.error(f"Failed to start plugin {name}: {e}")
            raise

    async def stop_plugin(self, name: str) -> None:
        """Stop a running plugin.

        Args:
            name: Plugin name
        """
        if name not in self.plugins:
            raise PluginError(f"Plugin not loaded: {name}")

        plugin = self.plugins[name]

        try:
            await plugin.stop()
            await plugin.cleanup()
            self.logger.info(f"Stopped plugin: {name}")
        except Exception as e:
            self.logger.error(f"Failed to stop plugin {name}: {e}")
            raise

    def unload_plugin(self, name: str) -> None:
        """
        Unload a plugin.

        Args:
            name: Plugin name
        """
        if name not in self.plugins:
            return

        # Remove from loaded plugins
        del self.plugins[name]
        del self.plugin_classes[name]
        del self.metadata[name]

        self.logger.info(f"Unloaded plugin: {name}")

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get loaded plugin instance.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not loaded
        """
        return self.plugins.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins.

        Returns:
            List of plugin information dictionaries
        """
        return [
            {
                "name": name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "status": "loaded"
            }
            for name, metadata in self.metadata.items()
        ]

    async def reload_plugin(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Reload a plugin with optional new configuration.

        Args:
            name: Plugin name
            config: New configuration (optional)
        """
        if name in self.plugins:
            await self.stop_plugin(name)
            self.unload_plugin(name)

        self.load_plugin(name, config)
        await self.start_plugin(name)

        self.logger.info(f"Reloaded plugin: {name}")

    def register_plugin(self, name: str, plugin: Any) -> None:
        """
        Register a plugin instance directly (for testing).

        Args:
            name: Plugin name
            plugin: Plugin instance
        """
        self.plugins[name] = plugin
        self._active_plugins[name] = False
        self.logger.debug(f"Registered plugin: {name}")

    def activate_plugin(self, name: str) -> bool:
        """
        Activate a registered plugin.

        Args:
            name: Plugin name

        Returns:
            True if activated successfully
        """
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]

        # Call activate method if exists
        if hasattr(plugin, 'activate'):
            result = plugin.activate()
            self._active_plugins[name] = True
            return result if result is not None else True

        self._active_plugins[name] = True
        return True

    def deactivate_plugin(self, name: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            name: Plugin name

        Returns:
            True if deactivated successfully
        """
        if name not in self.plugins:
            return False

        plugin = self.plugins[name]

        # Call deactivate method if exists
        if hasattr(plugin, 'deactivate'):
            plugin.deactivate()

        self._active_plugins[name] = False
        return True

    def activate_all_plugins(self) -> List[str]:
        """
        Activate all plugins in dependency order.

        Returns:
            List of plugin names in activation order
        """
        # Build dependency graph
        activation_order = []
        activated = set()

        def activate_with_deps(plugin_name: str):
            if plugin_name in activated:
                return

            plugin = self.plugins.get(plugin_name)
            if not plugin:
                return

            # Get dependencies
            deps = getattr(plugin, 'dependencies', [])

            # Activate dependencies first
            for dep in deps:
                activate_with_deps(dep)

            # Activate this plugin
            self.activate_plugin(plugin_name)
            activated.add(plugin_name)
            activation_order.append(plugin_name)

        # Activate all plugins
        for name in self.plugins.keys():
            activate_with_deps(name)

        return activation_order


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    Get global plugin manager instance.

    Returns:
        PluginManager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
