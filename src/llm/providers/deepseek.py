"""
DeepSeek API Provider Implementation

Supports DeepSeek models via their public API.
API Documentation: https://platform.deepseek.com/api-docs/
"""

from typing import Dict, Any, List, Optional, AsyncIterator
import os
import logging
import aiohttp
import asyncio
import json

from src.llm.providers import LocalLLMProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(LocalLLMProvider):
    """DeepSeek API provider for public cloud models"""

    def __init__(self, model_name: str = "deepseek-chat", api_key: Optional[str] = None) -> None:
        """
        Initialize DeepSeek provider

        Args:
            model_name: DeepSeek model name (deepseek-chat, deepseek-coder)
            api_key: DeepSeek API key (or use DEEPSEEK_API_KEY env var)
        """
        super().__init__(model_name, "")
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None

    def initialize(self) -> bool:
        """Initialize DeepSeek client"""
        try:
            if not self.api_key:
                logger.warning("No DeepSeek API key found. Set DEEPSEEK_API_KEY env var.")
                return False

            self.initialized = True
            logger.info(f"DeepSeek provider initialized with model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek: {e}")
            return False

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate text using DeepSeek (synchronous wrapper)

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            Generated text
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        # Run async method synchronously
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, use the existing loop
            import nest_asyncio
            nest_asyncio.apply()

        return loop.run_until_complete(self.agenerate(prompt, max_tokens, temperature))

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """
        Chat using DeepSeek

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant response
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()

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
            "max_tokens": max_tokens,
            "stream": False
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
                    raise RuntimeError(f"DeepSeek API error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"DeepSeek chat error: {e}")
            raise

    async def agenerate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Async generate text from prompt

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
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
            "max_tokens": max_tokens,
            "stream": False
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
                    raise RuntimeError(f"DeepSeek API error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"DeepSeek async generation error: {e}")
            raise

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Stream response from DeepSeek

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments (max_tokens, temperature)

        Yields:
            Response chunks
        """
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
                    raise RuntimeError(f"DeepSeek stream error ({response.status}): {error_text}")
        except Exception as e:
            logger.error(f"DeepSeek stream generation error: {e}")
            raise

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.session:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.session.close())
            else:
                loop.run_until_complete(self.session.close())
            self.session = None

        super().cleanup()
