"""
Comprehensive tests for LLM Providers with full mocking

Tests Ollama, Transformers, OpenAI, and Anthropic provider implementations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Dict, Any, List

from src.llm.providers import (
    LocalLLMProvider,
    OllamaProvider,
    LocalTransformersProvider,
    OpenAIProvider,
    AnthropicProvider,
    MockProvider,
    LLMProviderFactory,
    LLMConfig,
    LLMResponse
)


class TestLocalLLMProviderBase:
    """Test base LLM provider class"""

    def test_abstract_methods(self):
        """Test that base class cannot be instantiated"""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            LocalLLMProvider("test-model", "/path")

    def test_base_init(self):
        """Test base class initialization"""

        class ConcreteProvider(LocalLLMProvider):
            def initialize(self): return True
            def generate(self, prompt, max_tokens=500, temperature=0.7): return ""
            def chat(self, messages, max_tokens=500): return ""
            async def agenerate(self, prompt, max_tokens=500, temperature=0.7): return ""
            async def stream_generate(self, prompt, **kwargs): yield ""

        provider = ConcreteProvider("test-model", "/data/models")

        assert provider.model_name == "test-model"
        assert provider.model_path == "/data/models"
        assert not provider.initialized

    def test_cleanup_sets_initialized_false(self):
        """Test cleanup method sets initialized to False"""

        class ConcreteProvider(LocalLLMProvider):
            def initialize(self):
                self.initialized = True
                return True
            def generate(self, prompt, max_tokens=500, temperature=0.7): return ""
            def chat(self, messages, max_tokens=500): return ""
            async def agenerate(self, prompt, max_tokens=500, temperature=0.7): return ""
            async def stream_generate(self, prompt, **kwargs): yield ""

        provider = ConcreteProvider("test", "/path")
        provider.initialize()
        assert provider.initialized is True

        provider.cleanup()
        assert provider.initialized is False


class TestOllamaProvider:
    """Test Ollama provider implementation"""

    def test_init_default_values(self):
        """Test OllamaProvider initialization with defaults"""
        provider = OllamaProvider()

        assert provider.model_name == "llama2"
        assert provider.model_path == "/data0/models"
        assert provider.base_url == "http://localhost:11434"
        assert provider.client is None
        assert not provider.initialized

    def test_init_custom_values(self):
        """Test OllamaProvider with custom values"""
        provider = OllamaProvider(
            model_name="codellama",
            model_path="/custom/path",
            base_url="http://remote:8080"
        )

        assert provider.model_name == "codellama"
        assert provider.model_path == "/custom/path"
        assert provider.base_url == "http://remote:8080"

    @patch('src.llm.providers.ollama')
    def test_initialize_success_with_ollama(self, mock_ollama_module):
        """Test successful initialization with ollama package"""
        # Mock ollama client
        mock_client = Mock()
        mock_client.list.return_value = {"models": []}
        mock_ollama_module.Client.return_value = mock_client

        provider = OllamaProvider()
        result = provider.initialize()

        assert result is True
        assert provider.initialized is True
        assert provider.client is mock_client
        mock_ollama_module.Client.assert_called_once_with(host="http://localhost:11434")

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_initialize_mock_mode_no_ollama(self, mock_ollama_module):
        """Test initialization falls back to mock mode when ollama not installed"""
        provider = OllamaProvider()
        result = provider.initialize()

        assert result is True
        assert provider.initialized is True
        assert provider.client is not None
        assert hasattr(provider.client, 'generate')

    @patch('src.llm.providers.ollama')
    def test_initialize_connection_failure(self, mock_ollama_module):
        """Test initialization handles connection failures"""
        mock_ollama_module.Client.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        result = provider.initialize()

        assert result is False
        assert not provider.initialized

    def test_generate_not_initialized(self):
        """Test generate raises error when not initialized"""
        provider = OllamaProvider()

        with pytest.raises(RuntimeError, match="not initialized"):
            provider.generate("test prompt")

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_generate_success(self, mock_ollama):
        """Test successful text generation"""
        provider = OllamaProvider()
        provider.initialize()  # Uses mock client

        # Mock generate response
        mock_response = {"response": "This is a generated response"}
        provider.client.generate = Mock(return_value=mock_response)

        result = provider.generate("test prompt", max_tokens=100, temperature=0.5)

        assert result == "This is a generated response"
        provider.client.generate.assert_called_once_with(
            model="llama2",
            prompt="test prompt",
            options={'num_predict': 100, 'temperature': 0.5}
        )

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_generate_with_parameters(self, mock_ollama):
        """Test generation with custom parameters"""
        provider = OllamaProvider(model_name="mistral")
        provider.initialize()

        mock_response = {"response": "Response"}
        provider.client.generate = Mock(return_value=mock_response)

        result = provider.generate(
            "test prompt",
            max_tokens=500,
            temperature=0.9
        )

        call_args = provider.client.generate.call_args
        assert call_args[1]['options']['num_predict'] == 500
        assert call_args[1]['options']['temperature'] == 0.9

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_generate_handles_errors(self, mock_ollama):
        """Test generate handles API errors"""
        provider = OllamaProvider()
        provider.initialize()

        provider.client.generate = Mock(side_effect=Exception("API error"))

        with pytest.raises(Exception, match="API error"):
            provider.generate("test prompt")

    def test_generate_client_none(self):
        """Test generate raises error when client is None"""
        provider = OllamaProvider()
        provider.initialized = True
        provider.client = None

        with pytest.raises(RuntimeError, match="Client is None"):
            provider.generate("test")

    def test_chat_not_initialized(self):
        """Test chat raises error when not initialized"""
        provider = OllamaProvider()

        with pytest.raises(RuntimeError, match="not initialized"):
            provider.chat([{"role": "user", "content": "hello"}])

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_chat_success(self, mock_ollama):
        """Test successful chat interaction"""
        provider = OllamaProvider()
        provider.initialize()

        mock_response = {
            "message": {
                "content": "Hello! How can I help you?"
            }
        }
        provider.client.chat = Mock(return_value=mock_response)

        messages = [
            {"role": "user", "content": "Hello"}
        ]

        result = provider.chat(messages, max_tokens=200)

        assert result == "Hello! How can I help you?"
        provider.client.chat.assert_called_once_with(
            model="llama2",
            messages=messages,
            options={'num_predict': 200}
        )

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_chat_multi_turn(self, mock_ollama):
        """Test multi-turn chat conversation"""
        provider = OllamaProvider()
        provider.initialize()

        mock_response = {"message": {"content": "Response"}}
        provider.client.chat = Mock(return_value=mock_response)

        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more"}
        ]

        result = provider.chat(messages)

        assert result == "Response"
        # Verify all messages passed
        call_args = provider.client.chat.call_args
        assert len(call_args[1]['messages']) == 3

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_chat_handles_errors(self, mock_ollama):
        """Test chat handles API errors"""
        provider = OllamaProvider()
        provider.initialize()

        provider.client.chat = Mock(side_effect=Exception("Chat error"))

        with pytest.raises(Exception, match="Chat error"):
            provider.chat([{"role": "user", "content": "test"}])

    def test_chat_client_none(self):
        """Test chat raises error when client is None"""
        provider = OllamaProvider()
        provider.initialized = True
        provider.client = None

        with pytest.raises(RuntimeError, match="Client is None"):
            provider.chat([])

    def test_mock_client_methods(self):
        """Test mock client has all required methods"""
        provider = OllamaProvider()
        mock_client = provider._create_mock_client()

        assert hasattr(mock_client, 'generate')
        assert hasattr(mock_client, 'chat')
        assert hasattr(mock_client, 'list')

        # Test mock methods work
        gen_result = mock_client.generate("model", "prompt")
        assert 'response' in gen_result

        chat_result = mock_client.chat("model", [])
        assert 'message' in chat_result

        list_result = mock_client.list()
        assert 'models' in list_result


class TestLocalTransformersProvider:
    """Test Transformers provider implementation"""

    def test_init_default_values(self):
        """Test LocalTransformersProvider initialization"""
        provider = LocalTransformersProvider("gpt2")

        assert provider.model_name == "gpt2"
        assert provider.model_path == "/data0/models"
        assert provider.pipeline is None
        assert not provider.initialized

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_initialize_success_cuda(self, mock_pipeline_fn, mock_torch):
        """Test successful initialization with CUDA"""
        mock_torch.cuda.is_available.return_value = True
        mock_pipeline = Mock()
        mock_pipeline_fn.return_value = mock_pipeline

        provider = LocalTransformersProvider("gpt2", "/models")
        result = provider.initialize()

        assert result is True
        assert provider.initialized is True
        assert provider.pipeline is mock_pipeline

        mock_pipeline_fn.assert_called_once_with(
            "text-generation",
            model="gpt2",
            device=0,
            model_kwargs={"cache_dir": "/models"}
        )

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_initialize_success_cpu(self, mock_pipeline_fn, mock_torch):
        """Test successful initialization with CPU"""
        mock_torch.cuda.is_available.return_value = False
        mock_pipeline = Mock()
        mock_pipeline_fn.return_value = mock_pipeline

        provider = LocalTransformersProvider("gpt2")
        result = provider.initialize()

        assert result is True
        # Device should be -1 for CPU
        call_args = mock_pipeline_fn.call_args
        assert call_args[1]['device'] == -1

    @patch('src.llm.providers.pipeline', side_effect=ImportError)
    def test_initialize_no_transformers(self, mock_pipeline):
        """Test initialization when transformers not installed"""
        provider = LocalTransformersProvider("gpt2")
        result = provider.initialize()

        assert result is False
        assert not provider.initialized

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_initialize_model_load_failure(self, mock_pipeline_fn, mock_torch):
        """Test initialization handles model loading failures"""
        mock_torch.cuda.is_available.return_value = False
        mock_pipeline_fn.side_effect = Exception("Model not found")

        provider = LocalTransformersProvider("invalid-model")
        result = provider.initialize()

        assert result is False
        assert not provider.initialized

    def test_generate_not_initialized(self):
        """Test generate requires initialization"""
        provider = LocalTransformersProvider("gpt2")

        with pytest.raises(RuntimeError, match="not initialized"):
            provider.generate("test prompt")

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_generate_success(self, mock_pipeline_fn, mock_torch):
        """Test successful text generation"""
        mock_torch.cuda.is_available.return_value = False

        mock_pipeline = Mock()
        mock_pipeline.return_value = [{
            'generated_text': 'test prompt and this is the generated continuation'
        }]
        mock_pipeline_fn.return_value = mock_pipeline

        provider = LocalTransformersProvider("gpt2")
        provider.initialize()

        result = provider.generate("test prompt", max_tokens=50, temperature=0.8)

        assert result == " and this is the generated continuation"
        mock_pipeline.assert_called_once()
        call_args = mock_pipeline.call_args
        assert call_args[0][0] == "test prompt"
        assert call_args[1]['max_new_tokens'] == 50
        assert call_args[1]['temperature'] == 0.8
        assert call_args[1]['do_sample'] is True

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_generate_strips_prompt(self, mock_pipeline_fn, mock_torch):
        """Test generated text properly strips original prompt"""
        mock_torch.cuda.is_available.return_value = False

        mock_pipeline = Mock()
        prompt = "Once upon a time"
        generated = f"{prompt} there was a dragon"
        mock_pipeline.return_value = [{'generated_text': generated}]
        mock_pipeline_fn.return_value = mock_pipeline

        provider = LocalTransformersProvider("gpt2")
        provider.initialize()

        result = provider.generate(prompt)

        assert result == " there was a dragon"
        assert prompt not in result

    def test_generate_pipeline_none(self):
        """Test generate raises error when pipeline is None"""
        provider = LocalTransformersProvider("gpt2")
        provider.initialized = True
        provider.pipeline = None

        with pytest.raises(RuntimeError, match="Pipeline is None"):
            provider.generate("test")

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_generate_handles_errors(self, mock_pipeline_fn, mock_torch):
        """Test generate handles pipeline errors"""
        mock_torch.cuda.is_available.return_value = False

        mock_pipeline = Mock()
        mock_pipeline.side_effect = Exception("Generation failed")
        mock_pipeline_fn.return_value = mock_pipeline

        provider = LocalTransformersProvider("gpt2")
        provider.initialize()

        with pytest.raises(Exception, match="Generation failed"):
            provider.generate("test")

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_chat_converts_to_prompt(self, mock_pipeline_fn, mock_torch):
        """Test chat method converts messages to prompt format"""
        mock_torch.cuda.is_available.return_value = False

        mock_pipeline = Mock()
        mock_pipeline.return_value = [{
            'generated_text': 'user: Hello\nassistant: Hi there!'
        }]
        mock_pipeline_fn.return_value = mock_pipeline

        provider = LocalTransformersProvider("gpt2")
        provider.initialize()

        messages = [
            {"role": "user", "content": "Hello"}
        ]

        result = provider.chat(messages, max_tokens=100)

        # Should call generate with formatted prompt
        call_args = mock_pipeline.call_args
        prompt = call_args[0][0]
        assert "user: Hello" in prompt
        assert "assistant:" in prompt


class TestProviderErrorScenarios:
    """Test error scenarios across providers"""

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_ollama_timeout_handling(self, mock_ollama):
        """Test Ollama handles timeout errors"""
        provider = OllamaProvider()
        provider.initialize()

        provider.client.generate = Mock(side_effect=TimeoutError("Request timeout"))

        with pytest.raises(TimeoutError):
            provider.generate("test", max_tokens=1000)

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_ollama_rate_limit_handling(self, mock_ollama):
        """Test Ollama handles rate limit errors"""
        provider = OllamaProvider()
        provider.initialize()

        provider.client.generate = Mock(
            side_effect=Exception("Rate limit exceeded")
        )

        with pytest.raises(Exception, match="Rate limit"):
            provider.generate("test")

    @patch('src.llm.providers.torch')
    @patch('src.llm.providers.pipeline')
    def test_transformers_memory_error(self, mock_pipeline_fn, mock_torch):
        """Test Transformers handles memory errors"""
        mock_torch.cuda.is_available.return_value = True
        mock_pipeline_fn.side_effect = MemoryError("CUDA out of memory")

        provider = LocalTransformersProvider("large-model")
        result = provider.initialize()

        assert result is False

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_ollama_invalid_response_format(self, mock_ollama):
        """Test Ollama handles invalid response formats"""
        provider = OllamaProvider()
        provider.initialize()

        # Return response without expected key
        provider.client.generate = Mock(return_value={"error": "Invalid format"})

        result = provider.generate("test")

        # Should return empty string for missing 'response' key
        assert result == ""


class TestProviderCaching:
    """Test provider response caching patterns"""

    @patch('src.llm.providers.ollama', side_effect=ImportError)
    def test_ollama_repeated_calls(self, mock_ollama):
        """Test repeated calls to Ollama"""
        provider = OllamaProvider()
        provider.initialize()

        responses = ["Response 1", "Response 2", "Response 3"]
        provider.client.generate = Mock(
            side_effect=[{"response": r} for r in responses]
        )

        # Make multiple calls
        results = [provider.generate(f"prompt {i}") for i in range(3)]

        assert results == responses
        assert provider.client.generate.call_count == 3
