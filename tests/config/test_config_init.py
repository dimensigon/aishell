"""Tests for config module initialization."""

import pytest
from src.config import Settings, get_settings


class TestConfigInit:
    """Test config module __init__.py exports."""

    def test_imports_available(self):
        """Test all expected exports are available from config module."""
        from src import config

        assert hasattr(config, 'Settings')
        assert hasattr(config, 'get_settings')

    def test_settings_class_import(self):
        """Test Settings class can be imported from config."""
        assert Settings is not None
        assert callable(Settings)

    def test_get_settings_function_import(self):
        """Test get_settings function can be imported from config."""
        assert get_settings is not None
        assert callable(get_settings)

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        from src import config

        expected_exports = {'Settings', 'get_settings'}
        assert set(config.__all__) == expected_exports

    def test_no_unexpected_exports(self):
        """Test config module doesn't export unexpected items."""
        from src import config

        public_attrs = [attr for attr in dir(config) if not attr.startswith('_')]
        expected = {'Settings', 'get_settings'}

        # Should only have expected exports plus potential test artifacts
        assert expected.issubset(set(public_attrs))

    def test_settings_is_same_class(self):
        """Test Settings from config is same as from settings module."""
        from src.config import Settings as ConfigSettings
        from src.config.settings import Settings as SettingsSettings

        assert ConfigSettings is SettingsSettings

    def test_get_settings_is_same_function(self):
        """Test get_settings from config is same as from settings module."""
        from src.config import get_settings as config_get_settings
        from src.config.settings import get_settings as settings_get_settings

        assert config_get_settings is settings_get_settings

    def test_can_instantiate_settings_from_config(self):
        """Test Settings can be instantiated when imported from config."""
        from src.config import Settings

        settings = Settings()
        assert settings is not None
        assert hasattr(settings, 'db_host')

    def test_can_call_get_settings_from_config(self):
        """Test get_settings works when imported from config."""
        from src.config import get_settings

        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, 'db_host')

    def test_module_docstring(self):
        """Test config module has docstring."""
        from src import config

        assert config.__doc__ is not None
        assert len(config.__doc__) > 0

    def test_settings_attributes_accessible(self):
        """Test Settings attributes accessible from config import."""
        from src.config import Settings

        settings = Settings()
        assert hasattr(settings, 'db_host')
        assert hasattr(settings, 'db_port')
        assert hasattr(settings, 'to_dict')

    def test_multiple_imports_same_reference(self):
        """Test multiple imports reference same classes."""
        from src.config import Settings as Settings1
        from src.config import Settings as Settings2

        assert Settings1 is Settings2

    def test_relative_import_structure(self):
        """Test internal import structure is correct."""
        import src.config as config

        # Should be able to access through module
        assert hasattr(config, 'Settings')
        assert hasattr(config, 'get_settings')

        # And through direct attribute access
        settings = config.Settings()
        assert settings is not None
