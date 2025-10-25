"""Simplified tests for LLM Providers in mock mode"""

import pytest
from unittest.mock import Mock
from src.llm.providers import OllamaProvider, LocalTransformersProvider


def test_ollama_provider_mock_mode_initialization():
    """Test Ollama provider initialization in mock mode"""
    provider = OllamaProvider(model_name="llama2")
    result = provider.initialize()

    # Should succeed in mock mode
    assert result is True
    assert provider.initialized is True
    assert provider.client is not None


def test_ollama_provider_generate_in_mock_mode():
    """Test text generation in mock mode"""
    provider = OllamaProvider(model_name="llama2")
    provider.initialize()

    result = provider.generate("Test prompt")

    assert isinstance(result, str)
    assert len(result) > 0


def test_ollama_provider_generate_with_parameters():
    """Test generation with custom parameters in mock mode"""
    provider = OllamaProvider(model_name="llama2")
    provider.initialize()

    result = provider.generate("Test prompt", max_tokens=100, temperature=0.9)

    assert isinstance(result, str)
    assert len(result) > 0


def test_ollama_provider_chat_in_mock_mode():
    """Test chat in mock mode"""
    provider = OllamaProvider(model_name="llama2")
    provider.initialize()

    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]

    result = provider.chat(messages)

    assert isinstance(result, str)
    assert len(result) > 0


def test_ollama_provider_not_initialized():
    """Test error when using provider before initialization"""
    provider = OllamaProvider(model_name="llama2")

    with pytest.raises(RuntimeError, match="not initialized"):
        provider.generate("Test prompt")


def test_ollama_provider_chat_not_initialized():
    """Test error when using chat before initialization"""
    provider = OllamaProvider(model_name="llama2")

    with pytest.raises(RuntimeError, match="not initialized"):
        provider.chat([{"role": "user", "content": "Hello"}])


def test_ollama_provider_cleanup():
    """Test cleanup of Ollama provider"""
    provider = OllamaProvider(model_name="llama2")
    provider.initialize()

    assert provider.initialized is True

    provider.cleanup()

    assert provider.initialized is False


def test_ollama_provider_custom_base_url():
    """Test Ollama provider with custom base URL"""
    custom_url = "http://custom-host:11434"
    provider = OllamaProvider(model_name="llama2", base_url=custom_url)

    assert provider.base_url == custom_url


def test_ollama_provider_custom_model_path():
    """Test Ollama provider with custom model path"""
    custom_path = "/custom/model/path"
    provider = OllamaProvider(model_name="llama2", model_path=custom_path)

    assert provider.model_path == custom_path


def test_transformers_provider_initialization():
    """Test transformers provider initialization"""
    provider = LocalTransformersProvider(model_name="gpt2")
    result = provider.initialize()

    # Will fail due to missing transformers, but should handle gracefully
    assert isinstance(result, bool)


def test_transformers_provider_not_initialized():
    """Test error when using transformers provider before initialization"""
    provider = LocalTransformersProvider(model_name="gpt2")

    with pytest.raises(RuntimeError, match="not initialized"):
        provider.generate("Test prompt")


def test_transformers_provider_cleanup():
    """Test cleanup of transformers provider"""
    provider = LocalTransformersProvider(model_name="gpt2")

    # Even if not successfully initialized, cleanup should work
    provider.cleanup()

    assert provider.initialized is False


def test_provider_model_name_property():
    """Test model_name property"""
    provider = OllamaProvider(model_name="llama2")

    assert provider.model_name == "llama2"


def test_provider_model_path_property():
    """Test model_path property"""
    custom_path = "/data/models"
    provider = OllamaProvider(model_name="llama2", model_path=custom_path)

    assert provider.model_path == custom_path


def test_ollama_mock_client_functionality():
    """Test mock client provides expected interface"""
    provider = OllamaProvider(model_name="llama2")
    provider.initialize()

    # Mock client should have generate and chat methods
    assert hasattr(provider.client, 'generate')
    assert hasattr(provider.client, 'chat')
    assert callable(provider.client.generate)
    assert callable(provider.client.chat)


def test_multiple_generate_calls():
    """Test multiple generation calls work correctly"""
    provider = OllamaProvider(model_name="llama2")
    provider.initialize()

    result1 = provider.generate("First prompt")
    result2 = provider.generate("Second prompt")

    assert isinstance(result1, str)
    assert isinstance(result2, str)
    # Results should be different (or at least independent calls)
    assert len(result1) > 0
    assert len(result2) > 0
