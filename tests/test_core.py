"""
Tests for AI-Shell Core Application
"""

import pytest
import asyncio
from src.core.ai_shell import AIShellCore


@pytest.mark.asyncio
async def test_core_initialization():
    """Test core application initializes correctly"""
    core = AIShellCore()
    await core.initialize()

    assert core.modules is not None
    assert core.event_bus is not None
    assert core.config is not None
    assert core.initialized is True

    await core.shutdown()


@pytest.mark.asyncio
async def test_module_registration():
    """Test module can be registered"""
    core = AIShellCore()
    await core.initialize()

    class TestModule:
        name = "test_module"

    test_module = TestModule()
    core.register_module(test_module)

    assert "test_module" in core.modules
    assert core.modules["test_module"] is test_module

    await core.shutdown()


@pytest.mark.asyncio
async def test_module_registration_duplicate():
    """Test duplicate module registration raises error"""
    core = AIShellCore()
    await core.initialize()

    class TestModule:
        name = "duplicate"

    core.register_module(TestModule())

    with pytest.raises(KeyError, match="already registered"):
        core.register_module(TestModule())

    await core.shutdown()


@pytest.mark.asyncio
async def test_module_registration_no_name():
    """Test module without name raises error"""
    core = AIShellCore()
    await core.initialize()

    class BadModule:
        pass

    with pytest.raises(ValueError, match="must have 'name' attribute"):
        core.register_module(BadModule())

    await core.shutdown()


@pytest.mark.asyncio
async def test_module_unregistration():
    """Test module can be unregistered"""
    core = AIShellCore()
    await core.initialize()

    class TestModule:
        name = "removable"

    core.register_module(TestModule())
    assert "removable" in core.modules

    core.unregister_module("removable")
    assert "removable" not in core.modules

    await core.shutdown()


@pytest.mark.asyncio
async def test_module_unregistration_not_found():
    """Test unregistering non-existent module raises error"""
    core = AIShellCore()
    await core.initialize()

    with pytest.raises(KeyError, match="not found"):
        core.unregister_module("nonexistent")

    await core.shutdown()


@pytest.mark.asyncio
async def test_get_module():
    """Test retrieving registered module"""
    core = AIShellCore()
    await core.initialize()

    class TestModule:
        name = "getter_test"
        value = 42

    test_module = TestModule()
    core.register_module(test_module)

    retrieved = core.get_module("getter_test")
    assert retrieved is test_module
    assert retrieved.value == 42

    await core.shutdown()


@pytest.mark.asyncio
async def test_get_module_not_found():
    """Test retrieving non-existent module raises error"""
    core = AIShellCore()
    await core.initialize()

    with pytest.raises(KeyError, match="not found"):
        core.get_module("nonexistent")

    await core.shutdown()


@pytest.mark.asyncio
async def test_double_initialization():
    """Test double initialization is handled gracefully"""
    core = AIShellCore()
    await core.initialize()

    # Should not raise error, just log warning
    await core.initialize()

    assert core.initialized is True

    await core.shutdown()


@pytest.mark.asyncio
async def test_shutdown_cleanup():
    """Test shutdown properly cleans up resources"""
    core = AIShellCore()
    await core.initialize()

    class TestModule:
        name = "cleanup_test"

    core.register_module(TestModule())

    await core.shutdown()

    assert core.initialized is False
    assert len(core.modules) == 0
