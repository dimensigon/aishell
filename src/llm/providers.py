"""
LLM Provider Implementations

Supports multiple LLM backends for flexible deployment.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass
import os
import json
import logging
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    stream: bool = False
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = None
    raw_response: Dict[str, Any] = None


class LocalLLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, model_name: str, model_path: str) -> None:
        self.model_name = model_name
        self.model_path = model_path
        self.initialized = False
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the LLM model"""
        pass

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Chat-style generation with message history"""
        pass

    @abstractmethod
    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Async generate text from prompt"""
        pass

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from the LLM"""
        pass

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.initialized = False


class OllamaProvider(LocalLLMProvider):
    """Ollama LLM Provider Implementation"""

    def __init__(self, model_name: str = "llama2", model_path: str = "/data0/models",
                 base_url: str = "http://localhost:11434") -> None:
        super().__init__(model_name, model_path)
        self.base_url = base_url
        self.client: Optional[Any] = None

    def initialize(self) -> bool:
        """Initialize Ollama client"""
        try:
            # In production, this would import ollama
            # For now, we'll use a mock-friendly approach
            try:
                import ollama
                self.client = ollama.Client(host=self.base_url)
                # Test connection
                if self.client is not None:
                    self.client.list()
                self.initialized = True
                logger.info(f"Ollama provider initialized with model: {self.model_name}")
                return True
            except ImportError:
                # Mock mode for testing
                logger.warning("Ollama not installed, using mock mode")
                self.client = self._create_mock_client()
                self.initialized = True
                return True
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            return False

    def _create_mock_client(self) -> Any:
        """Create mock client for testing"""
        class MockOllamaClient:
            def generate(self, model: str, prompt: str, **kwargs: Any) -> Dict[str, Any]:
                return {"response": f"Mock response for: {prompt[:50]}..."}

            def chat(self, model: str, messages: List[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
                return {"message": {"content": f"Mock chat response"}}

            def list(self) -> Dict[str, List[Any]]:
                return {"models": []}

        return MockOllamaClient()

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text using Ollama"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        try:
            if self.client is None:
                raise RuntimeError("Client is None")
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': temperature
                }
            )
            return str(response.get('response', ''))
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Chat with Ollama"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        try:
            if self.client is None:
                raise RuntimeError("Client is None")
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={'num_predict': max_tokens}
            )
            return str(response.get('message', {}).get('content', ''))
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise

    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Async generate with Ollama"""
        return self.generate(prompt, max_tokens, temperature)

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from Ollama"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        # Mock streaming for Ollama
        response = self.generate(prompt, kwargs.get('max_tokens', 500))
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.01)


class LocalTransformersProvider(LocalLLMProvider):
    """Hugging Face Transformers Provider for local models"""

    def __init__(self, model_name: str, model_path: str = "/data0/models") -> None:
        super().__init__(model_name, model_path)
        self.pipeline: Optional[Any] = None

    def initialize(self) -> bool:
        """Initialize transformers pipeline"""
        try:
            from transformers import pipeline
            import torch

            device = 0 if torch.cuda.is_available() else -1
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device=device,
                model_kwargs={"cache_dir": self.model_path}
            )
            self.initialized = True
            logger.info(f"Transformers provider initialized: {self.model_name}")
            return True
        except ImportError:
            logger.warning("Transformers not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize transformers: {e}")
            return False

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text using transformers"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        try:
            if self.pipeline is None:
                raise RuntimeError("Pipeline is None")
            result = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True
            )[0]
            return str(result['generated_text'][len(prompt):])
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Convert chat to prompt and generate"""
        # Convert messages to prompt format
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        prompt += "\nassistant:"
        return self.generate(prompt, max_tokens)

    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Async generate with transformers"""
        return self.generate(prompt, max_tokens, temperature)

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from transformers"""
        response = self.generate(prompt, kwargs.get('max_tokens', 500))
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.01)


class OpenAIProvider(LocalLLMProvider):
    """OpenAI API provider with full API support"""

    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None) -> None:
        super().__init__(model_name, "")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

    def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            if not self.api_key:
                logger.warning("No OpenAI API key found. Set OPENAI_API_KEY env var.")
                return False
            self.initialized = True
            logger.info(f"OpenAI provider initialized with model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            return False

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text using OpenAI (synchronous wrapper)"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        # Run async method synchronously
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, use the existing loop
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                logger.warning("nest_asyncio not available, using direct async call")

        return loop.run_until_complete(self.agenerate(prompt, max_tokens, temperature))

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Chat using OpenAI"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass

        return loop.run_until_complete(self._achat(messages, max_tokens))

    async def _achat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Async chat implementation"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens
        }

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI API error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Async generate with OpenAI"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI API error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"OpenAI async generation error: {e}")
            raise

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from OpenAI"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 500),
            "stream": True
        }

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenAI stream error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"OpenAI stream generation error: {e}")
            raise


class AnthropicProvider(LocalLLMProvider):
    """Anthropic Claude API provider with full API support"""

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None) -> None:
        super().__init__(model_name, "")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        self.api_version = "2023-06-01"

    def initialize(self) -> bool:
        """Initialize Anthropic client"""
        try:
            if not self.api_key:
                logger.warning("No Anthropic API key found. Set ANTHROPIC_API_KEY env var.")
                return False
            self.initialized = True
            logger.info(f"Anthropic provider initialized with model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            return False

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text using Anthropic (synchronous wrapper)"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass

        return loop.run_until_complete(self.agenerate(prompt, max_tokens, temperature))

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Chat using Anthropic"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass

        return loop.run_until_complete(self._achat(messages, max_tokens))

    async def _achat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Async chat implementation"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens
        }

        try:
            async with self.session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["content"][0]["text"]
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Anthropic API error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            raise

    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Async generate with Anthropic"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            async with self.session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["content"][0]["text"]
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Anthropic API error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"Anthropic async generation error: {e}")
            raise

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from Anthropic"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get('max_tokens', 500),
            "temperature": kwargs.get('temperature', 0.7),
            "stream": True
        }

        try:
            async with self.session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if data.get('type') == 'content_block_delta':
                                    delta = data.get('delta', {})
                                    if delta.get('type') == 'text_delta':
                                        yield delta.get('text', '')
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Anthropic stream error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"Anthropic stream generation error: {e}")
            raise


class MockProvider(LocalLLMProvider):
    """Mock provider for testing"""

    def __init__(self, model_name: str = "mock-model") -> None:
        super().__init__(model_name, "")

    def initialize(self) -> bool:
        """Initialize mock provider"""
        self.initialized = True
        logger.info("Mock provider initialized")
        return True

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate mock response"""
        return f"Mock response for: {prompt[:50]}..."

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Mock chat response"""
        return f"Mock chat response for {len(messages)} messages"

    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Async mock generate"""
        await asyncio.sleep(0.1)
        return f"Mock async response for: {prompt[:50]}..."

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream mock response"""
        response = f"Mock streaming response for: {prompt[:50]}..."
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.05)


class LLMProviderFactory:
    """Factory for creating LLM providers"""

    PROVIDERS = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "deepseek": DeepSeekProvider,
        "transformers": LocalTransformersProvider,
        "mock": MockProvider
    }

    @classmethod
    def create(cls, provider_type: str, **kwargs) -> LocalLLMProvider:
        """Create an LLM provider based on type"""
        # Import DeepSeek here to avoid circular import
        from src.llm.providers.deepseek import DeepSeekProvider

        # Update providers with DeepSeek
        providers = {
            **cls.PROVIDERS,
            "deepseek": DeepSeekProvider
        }

        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_type}. Available: {', '.join(providers.keys())}")
        return provider_class(**kwargs)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List available providers"""
        providers = list(cls.PROVIDERS.keys())
        if "deepseek" not in providers:
            providers.append("deepseek")
        return providers
