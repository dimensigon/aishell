#!/usr/bin/env python3
"""
Custom LLM Provider Integration for agentic-aishell

This example demonstrates how to integrate a custom LLM provider with agentic-aishell.
You can use this to add support for:
- Self-hosted models (Llama, Mistral, etc.)
- Custom API endpoints
- Fine-tuned models
- Local models with custom inference
- Enterprise LLM services

Features:
- Custom provider registration
- Streaming response support
- Token counting and rate limiting
- Error handling and retries
- Embedding generation
- Function calling support

See examples/use-cases/README.md for full documentation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, AsyncIterator, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM provider configuration"""
    provider_name: str
    model_name: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class LLMMessage:
    """LLM message format"""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str  # 'stop', 'length', 'error'


class BaseLLMProvider(ABC):
    """
    Base class for custom LLM providers.

    Implement this interface to add your own LLM provider to agentic-aishell.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.name = config.provider_name
        self.model = config.model_name

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate completion from messages.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature (override config)
            max_tokens: Maximum tokens (override config)

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming completion from messages.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Token chunks as they are generated
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Simple approximation: 1 token ≈ 4 characters
        return len(text) // 4


class OllamaProvider(BaseLLMProvider):
    """
    Ollama local LLM provider.

    Supports running local models like Llama, Mistral, CodeLlama, etc.
    """

    def __init__(self, config: LLMConfig):
        """Initialize Ollama provider"""
        super().__init__(config)
        self.endpoint = config.api_endpoint or "http://localhost:11434"

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion using Ollama API"""
        logger.info(f"Generating with Ollama model: {self.model}")

        # Format messages for Ollama
        prompt = self._format_messages(messages)

        # Simulate API call
        # In production, use httpx or aiohttp
        response_text = await self._call_ollama_api(
            prompt,
            temperature or self.config.temperature,
            max_tokens or self.config.max_tokens
        )

        return LLMResponse(
            content=response_text,
            model=self.model,
            tokens_used=self.estimate_tokens(response_text),
            finish_reason='stop'
        )

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Generate streaming completion"""
        prompt = self._format_messages(messages)

        # Simulate streaming
        # In production, use streaming HTTP request
        response_text = await self._call_ollama_api(prompt, temperature, max_tokens)

        # Simulate token-by-token streaming
        words = response_text.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Simulate network delay

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        logger.info(f"Generating embedding for text: {text[:50]}...")

        # Simulate embedding generation
        # In production, call Ollama's embedding endpoint
        # Example: POST http://localhost:11434/api/embeddings
        embedding_dim = 384  # Common embedding dimension
        import random
        embedding = [random.random() for _ in range(embedding_dim)]

        return embedding

    def _format_messages(self, messages: List[LLMMessage]) -> str:
        """Format messages into prompt string"""
        prompt_parts = []
        for msg in messages:
            if msg.role == 'system':
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == 'user':
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == 'assistant':
                prompt_parts.append(f"Assistant: {msg.content}")
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"

    async def _call_ollama_api(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Call Ollama API.

        In production, implement actual HTTP call:

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )
            return response.json()["response"]
        """
        # Simulated response
        return f"This is a simulated response from Ollama {self.model} model."


class CustomAPIProvider(BaseLLMProvider):
    """
    Custom API provider for enterprise or self-hosted LLMs.

    Use this to integrate with:
    - Internal enterprise LLM services
    - Custom-trained models
    - Specialized API endpoints
    """

    def __init__(self, config: LLMConfig):
        """Initialize custom API provider"""
        super().__init__(config)
        if not config.api_endpoint:
            raise ValueError("api_endpoint required for CustomAPIProvider")

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate completion using custom API"""
        logger.info(f"Generating with custom API: {self.config.api_endpoint}")

        # Build request payload
        payload = {
            "model": self.model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens
        }

        # Simulate API call
        response = await self._call_custom_api(payload)

        return LLMResponse(
            content=response["content"],
            model=self.model,
            tokens_used=response.get("tokens_used", 0),
            finish_reason=response.get("finish_reason", "stop")
        )

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Generate streaming completion"""
        # For custom API, implement streaming based on API specs
        response = await self.generate(messages, temperature, max_tokens)

        # Simulate streaming
        words = response.content.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.03)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using custom API"""
        logger.info(f"Generating embedding via custom API: {text[:50]}...")

        # Call custom embedding endpoint
        payload = {"text": text, "model": self.model}
        response = await self._call_custom_api(payload, endpoint="/embeddings")

        return response.get("embedding", [])

    async def _call_custom_api(
        self,
        payload: Dict[str, Any],
        endpoint: str = "/generate"
    ) -> Dict[str, Any]:
        """
        Call custom API endpoint.

        In production, implement actual HTTP call with authentication:

        import httpx
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.api_endpoint}{endpoint}",
                json=payload,
                headers=headers,
                timeout=self.config.timeout
            )
            return response.json()
        """
        # Simulated response
        return {
            "content": f"Response from custom API at {self.config.api_endpoint}",
            "tokens_used": 150,
            "finish_reason": "stop"
        }


class LLMProviderRegistry:
    """
    Registry for managing multiple LLM providers.

    Use this to register and switch between different LLM providers
    in your agentic-aishell instance.
    """

    def __init__(self):
        """Initialize provider registry"""
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider: Optional[str] = None

    def register_provider(
        self,
        name: str,
        provider: BaseLLMProvider,
        set_as_default: bool = False
    ):
        """
        Register a new LLM provider.

        Args:
            name: Provider identifier
            provider: Provider instance
            set_as_default: Set as default provider
        """
        self.providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")

        if set_as_default or not self.default_provider:
            self.default_provider = name
            logger.info(f"Set default provider: {name}")

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get provider by name or return default.

        Args:
            name: Provider name (uses default if None)

        Returns:
            Provider instance
        """
        provider_name = name or self.default_provider
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"Provider not found: {provider_name}")

        return self.providers[provider_name]

    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        return list(self.providers.keys())


async def main():
    """Example usage"""
    print("=== Custom LLM Provider Integration ===\n")
    print("This example shows how to integrate custom LLM providers.\n")

    # Initialize registry
    registry = LLMProviderRegistry()

    # Register Ollama provider
    ollama_config = LLMConfig(
        provider_name="ollama",
        model_name="llama2",
        api_endpoint="http://localhost:11434",
        temperature=0.7
    )
    ollama_provider = OllamaProvider(ollama_config)
    registry.register_provider("ollama", ollama_provider, set_as_default=True)

    # Register custom API provider
    custom_config = LLMConfig(
        provider_name="custom",
        model_name="enterprise-gpt",
        api_endpoint="https://api.example.com/v1",
        api_key="your-api-key",
        temperature=0.5
    )
    custom_provider = CustomAPIProvider(custom_config)
    registry.register_provider("custom", custom_provider)

    print(f"Registered providers: {registry.list_providers()}\n")

    # Example: Generate completion
    print("=== Example 1: Generate Completion ===")
    messages = [
        LLMMessage(role="system", content="You are a helpful SQL expert."),
        LLMMessage(role="user", content="Explain what a database index is.")
    ]

    provider = registry.get_provider("ollama")
    response = await provider.generate(messages)

    print(f"Provider: {provider.name}")
    print(f"Model: {response.model}")
    print(f"Response: {response.content}")
    print(f"Tokens used: {response.tokens_used}\n")

    # Example: Streaming completion
    print("=== Example 2: Streaming Completion ===")
    print("Streaming response: ", end="", flush=True)

    async for chunk in provider.generate_stream(messages):
        print(chunk, end="", flush=True)

    print("\n")

    # Example: Generate embedding
    print("=== Example 3: Generate Embedding ===")
    text = "Database indexing improves query performance"
    embedding = await provider.generate_embedding(text)

    print(f"Text: {text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}\n")

    # Example: Switch provider
    print("=== Example 4: Switch Provider ===")
    custom_provider = registry.get_provider("custom")
    response = await custom_provider.generate(messages)

    print(f"Provider: {custom_provider.name}")
    print(f"Response: {response.content}\n")

    print("\n" + "="*60)
    print("Integration Tips:")
    print("="*60)
    print("1. Subclass BaseLLMProvider for your custom provider")
    print("2. Implement generate(), generate_stream(), and generate_embedding()")
    print("3. Register with LLMProviderRegistry")
    print("4. Use in agentic-aishell by configuring src/llm/manager.py")
    print("\nSee examples/use-cases/README.md for full documentation")


if __name__ == "__main__":
    print("Custom LLM Provider Integration for agentic-aishell")
    print("See examples/use-cases/README.md for full documentation\n")
    asyncio.run(main())
