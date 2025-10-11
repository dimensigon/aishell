"""Plugin configuration management and validation."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PluginConfig:
    """Manages configuration for a single plugin."""

    def __init__(self, plugin_name: str, config_data: Dict[str, Any],
                 schema: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin configuration.

        Args:
            plugin_name: Name of the plugin
            config_data: Configuration dictionary
            schema: Optional JSON schema for validation
        """
        self.plugin_name = plugin_name
        self.config_data = config_data
        self.schema = schema
        self.logger = logging.getLogger(f"plugin.config.{plugin_name}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config_data[key] = value

    def is_valid(self) -> bool:
        """
        Validate configuration against schema.

        Returns:
            True if configuration is valid
        """
        if not self.schema:
            return True

        try:
            import jsonschema
            jsonschema.validate(instance=self.config_data, schema=self.schema)
            return True
        except ImportError:
            self.logger.warning("jsonschema not installed, skipping validation")
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config_data.copy()


class PluginConfigManager:
    """Manages configurations for all plugins."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize plugin configuration manager.

        Args:
            config_dir: Directory to store plugin configurations
        """
        self.config_dir = config_dir or Path.home() / ".ai-shell" / "plugin-configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("plugin.config_manager")
        self._configs: Dict[str, Dict[str, Any]] = {}

    def save_config(self, plugin_name: str, config_data: Dict[str, Any]) -> None:
        """
        Save plugin configuration to disk.

        Args:
            plugin_name: Name of the plugin
            config_data: Configuration dictionary
        """
        config_file = self.config_dir / f"{plugin_name}.json"

        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            self._configs[plugin_name] = config_data
            self.logger.debug(f"Saved configuration for {plugin_name}")

        except Exception as e:
            self.logger.error(f"Failed to save configuration for {plugin_name}: {e}")
            raise

    def load_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Load plugin configuration from disk.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Configuration dictionary
        """
        # Check cache first
        if plugin_name in self._configs:
            return self._configs[plugin_name].copy()

        config_file = self.config_dir / f"{plugin_name}.json"

        if not config_file.exists():
            return {}

        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            self._configs[plugin_name] = config_data
            self.logger.debug(f"Loaded configuration for {plugin_name}")

            return config_data.copy()

        except Exception as e:
            self.logger.error(f"Failed to load configuration for {plugin_name}: {e}")
            return {}

    def delete_config(self, plugin_name: str) -> bool:
        """
        Delete plugin configuration.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if configuration was deleted
        """
        config_file = self.config_dir / f"{plugin_name}.json"

        try:
            if config_file.exists():
                config_file.unlink()

            if plugin_name in self._configs:
                del self._configs[plugin_name]

            self.logger.debug(f"Deleted configuration for {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete configuration for {plugin_name}: {e}")
            return False

    def list_configs(self) -> list:
        """
        List all plugin configurations.

        Returns:
            List of plugin names with configurations
        """
        configs = []

        for config_file in self.config_dir.glob("*.json"):
            plugin_name = config_file.stem
            configs.append(plugin_name)

        return configs
