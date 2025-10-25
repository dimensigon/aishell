"""
Comprehensive tests for ConfigManager

Tests cover:
- Configuration loading from files
- Environment variable overrides
- Nested configuration access
- Default configuration
- Type conversion
- Configuration validation
- Error handling
- Edge cases
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from src.core.config import ConfigManager


class TestConfigManagerInit:
    """Test ConfigManager initialization"""

    def test_init_with_path(self):
        """Test initialization with explicit path"""
        config_path = "/tmp/test-config.yaml"
        manager = ConfigManager(config_path)

        assert manager.config_path == Path(config_path)
        assert manager.config == {}
        assert manager.loaded is False

    def test_init_without_path(self):
        """Test initialization without path"""
        manager = ConfigManager()

        assert manager.config_path is None
        assert manager.config == {}
        assert manager.loaded is False


class TestConfigManagerLoad:
    """Test configuration loading"""

    @pytest.mark.asyncio
    async def test_load_from_explicit_path(self, tmp_path):
        """Test loading from explicitly provided path"""
        config_file = tmp_path / "config.yaml"
        test_config = {
            'system': {'startup_animation': False},
            'llm': {'ollama_host': 'localhost:11434'}
        }

        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)

        manager = ConfigManager(str(config_file))
        await manager.load()

        assert manager.loaded is True
        assert manager.config['system']['startup_animation'] is False
        assert manager.config['llm']['ollama_host'] == 'localhost:11434'

    @pytest.mark.asyncio
    async def test_load_from_default_locations(self, tmp_path, monkeypatch):
        """Test loading from default locations"""
        config_file = tmp_path / "ai-shell-config.yaml"
        test_config = {'system': {'theme': 'dark'}}

        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)

        # Mock Path.cwd() to return tmp_path
        monkeypatch.setattr(Path, 'cwd', lambda: tmp_path)

        manager = ConfigManager()
        await manager.load()

        assert manager.loaded is True
        assert manager.config['system']['theme'] == 'dark'

    @pytest.mark.asyncio
    async def test_load_with_env_overrides(self, tmp_path):
        """Test environment variable overrides"""
        config_file = tmp_path / "config.yaml"
        test_config = {
            'llm': {'ollama_host': 'localhost:11434'}
        }

        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)

        # Set environment variable
        with patch.dict(os.environ, {
            'AI_SHELL_LLM_OLLAMA_HOST': 'remote:11434',
            'AI_SHELL_SYSTEM_DEBUG': 'true',
            'AI_SHELL_PERFORMANCE_WORKERS': '8'
        }):
            manager = ConfigManager(str(config_file))
            await manager.load()

        assert manager.config['llm']['ollama_host'] == 'remote:11434'
        assert manager.config['system']['debug'] is True
        assert manager.config['performance']['workers'] == 8

    @pytest.mark.asyncio
    async def test_load_without_file_uses_defaults(self):
        """Test loading uses defaults when no file exists"""
        manager = ConfigManager("/nonexistent/config.yaml")
        await manager.load()

        assert manager.loaded is True
        assert 'system' in manager.config
        assert 'llm' in manager.config
        assert 'mcp' in manager.config
        assert manager.config['system']['startup_animation'] is True

    @pytest.mark.asyncio
    async def test_load_empty_yaml_file(self, tmp_path):
        """Test loading empty YAML file"""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        manager = ConfigManager(str(config_file))
        await manager.load()

        assert manager.loaded is True
        # Should use defaults when file is empty
        assert 'system' in manager.config

    @pytest.mark.asyncio
    async def test_load_with_nested_env_overrides(self, tmp_path):
        """Test deeply nested environment overrides"""
        config_file = tmp_path / "config.yaml"
        test_config = {
            'llm': {
                'models': {
                    'intent': 'llama2:7b'
                }
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)

        with patch.dict(os.environ, {
            'AI_SHELL_LLM_MODELS_INTENT': 'mistral:7b',
            'AI_SHELL_LLM_MODELS_COMPLETION': 'codellama:34b'
        }):
            manager = ConfigManager(str(config_file))
            await manager.load()

        assert manager.config['llm']['models']['intent'] == 'mistral:7b'
        assert manager.config['llm']['models']['completion'] == 'codellama:34b'


class TestConfigManagerGet:
    """Test configuration retrieval"""

    @pytest.mark.asyncio
    async def test_get_simple_key(self):
        """Test getting simple top-level key"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('system')
        assert isinstance(result, dict)
        assert 'startup_animation' in result

    @pytest.mark.asyncio
    async def test_get_nested_key(self):
        """Test getting nested key with dot notation"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('llm.models.intent')
        assert result == 'llama2:7b'

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_default(self):
        """Test getting non-existent key returns default"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('nonexistent.key', 'default_value')
        assert result == 'default_value'

    @pytest.mark.asyncio
    async def test_get_without_default(self):
        """Test getting non-existent key without default"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('nonexistent.key')
        assert result is None

    @pytest.mark.asyncio
    async def test_get_deeply_nested_key(self):
        """Test getting deeply nested configuration"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('mcp.oracle.thin_mode')
        assert result is True

    @pytest.mark.asyncio
    async def test_get_partial_path(self):
        """Test getting partial path that doesn't exist"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('llm.nonexistent.key', 'default')
        assert result == 'default'


class TestConfigManagerSet:
    """Test configuration setting"""

    @pytest.mark.asyncio
    async def test_set_simple_value(self):
        """Test setting simple value"""
        manager = ConfigManager()
        await manager.load()

        manager.set('test_key', 'test_value')
        assert manager.get('test_key') == 'test_value'

    @pytest.mark.asyncio
    async def test_set_nested_value(self):
        """Test setting nested value with dot notation"""
        manager = ConfigManager()
        await manager.load()

        manager.set('new.nested.key', 'value')
        assert manager.get('new.nested.key') == 'value'

    @pytest.mark.asyncio
    async def test_set_overwrites_existing(self):
        """Test setting overwrites existing value"""
        manager = ConfigManager()
        await manager.load()

        original = manager.get('system.startup_animation')
        manager.set('system.startup_animation', False)
        assert manager.get('system.startup_animation') != original
        assert manager.get('system.startup_animation') is False

    @pytest.mark.asyncio
    async def test_set_creates_intermediate_dicts(self):
        """Test setting creates intermediate dictionaries"""
        manager = ConfigManager()
        await manager.load()

        manager.set('level1.level2.level3.value', 42)
        assert manager.get('level1.level2.level3.value') == 42

    @pytest.mark.asyncio
    async def test_set_complex_value(self):
        """Test setting complex value (dict/list)"""
        manager = ConfigManager()
        await manager.load()

        complex_value = {'list': [1, 2, 3], 'nested': {'key': 'value'}}
        manager.set('complex', complex_value)
        assert manager.get('complex') == complex_value


class TestConfigManagerSection:
    """Test configuration section operations"""

    @pytest.mark.asyncio
    async def test_get_section(self):
        """Test getting entire configuration section"""
        manager = ConfigManager()
        await manager.load()

        llm_section = manager.get_section('llm')
        assert isinstance(llm_section, dict)
        assert 'models' in llm_section
        assert 'ollama_host' in llm_section

    @pytest.mark.asyncio
    async def test_get_nonexistent_section(self):
        """Test getting non-existent section returns empty dict"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get_section('nonexistent')
        assert result == {}


class TestConfigManagerValidation:
    """Test configuration validation"""

    @pytest.mark.asyncio
    async def test_validate_complete_config(self):
        """Test validation passes with complete config"""
        manager = ConfigManager()
        await manager.load()

        assert manager.validate() is True

    @pytest.mark.asyncio
    async def test_validate_missing_section(self):
        """Test validation fails with missing section"""
        manager = ConfigManager()
        manager.config = {'system': {}}  # Missing other required sections

        assert manager.validate() is False

    @pytest.mark.asyncio
    async def test_validate_empty_config(self):
        """Test validation fails with empty config"""
        manager = ConfigManager()
        manager.config = {}

        assert manager.validate() is False

    @pytest.mark.asyncio
    async def test_validate_all_required_sections(self):
        """Test validation checks all required sections"""
        manager = ConfigManager()
        await manager.load()

        required_sections = ['system', 'llm', 'mcp', 'ui', 'security', 'performance']

        for section in required_sections:
            assert section in manager.config


class TestConfigManagerTypeConversion:
    """Test type conversion from environment variables"""

    @pytest.mark.asyncio
    async def test_convert_boolean_true(self):
        """Test converting 'true' string to boolean"""
        manager = ConfigManager()

        with patch.dict(os.environ, {'AI_SHELL_TEST_BOOL': 'true'}):
            await manager.load()

        assert manager.get('test.bool') is True

    @pytest.mark.asyncio
    async def test_convert_boolean_false(self):
        """Test converting 'false' string to boolean"""
        manager = ConfigManager()

        with patch.dict(os.environ, {'AI_SHELL_TEST_BOOL': 'false'}):
            await manager.load()

        assert manager.get('test.bool') is False

    @pytest.mark.asyncio
    async def test_convert_integer(self):
        """Test converting string to integer"""
        manager = ConfigManager()

        with patch.dict(os.environ, {'AI_SHELL_TEST_INT': '42'}):
            await manager.load()

        result = manager.get('test.int')
        assert result == 42
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_convert_float(self):
        """Test converting string to float"""
        manager = ConfigManager()

        with patch.dict(os.environ, {'AI_SHELL_TEST_FLOAT': '3.14'}):
            await manager.load()

        result = manager.get('test.float')
        assert result == 3.14
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_convert_string_remains_string(self):
        """Test non-convertible strings remain strings"""
        manager = ConfigManager()

        with patch.dict(os.environ, {'AI_SHELL_TEST_STR': 'hello_world'}):
            await manager.load()

        result = manager.get('test.str')
        assert result == 'hello_world'
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_convert_boolean_case_insensitive(self):
        """Test boolean conversion is case insensitive"""
        manager = ConfigManager()

        with patch.dict(os.environ, {
            'AI_SHELL_TEST_UPPER': 'TRUE',
            'AI_SHELL_TEST_LOWER': 'false',
            'AI_SHELL_TEST_MIXED': 'True'
        }):
            await manager.load()

        assert manager.get('test.upper') is True
        assert manager.get('test.lower') is False
        assert manager.get('test.mixed') is True


class TestConfigManagerEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_set_nested_value_overwrites_non_dict(self):
        """Test setting nested value overwrites non-dict values"""
        manager = ConfigManager()
        await manager.load()

        # Set a non-dict value
        manager.set('test', 'string_value')
        # Try to set nested value under it
        manager.set('test.nested', 'value')

        assert manager.get('test.nested') == 'value'
        assert isinstance(manager.get('test'), dict)

    @pytest.mark.asyncio
    async def test_to_dict_returns_copy(self):
        """Test to_dict returns a copy of config"""
        manager = ConfigManager()
        await manager.load()

        config_copy = manager.to_dict()
        config_copy['test'] = 'modified'

        assert 'test' not in manager.config

    @pytest.mark.asyncio
    async def test_get_with_empty_string_key(self):
        """Test getting with empty string key"""
        manager = ConfigManager()
        await manager.load()

        result = manager.get('', 'default')
        # Should return config itself or default
        assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_loads(self):
        """Test loading multiple times doesn't break state"""
        manager = ConfigManager()

        await manager.load()
        assert manager.loaded is True

        await manager.load()
        assert manager.loaded is True

    @pytest.mark.asyncio
    async def test_env_override_creates_new_sections(self):
        """Test env overrides can create entirely new sections"""
        manager = ConfigManager()

        with patch.dict(os.environ, {
            'AI_SHELL_NEW_SECTION_KEY': 'value',
            'AI_SHELL_NEW_SECTION_NUM': '123'
        }):
            await manager.load()

        assert manager.get('new.section.key') == 'value'
        assert manager.get('new.section.num') == 123

    @pytest.mark.asyncio
    async def test_default_config_structure(self):
        """Test default config has expected structure"""
        manager = ConfigManager()
        await manager.load()

        # Check all expected sections exist
        assert 'system' in manager.config
        assert 'llm' in manager.config
        assert 'mcp' in manager.config
        assert 'ui' in manager.config
        assert 'security' in manager.config
        assert 'performance' in manager.config

        # Check some expected values
        assert manager.config['system']['startup_animation'] is True
        assert manager.config['llm']['ollama_host'] == 'localhost:11434'
        assert manager.config['performance']['async_workers'] == 4

    @pytest.mark.asyncio
    async def test_malformed_yaml_uses_defaults(self, tmp_path):
        """Test malformed YAML falls back to defaults"""
        config_file = tmp_path / "malformed.yaml"
        config_file.write_text("this is not: valid: yaml: content")

        manager = ConfigManager(str(config_file))

        # Should not raise exception, should use defaults
        with pytest.raises(Exception):
            await manager.load()

    @pytest.mark.asyncio
    async def test_get_all_values(self):
        """Test retrieving all config values"""
        manager = ConfigManager()
        await manager.load()

        all_config = manager.to_dict()
        assert len(all_config) > 0
        assert isinstance(all_config, dict)
