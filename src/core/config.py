"""
Configuration Management System

Supports YAML configuration files with environment variable overrides.
"""

import os
import yaml
import logging
from typing import Any, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration manager with YAML support and environment variable overrides.

    Features:
    - Load from YAML files
    - Environment variable overrides (AI_SHELL_*)
    - Nested configuration access with dot notation
    - Configuration validation
    """

    DEFAULT_CONFIG_PATHS = [
        Path.home() / '.ai-shell' / 'config.yaml',
        Path.cwd() / 'config' / 'ai-shell-config.yaml',
        Path.cwd() / 'ai-shell-config.yaml'
    ]

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize configuration manager.

        Args:
            config_path: Optional path to config file. If None, searches default locations.
        """
        self.config_path = Path(config_path) if config_path else None
        self.config: Dict[str, Any] = {}
        self.loaded = False

        logger.info(f"ConfigManager created with path: {self.config_path}")

    async def load(self) -> None:
        """
        Load configuration from file and apply environment overrides.

        Raises:
            FileNotFoundError: If config file not found and no defaults available
        """
        # Determine config file to use
        if self.config_path and self.config_path.exists():
            config_file = self.config_path
        else:
            # Search default locations
            config_file = None
            for path in self.DEFAULT_CONFIG_PATHS:
                if path.exists():
                    config_file = path
                    break

        # Apply environment variable overrides FIRST
        env_overrides = self._get_env_overrides()

        # Load from file if found
        if config_file:
            logger.info(f"Loading configuration from: {config_file}")
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            logger.warning("No configuration file found, using defaults")
            self.config = self._get_default_config()

        # Apply env overrides AFTER loading
        for path_tuple, value in env_overrides.items():
            path_list = list(path_tuple) if isinstance(path_tuple, tuple) else [path_tuple]
            self._set_nested_value(path_list, value)

        self.loaded = True
        logger.info("Configuration loaded successfully")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'startup_animation': True,
                'matrix_style': 'enhanced'
            },
            'llm': {
                'models': {
                    'intent': 'llama2:7b',
                    'completion': 'codellama:13b',
                    'anonymizer': 'mistral:7b'
                },
                'ollama_host': 'localhost:11434'
            },
            'mcp': {
                'oracle': {
                    'thin_mode': True,
                    'connection_pool_size': 5
                },
                'postgresql': {
                    'connection_pool_size': 5
                }
            },
            'ui': {
                'framework': 'textual',
                'theme': 'cyberpunk',
                'panel_priority': {
                    'typing': 'prompt',
                    'idle': 'balanced'
                }
            },
            'security': {
                'vault_backend': 'keyring',
                'auto_redaction': True,
                'sensitive_commands_require_confirmation': True
            },
            'performance': {
                'async_workers': 4,
                'cache_size': 1000,
                'vector_db_dimension': 384
            }
        }

    def _get_env_overrides(self) -> Dict[tuple, Any]:
        """
        Get environment variable overrides.

        Environment variables format: AI_SHELL_<SECTION>_<KEY>
        Example: AI_SHELL_LLM_MODELS_INTENT=mistral:7b

        Returns:
            Dictionary of path tuples to values
        """
        prefix = 'AI_SHELL_'
        overrides = {}

        for env_var, value in os.environ.items():
            if not env_var.startswith(prefix):
                continue

            # Parse environment variable path
            path = tuple(env_var[len(prefix):].lower().split('_'))
            overrides[path] = value
            logger.debug(f"Found env override: {env_var} = {value}")

        return overrides

    def _set_nested_value(self, path: list, value: Any) -> None:
        """Set a value in nested dictionary using path"""
        current = self.config

        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # Overwrite non-dict values with dict
                current[key] = {}
            current = current[key]

        # Convert string values to appropriate types
        final_value = self._convert_value(value) if isinstance(value, str) else value
        current[path[-1]] = final_value

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'llm.models.intent')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        parts = key.split('.')
        current = self.config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.

        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        parts = key.split('.')
        self._set_nested_value(parts, value)
        logger.debug(f"Config updated: {key} = {value}")

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.

        Args:
            section: Section name (e.g., 'llm', 'mcp')

        Returns:
            Section dictionary or empty dict if not found
        """
        return self.config.get(section, {})

    def validate(self) -> bool:
        """
        Validate configuration has required fields.

        Returns:
            True if valid, False otherwise
        """
        required_sections = ['system', 'llm', 'mcp', 'ui', 'security', 'performance']

        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required config section: {section}")
                return False

        logger.info("Configuration validation passed")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Get complete configuration as dictionary"""
        return self.config.copy()
