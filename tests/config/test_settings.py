"""Comprehensive tests for settings module."""

import pytest
import os
from unittest.mock import patch, MagicMock
from src.config.settings import Settings, get_settings, _settings


class TestSettings:
    """Test Settings dataclass configuration management."""

    def setup_method(self):
        """Reset settings singleton before each test."""
        global _settings
        import src.config.settings
        src.config.settings._settings = None

    def test_settings_default_values(self):
        """Test Settings initializes with correct default values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.db_host == 'localhost'
            assert settings.db_port == 5432
            assert settings.db_name == 'postgres'
            assert settings.db_user == 'postgres'
            assert settings.db_password == ''
            assert settings.openai_api_key == ''
            assert settings.model_name == 'gpt-4'
            assert settings.vector_dimension == 384
            assert settings.max_enrichment_workers == 4
            assert settings.log_level == 'INFO'

    def test_settings_from_environment_variables(self):
        """Test Settings loads values from environment variables."""
        env_vars = {
            'DB_HOST': 'testhost',
            'DB_PORT': '3306',
            'DB_NAME': 'testdb',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'OPENAI_API_KEY': 'sk-test123',
            'MODEL_NAME': 'gpt-3.5-turbo',
            'LOG_LEVEL': 'DEBUG'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.db_host == 'testhost'
            assert settings.db_port == 3306
            assert settings.db_name == 'testdb'
            assert settings.db_user == 'testuser'
            assert settings.db_password == 'testpass'
            assert settings.openai_api_key == 'sk-test123'
            assert settings.model_name == 'gpt-3.5-turbo'
            assert settings.log_level == 'DEBUG'

    def test_settings_partial_environment_override(self):
        """Test Settings uses defaults when environment variables missing."""
        env_vars = {
            'DB_HOST': 'custom-host',
            'MODEL_NAME': 'custom-model'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.db_host == 'custom-host'
            assert settings.model_name == 'custom-model'
            assert settings.db_port == 5432  # Default
            assert settings.db_name == 'postgres'  # Default

    def test_settings_db_port_type_conversion(self):
        """Test DB_PORT environment variable converts to integer."""
        with patch.dict(os.environ, {'DB_PORT': '8080'}, clear=True):
            settings = Settings()
            assert settings.db_port == 8080
            assert isinstance(settings.db_port, int)

    def test_settings_db_port_invalid_conversion(self):
        """Test DB_PORT handles invalid integer conversion."""
        with patch.dict(os.environ, {'DB_PORT': 'invalid'}, clear=True):
            with pytest.raises(ValueError):
                Settings()

    def test_settings_to_dict(self):
        """Test Settings.to_dict() returns correct dictionary representation."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            settings_dict = settings.to_dict()

            assert isinstance(settings_dict, dict)
            assert settings_dict['db_host'] == 'localhost'
            assert settings_dict['db_port'] == 5432
            assert settings_dict['db_name'] == 'postgres'
            assert settings_dict['db_user'] == 'postgres'
            assert settings_dict['vector_dimension'] == 384
            assert settings_dict['max_enrichment_workers'] == 4
            assert settings_dict['log_level'] == 'INFO'
            assert settings_dict['model_name'] == 'gpt-4'

    def test_settings_to_dict_excludes_password(self):
        """Test Settings.to_dict() doesn't include sensitive password field."""
        with patch.dict(os.environ, {'DB_PASSWORD': 'secret'}, clear=True):
            settings = Settings()
            settings_dict = settings.to_dict()

            assert 'db_password' not in settings_dict
            assert 'openai_api_key' not in settings_dict

    def test_settings_immutable_fields(self):
        """Test Settings fields can be modified after creation."""
        settings = Settings()

        # Dataclasses are mutable by default
        settings.db_host = 'modified-host'
        assert settings.db_host == 'modified-host'

        settings.vector_dimension = 512
        assert settings.vector_dimension == 512

    def test_settings_vector_dimension_not_from_env(self):
        """Test vector_dimension is not loaded from environment."""
        with patch.dict(os.environ, {'VECTOR_DIMENSION': '1024'}, clear=True):
            settings = Settings()
            # Should remain default, not from environment
            assert settings.vector_dimension == 384

    def test_settings_max_enrichment_workers_not_from_env(self):
        """Test max_enrichment_workers is not loaded from environment."""
        with patch.dict(os.environ, {'MAX_ENRICHMENT_WORKERS': '8'}, clear=True):
            settings = Settings()
            # Should remain default, not from environment
            assert settings.max_enrichment_workers == 4

    def test_settings_empty_environment_values(self):
        """Test Settings handles empty string environment variables."""
        env_vars = {
            'DB_HOST': '',
            'DB_NAME': '',
            'MODEL_NAME': ''
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.db_host == ''
            assert settings.db_name == ''
            assert settings.model_name == ''

    def test_get_settings_singleton_pattern(self):
        """Test get_settings() returns singleton instance."""
        with patch.dict(os.environ, {}, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()

            assert settings1 is settings2
            assert id(settings1) == id(settings2)

    def test_get_settings_creates_instance_once(self):
        """Test get_settings() creates Settings instance only once."""
        with patch.dict(os.environ, {}, clear=True):
            settings1 = get_settings()
            settings1.db_host = 'modified'

            settings2 = get_settings()
            assert settings2.db_host == 'modified'

    def test_get_settings_thread_safety(self):
        """Test get_settings() behavior with multiple calls."""
        import threading
        results = []

        def get_setting():
            results.append(id(get_settings()))

        with patch.dict(os.environ, {}, clear=True):
            threads = [threading.Thread(target=get_setting) for _ in range(10)]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # All threads should get same instance ID
            assert len(set(results)) == 1

    def test_settings_with_all_environment_variables(self):
        """Test Settings with complete environment configuration."""
        env_vars = {
            'DB_HOST': 'prod-db.example.com',
            'DB_PORT': '5433',
            'DB_NAME': 'production',
            'DB_USER': 'app_user',
            'DB_PASSWORD': 'secure_password',
            'OPENAI_API_KEY': 'sk-prod-key',
            'MODEL_NAME': 'gpt-4-turbo',
            'LOG_LEVEL': 'WARNING'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.db_host == 'prod-db.example.com'
            assert settings.db_port == 5433
            assert settings.db_name == 'production'
            assert settings.db_user == 'app_user'
            assert settings.db_password == 'secure_password'
            assert settings.openai_api_key == 'sk-prod-key'
            assert settings.model_name == 'gpt-4-turbo'
            assert settings.log_level == 'WARNING'

    def test_settings_log_level_case_sensitivity(self):
        """Test LOG_LEVEL environment variable preserves case."""
        test_cases = ['DEBUG', 'debug', 'Info', 'ERROR']

        for log_level in test_cases:
            with patch.dict(os.environ, {'LOG_LEVEL': log_level}, clear=True):
                settings = Settings()
                assert settings.log_level == log_level

    def test_settings_db_port_zero(self):
        """Test DB_PORT handles edge case of zero."""
        with patch.dict(os.environ, {'DB_PORT': '0'}, clear=True):
            settings = Settings()
            assert settings.db_port == 0

    def test_settings_db_port_large_number(self):
        """Test DB_PORT handles large port numbers."""
        with patch.dict(os.environ, {'DB_PORT': '65535'}, clear=True):
            settings = Settings()
            assert settings.db_port == 65535

    def test_settings_special_characters_in_password(self):
        """Test DB_PASSWORD handles special characters."""
        special_password = 'p@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?'

        with patch.dict(os.environ, {'DB_PASSWORD': special_password}, clear=True):
            settings = Settings()
            assert settings.db_password == special_password

    def test_settings_unicode_characters(self):
        """Test Settings handles unicode in environment variables."""
        with patch.dict(os.environ, {'DB_NAME': 'データベース'}, clear=True):
            settings = Settings()
            assert settings.db_name == 'データベース'

    def test_settings_to_dict_matches_fields(self):
        """Test to_dict() includes all expected fields."""
        settings = Settings()
        settings_dict = settings.to_dict()

        expected_keys = {
            'db_host', 'db_port', 'db_name', 'db_user',
            'vector_dimension', 'max_enrichment_workers',
            'log_level', 'model_name'
        }

        assert set(settings_dict.keys()) == expected_keys

    @patch('src.config.settings._settings', None)
    def test_get_settings_after_manual_reset(self):
        """Test get_settings() creates new instance after manual reset."""
        import src.config.settings

        with patch.dict(os.environ, {'DB_HOST': 'host1'}, clear=True):
            settings1 = get_settings()
            assert settings1.db_host == 'host1'

        # Manually reset singleton
        src.config.settings._settings = None

        with patch.dict(os.environ, {'DB_HOST': 'host2'}, clear=True):
            settings2 = get_settings()
            # Should create new instance with new environment
            assert settings2.db_host == 'host2'

    def test_settings_representation(self):
        """Test Settings has meaningful string representation."""
        settings = Settings()
        settings_repr = repr(settings)

        assert 'Settings' in settings_repr
        assert 'db_host' in settings_repr

    def test_settings_equality(self):
        """Test Settings instances with same values are equal."""
        with patch.dict(os.environ, {}, clear=True):
            settings1 = Settings()
            settings2 = Settings()

            # Dataclasses implement __eq__ by default
            assert settings1 == settings2

    def test_settings_different_values_not_equal(self):
        """Test Settings instances with different values are not equal."""
        with patch.dict(os.environ, {}, clear=True):
            settings1 = Settings()

        with patch.dict(os.environ, {'DB_HOST': 'different'}, clear=True):
            settings2 = Settings()

            assert settings1 != settings2
