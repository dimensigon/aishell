"""
LLM Provider Implementations

Supports multiple LLM backends for flexible deployment.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class LocalLLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, model_name: str, model_path: str):
        self.model_name = model_name
        self.model_path = model_path
        self.initialized = False

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

    def cleanup(self):
        """Cleanup resources"""
        self.initialized = False


class OllamaProvider(LocalLLMProvider):
    """Ollama LLM Provider Implementation"""

    def __init__(self, model_name: str = "llama2", model_path: str = "/data0/models",
                 base_url: str = "http://localhost:11434"):
        super().__init__(model_name, model_path)
        self.base_url = base_url
        self.client = None

    def initialize(self) -> bool:
        """Initialize Ollama client"""
        try:
            # In production, this would import ollama
            # For now, we'll use a mock-friendly approach
            try:
                import ollama
                self.client = ollama.Client(host=self.base_url)
                # Test connection
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

    def _create_mock_client(self):
        """Create mock client for testing"""
        class MockOllamaClient:
            def generate(self, model: str, prompt: str, **kwargs):
                return {"response": f"Mock response for: {prompt[:50]}..."}

            def chat(self, model: str, messages: List[Dict[str, str]], **kwargs):
                return {"message": {"content": f"Mock chat response"}}

            def list(self):
                return {"models": []}

        return MockOllamaClient()

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate text using Ollama"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'num_predict': max_tokens,
                    'temperature': temperature
                }
            )
            return response.get('response', '')
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Chat with Ollama"""
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={'num_predict': max_tokens}
            )
            return response.get('message', {}).get('content', '')
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise


class LocalTransformersProvider(LocalLLMProvider):
    """Hugging Face Transformers Provider for local models"""

    def __init__(self, model_name: str, model_path: str = "/data0/models"):
        super().__init__(model_name, model_path)
        self.pipeline = None

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
            result = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True
            )[0]
            return result['generated_text'][len(prompt):]
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Convert chat to prompt and generate"""
        # Convert messages to prompt format
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        prompt += "\nassistant:"
        return self.generate(prompt, max_tokens)
