"""Comprehensive tests for plugin configuration module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.plugins.config import PluginConfig, PluginConfigManager


class TestPluginConfig:
    """Test suite for PluginConfig class."""

    @pytest.fixture
    def config(self):
        """Create a plugin config instance."""
        config_data = {
            "timeout": 30,
            "retries": 3,
            "enabled": True
        }
        return PluginConfig("test_plugin", config_data)

    def test_config_initialization(self, config):
        """Test config initialization."""
        assert config.plugin_name == "test_plugin"
        assert config.config_data is not None
        assert config.schema is None

    def test_config_with_schema(self):
        """Test config initialization with schema."""
        schema = {
            "type": "object",
            "properties": {
                "timeout": {"type": "number"}
            }
        }

        config = PluginConfig("test", {}, schema=schema)

        assert config.schema is not None

    def test_get_existing_key(self, config):
        """Test getting existing configuration key."""
        value = config.get("timeout")

        assert value == 30

    def test_get_nonexistent_key(self, config):
        """Test getting non-existent key."""
        value = config.get("nonexistent")

        assert value is None

    def test_get_with_default(self, config):
        """Test getting key with default value."""
        value = config.get("nonexistent", "default_value")

        assert value == "default_value"

    def test_set_value(self, config):
        """Test setting configuration value."""
        config.set("new_key", "new_value")

        assert config.get("new_key") == "new_value"

    def test_set_overwrite(self, config):
        """Test overwriting existing value."""
        config.set("timeout", 60)

        assert config.get("timeout") == 60

    def test_is_valid_without_schema(self, config):
        """Test validation without schema."""
        # Should always return True without schema
        assert config.is_valid() is True

    def test_is_valid_with_schema_valid_data(self):
        """Test validation with valid data."""
        schema = {
            "type": "object",
            "properties": {
                "timeout": {"type": "number"}
            },
            "required": ["timeout"]
        }

        config_data = {"timeout": 30}
        config = PluginConfig("test", config_data, schema=schema)

        # Note: requires jsonschema library
        try:
            assert config.is_valid() is True
        except ImportError:
            pytest.skip("jsonschema not installed")

    def test_is_valid_with_schema_invalid_data(self):
        """Test validation with invalid data."""
        schema = {
            "type": "object",
            "properties": {
                "timeout": {"type": "number"}
            },
            "required": ["timeout"]
        }

        config_data = {"timeout": "not_a_number"}
        config = PluginConfig("test", config_data, schema=schema)

        try:
            assert config.is_valid() is False
        except ImportError:
            pytest.skip("jsonschema not installed")

    def test_to_dict(self, config):
        """Test converting config to dictionary."""
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["timeout"] == 30
        assert config_dict["retries"] == 3

    def test_to_dict_returns_copy(self, config):
        """Test that to_dict returns a copy."""
        config_dict = config.to_dict()
        config_dict["timeout"] = 100

        # Original should be unchanged
        assert config.get("timeout") == 30


class TestPluginConfigManager:
    """Test suite for PluginConfigManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a config manager with temp directory."""
        return PluginConfigManager(config_dir=tmp_path)

    def test_manager_initialization(self, tmp_path):
        """Test manager initialization."""
        manager = PluginConfigManager(config_dir=tmp_path)

        assert manager.config_dir == tmp_path
        assert manager.config_dir.exists()

    def test_manager_default_config_dir(self):
        """Test manager with default config directory."""
        manager = PluginConfigManager()

        # Should create directory in home
        assert ".ai-shell" in str(manager.config_dir)

    def test_save_config(self, manager):
        """Test saving plugin configuration."""
        config_data = {"timeout": 30, "enabled": True}

        manager.save_config("test_plugin", config_data)

        # Check file was created
        config_file = manager.config_dir / "test_plugin.json"
        assert config_file.exists()

        # Check content
        with open(config_file) as f:
            saved_data = json.load(f)

        assert saved_data == config_data

    def test_save_config_overwrites(self, manager):
        """Test that saving overwrites existing config."""
        config_data1 = {"version": 1}
        config_data2 = {"version": 2}

        manager.save_config("test_plugin", config_data1)
        manager.save_config("test_plugin", config_data2)

        loaded = manager.load_config("test_plugin")

        assert loaded["version"] == 2

    def test_load_config(self, manager):
        """Test loading plugin configuration."""
        config_data = {"timeout": 30, "enabled": True}
        manager.save_config("test_plugin", config_data)

        loaded = manager.load_config("test_plugin")

        assert loaded == config_data

    def test_load_config_nonexistent(self, manager):
        """Test loading non-existent config."""
        loaded = manager.load_config("nonexistent_plugin")

        assert loaded == {}

    def test_load_config_uses_cache(self, manager):
        """Test that load_config uses cache."""
        config_data = {"value": 42}
        manager.save_config("test_plugin", config_data)

        # Load first time
        loaded1 = manager.load_config("test_plugin")

        # Modify file directly
        config_file = manager.config_dir / "test_plugin.json"
        with open(config_file, 'w') as f:
            json.dump({"value": 100}, f)

        # Load again (should use cache)
        loaded2 = manager.load_config("test_plugin")

        assert loaded2["value"] == 42  # From cache

    def test_delete_config(self, manager):
        """Test deleting plugin configuration."""
        config_data = {"value": 1}
        manager.save_config("test_plugin", config_data)

        result = manager.delete_config("test_plugin")

        assert result is True

        # File should be gone
        config_file = manager.config_dir / "test_plugin.json"
        assert not config_file.exists()

    def test_delete_config_nonexistent(self, manager):
        """Test deleting non-existent config."""
        result = manager.delete_config("nonexistent")

        # Should return True even if file doesn't exist
        assert result is True

    def test_delete_config_clears_cache(self, manager):
        """Test that delete clears cache."""
        manager.save_config("test_plugin", {"value": 1})
        manager.load_config("test_plugin")  # Cache it

        manager.delete_config("test_plugin")

        # Should not be in cache
        assert "test_plugin" not in manager._configs

    def test_list_configs_empty(self, manager):
        """Test listing configs when none exist."""
        configs = manager.list_configs()

        assert configs == []

    def test_list_configs_with_configs(self, manager):
        """Test listing multiple configs."""
        manager.save_config("plugin1", {"a": 1})
        manager.save_config("plugin2", {"b": 2})
        manager.save_config("plugin3", {"c": 3})

        configs = manager.list_configs()

        assert len(configs) == 3
        assert "plugin1" in configs
        assert "plugin2" in configs
        assert "plugin3" in configs

    def test_save_complex_config(self, manager):
        """Test saving complex configuration."""
        config_data = {
            "nested": {
                "value": 42,
                "items": [1, 2, 3]
            },
            "enabled": True,
            "options": ["opt1", "opt2"]
        }

        manager.save_config("complex_plugin", config_data)
        loaded = manager.load_config("complex_plugin")

        assert loaded == config_data

    def test_save_config_with_unicode(self, manager):
        """Test saving config with Unicode characters."""
        config_data = {
            "message": "Hello 世界",
            "emoji": "🚀"
        }

        manager.save_config("unicode_plugin", config_data)
        loaded = manager.load_config("unicode_plugin")

        assert loaded == config_data

    def test_concurrent_save_operations(self, manager):
        """Test concurrent save operations."""
        import concurrent.futures

        def save_config(i):
            manager.save_config(f"plugin_{i}", {"id": i})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(save_config, i) for i in range(10)]
            [f.result() for f in concurrent.futures.as_completed(futures)]

        # All configs should be saved
        configs = manager.list_configs()
        assert len(configs) == 10

    def test_concurrent_load_operations(self, manager):
        """Test concurrent load operations."""
        import concurrent.futures

        # Prep configs
        for i in range(5):
            manager.save_config(f"plugin_{i}", {"id": i})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(manager.load_config, f"plugin_{i}")
                      for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should load successfully
        assert len(results) == 5


class TestPluginConfigEdgeCases:
    """Test edge cases in configuration management."""

    def test_config_empty_data(self):
        """Test config with empty data."""
        config = PluginConfig("test", {})

        assert config.to_dict() == {}

    def test_config_none_values(self):
        """Test config with None values."""
        config = PluginConfig("test", {"key": None})

        assert config.get("key") is None

    def test_config_special_characters_in_name(self, tmp_path):
        """Test config with special characters in plugin name."""
        manager = PluginConfigManager(config_dir=tmp_path)

        # Some filesystems may not support all characters
        try:
            manager.save_config("plugin:with:colons", {"value": 1})
            loaded = manager.load_config("plugin:with:colons")
            assert loaded["value"] == 1
        except OSError:
            pytest.skip("Filesystem doesn't support special characters")

    def test_config_very_large_data(self, tmp_path):
        """Test saving very large configuration."""
        manager = PluginConfigManager(config_dir=tmp_path)

        # Create large config
        large_data = {
            f"key_{i}": f"value_{i}" * 100
            for i in range(1000)
        }

        manager.save_config("large_plugin", large_data)
        loaded = manager.load_config("large_plugin")

        assert len(loaded) == 1000

    def test_config_file_permissions(self, tmp_path):
        """Test handling of file permission errors."""
        manager = PluginConfigManager(config_dir=tmp_path)

        # Save a config
        manager.save_config("test", {"value": 1})

        # Make config dir read-only (Unix only)
        import os
        import stat

        try:
            os.chmod(tmp_path, stat.S_IRUSR | stat.S_IXUSR)

            # Try to save (should raise)
            with pytest.raises(PermissionError):
                manager.save_config("test2", {"value": 2})
        except Exception:
            pytest.skip("Cannot test permissions on this platform")
        finally:
            # Restore permissions
            os.chmod(tmp_path, stat.S_IRWXU)

    def test_config_corrupted_json(self, tmp_path):
        """Test loading corrupted JSON file."""
        manager = PluginConfigManager(config_dir=tmp_path)

        # Create corrupted JSON file
        config_file = tmp_path / "corrupted.json"
        config_file.write_text("{invalid json content")

        # Should return empty dict on error
        loaded = manager.load_config("corrupted")

        assert loaded == {}

    def test_manager_config_dir_creation(self, tmp_path):
        """Test that config directory is created if it doesn't exist."""
        config_dir = tmp_path / "new" / "nested" / "dir"

        manager = PluginConfigManager(config_dir=config_dir)

        assert config_dir.exists()

    def test_config_get_nested_keys(self):
        """Test getting nested configuration keys."""
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }

        config = PluginConfig("test", config_data)

        # Get nested dict
        db_config = config.get("database")

        assert db_config["host"] == "localhost"
        assert db_config["port"] == 5432

    def test_config_set_nested_keys(self):
        """Test setting nested configuration."""
        config = PluginConfig("test", {})

        nested_data = {
            "host": "localhost",
            "port": 5432
        }

        config.set("database", nested_data)

        assert config.get("database")["host"] == "localhost"


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_full_config_lifecycle(self, tmp_path):
        """Test complete configuration lifecycle."""
        manager = PluginConfigManager(config_dir=tmp_path)

        # Create initial config
        config_data = {
            "version": "1.0.0",
            "settings": {
                "enabled": True,
                "timeout": 30
            }
        }

        # Save
        manager.save_config("test_plugin", config_data)

        # Load
        loaded = manager.load_config("test_plugin")
        assert loaded == config_data

        # Update
        config_data["settings"]["timeout"] = 60
        manager.save_config("test_plugin", config_data)

        # Verify update
        loaded = manager.load_config("test_plugin")
        assert loaded["settings"]["timeout"] == 60

        # Delete
        manager.delete_config("test_plugin")

        # Verify deletion
        loaded = manager.load_config("test_plugin")
        assert loaded == {}

    def test_multiple_plugins_configs(self, tmp_path):
        """Test managing configs for multiple plugins."""
        manager = PluginConfigManager(config_dir=tmp_path)

        # Create configs for multiple plugins
        plugins = {
            "auth_plugin": {"secret": "xyz", "timeout": 300},
            "db_plugin": {"host": "localhost", "port": 5432},
            "cache_plugin": {"ttl": 3600, "max_size": 1000}
        }

        for name, config in plugins.items():
            manager.save_config(name, config)

        # Verify all saved
        configs = manager.list_configs()
        assert len(configs) == 3

        # Verify each can be loaded
        for name, expected_config in plugins.items():
            loaded = manager.load_config(name)
            assert loaded == expected_config
