"""
Tests for Configuration Management
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.core.config import ConfigManager


@pytest.mark.asyncio
async def test_load_yaml_config():
    """Test YAML configuration loading"""
    config_content = """
system:
  startup_animation: true
llm:
  models:
    intent: "llama2:7b"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigManager(config_path)
        await config.load()

        assert config.get('system.startup_animation') == True
        assert config.get('llm.models.intent') == "llama2:7b"
    finally:
        os.unlink(config_path)


@pytest.mark.asyncio
async def test_env_variable_override():
    """Test environment variables override config"""
    config_content = """
llm:
  models:
    intent: "llama2:7b"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        # Set environment override
        os.environ['AI_SHELL_LLM_MODELS_INTENT'] = 'mistral:7b'

        config = ConfigManager(config_path)
        await config.load()

        assert config.get('llm.models.intent') == 'mistral:7b'

        # Cleanup
        del os.environ['AI_SHELL_LLM_MODELS_INTENT']
    finally:
        os.unlink(config_path)


@pytest.mark.asyncio
async def test_default_config():
    """Test default configuration when no file found"""
    config = ConfigManager('/nonexistent/path/config.yaml')
    await config.load()

    # Should have default values
    assert config.get('system.startup_animation') is not None
    assert config.get('llm.ollama_host') is not None
    assert config.get('ui.framework') is not None


@pytest.mark.asyncio
async def test_nested_get():
    """Test getting nested configuration values"""
    config_content = """
database:
  oracle:
    host: localhost
    port: 1521
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigManager(config_path)
        await config.load()

        assert config.get('database.oracle.host') == 'localhost'
        assert config.get('database.oracle.port') == 1521
    finally:
        os.unlink(config_path)


@pytest.mark.asyncio
async def test_get_with_default():
    """Test getting non-existent key returns default"""
    config = ConfigManager()
    await config.load()

    value = config.get('nonexistent.key', 'default_value')
    assert value == 'default_value'


@pytest.mark.asyncio
async def test_set_config_value():
    """Test setting configuration values"""
    config = ConfigManager()
    await config.load()

    config.set('custom.setting', 'test_value')
    assert config.get('custom.setting') == 'test_value'


@pytest.mark.asyncio
async def test_get_section():
    """Test getting entire configuration section"""
    config_content = """
llm:
  models:
    intent: "llama2:7b"
    completion: "codellama:13b"
  ollama_host: "localhost:11434"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigManager(config_path)
        await config.load()

        llm_section = config.get_section('llm')
        assert 'models' in llm_section
        assert llm_section['ollama_host'] == "localhost:11434"
    finally:
        os.unlink(config_path)


@pytest.mark.asyncio
async def test_validation():
    """Test configuration validation"""
    config = ConfigManager()
    await config.load()

    # Default config should be valid
    assert config.validate() == True


@pytest.mark.asyncio
async def test_validation_missing_section():
    """Test validation fails with missing section"""
    config_content = """
system:
  startup_animation: true
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        config = ConfigManager(config_path)
        await config.load()

        # Missing required sections
        assert config.validate() == False
    finally:
        os.unlink(config_path)


@pytest.mark.asyncio
async def test_to_dict():
    """Test getting complete config as dictionary"""
    config = ConfigManager()
    await config.load()

    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert 'system' in config_dict
    assert 'llm' in config_dict


@pytest.mark.asyncio
async def test_boolean_env_override():
    """Test boolean environment variable conversion"""
    # Use a simple key without underscores to test boolean conversion
    os.environ['AI_SHELL_SYSTEM_DEBUG'] = 'true'

    config = ConfigManager()
    await config.load()

    assert config.get('system.debug') == True

    del os.environ['AI_SHELL_SYSTEM_DEBUG']


@pytest.mark.asyncio
async def test_integer_env_override():
    """Test integer environment variable conversion"""
    # Use a simple key to test integer conversion
    os.environ['AI_SHELL_PERFORMANCE_WORKERS'] = '8'

    config = ConfigManager()
    await config.load()

    assert config.get('performance.workers') == 8
    assert isinstance(config.get('performance.workers'), int)

    del os.environ['AI_SHELL_PERFORMANCE_WORKERS']
