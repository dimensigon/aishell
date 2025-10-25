"""
Local LLM Integration Module

Provides LLM-based functionality for AI-Shell including:
- Intent analysis
- Pseudo-anonymization
- Embedding generation
- Multiple LLM provider support
"""

from src.llm.manager import LocalLLMManager
from src.llm.providers import LocalLLMProvider, OllamaProvider
from src.llm.embeddings import EmbeddingModel

__all__ = [
    'LocalLLMManager',
    'LocalLLMProvider',
    'OllamaProvider',
    'EmbeddingModel'
]

__version__ = '1.0.0'
