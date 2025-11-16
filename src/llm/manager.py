"""
Local LLM Manager

Manages LLM operations including intent analysis, anonymization, and embeddings.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re
import json
import hashlib
import logging
from enum import Enum

from src.llm.providers import (
    LocalLLMProvider, OllamaProvider, LocalTransformersProvider,
    OpenAIProvider, AnthropicProvider, MockProvider, LLMProviderFactory
)
from src.llm.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Query intent types"""
    QUERY = "query"
    MUTATION = "mutation"
    SCHEMA = "schema"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


class ModelType(Enum):
    """LLM model types"""
    OLLAMA = "ollama"
    TRANSFORMERS = "transformers"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM manager"""
    provider_type: str = "ollama"
    model_name: str = "llama2"
    model_path: str = "/data0/models"
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class FunctionProviderConfig:
    """Configuration for per-function LLM providers (dual functionality)"""
    provider_type: str
    model_name: str
    api_key: Optional[str] = None


class LocalLLMManager:
    """Manages all LLM operations for AI-Shell with dual provider support"""

    def __init__(self, provider: Optional[LocalLLMProvider] = None,
                 model_path: str = "/data0/models") -> None:
        self.model_path = model_path
        self.provider = provider
        self.embedding_model = EmbeddingModel(model_path=model_path)

        # Per-function providers for dual mode (self-hosted + public APIs)
        self.intent_provider: Optional[LocalLLMProvider] = None
        self.completion_provider: Optional[LocalLLMProvider] = None
        self.anonymizer_provider: Optional[LocalLLMProvider] = None

        # Anonymization mappings
        self.anonymization_map: Dict[str, str] = {}
        self.reverse_map: Dict[str, str] = {}
        self._counter = 0

        self.initialized = False

    def initialize(self, provider_type: str = "ollama", model_name: str = "llama2", api_key: Optional[str] = None) -> bool:
        """
        Initialize LLM manager with specified provider

        Args:
            provider_type: Type of provider (ollama, transformers, openai, anthropic, deepseek, mock)
            model_name: Name of the model to use
            api_key: API key for cloud providers (OpenAI, Anthropic, DeepSeek)

        Returns:
            True if initialization successful
        """
        try:
            # Initialize provider if not provided
            if self.provider is None:
                # Use factory to create provider
                kwargs = {"model_name": model_name}
                if provider_type in ["openai", "anthropic", "deepseek"]:
                    kwargs["api_key"] = api_key
                elif provider_type in ["ollama", "transformers"]:
                    kwargs["model_path"] = self.model_path

                self.provider = LLMProviderFactory.create(provider_type, **kwargs)

            # Initialize provider and embeddings
            provider_success = self.provider.initialize()
            embedding_success = self.embedding_model.initialize()

            self.initialized = provider_success and embedding_success

            if self.initialized:
                logger.info(f"LLM Manager initialized successfully with {provider_type} provider")
            else:
                logger.error("LLM Manager initialization failed")

            return self.initialized
        except Exception as e:
            logger.error(f"Failed to initialize LLM Manager: {e}")
            return False

    def initialize_function_providers(
        self,
        intent_config: Optional[FunctionProviderConfig] = None,
        completion_config: Optional[FunctionProviderConfig] = None,
        anonymizer_config: Optional[FunctionProviderConfig] = None
    ) -> bool:
        """
        Initialize separate providers for each function (dual functionality mode)

        This allows using different providers (self-hosted or public API) for each function.

        Args:
            intent_config: Provider config for intent analysis
            completion_config: Provider config for code completion
            anonymizer_config: Provider config for data anonymization

        Returns:
            True if initialization successful

        Example:
            manager.initialize_function_providers(
                intent_config=FunctionProviderConfig(
                    provider_type="openai",
                    model_name="gpt-3.5-turbo",
                    api_key="sk-..."
                ),
                completion_config=FunctionProviderConfig(
                    provider_type="ollama",
                    model_name="codellama:13b"
                ),
                anonymizer_config=FunctionProviderConfig(
                    provider_type="deepseek",
                    model_name="deepseek-chat",
                    api_key="..."
                )
            )
        """
        try:
            # Initialize intent provider
            if intent_config:
                kwargs = {"model_name": intent_config.model_name}
                if intent_config.provider_type in ["openai", "anthropic", "deepseek"]:
                    kwargs["api_key"] = intent_config.api_key
                elif intent_config.provider_type in ["ollama", "transformers"]:
                    kwargs["model_path"] = self.model_path

                self.intent_provider = LLMProviderFactory.create(
                    intent_config.provider_type, **kwargs
                )
                self.intent_provider.initialize()
                logger.info(f"Intent provider initialized: {intent_config.provider_type}/{intent_config.model_name}")

            # Initialize completion provider
            if completion_config:
                kwargs = {"model_name": completion_config.model_name}
                if completion_config.provider_type in ["openai", "anthropic", "deepseek"]:
                    kwargs["api_key"] = completion_config.api_key
                elif completion_config.provider_type in ["ollama", "transformers"]:
                    kwargs["model_path"] = self.model_path

                self.completion_provider = LLMProviderFactory.create(
                    completion_config.provider_type, **kwargs
                )
                self.completion_provider.initialize()
                logger.info(f"Completion provider initialized: {completion_config.provider_type}/{completion_config.model_name}")

            # Initialize anonymizer provider
            if anonymizer_config:
                kwargs = {"model_name": anonymizer_config.model_name}
                if anonymizer_config.provider_type in ["openai", "anthropic", "deepseek"]:
                    kwargs["api_key"] = anonymizer_config.api_key
                elif anonymizer_config.provider_type in ["ollama", "transformers"]:
                    kwargs["model_path"] = self.model_path

                self.anonymizer_provider = LLMProviderFactory.create(
                    anonymizer_config.provider_type, **kwargs
                )
                self.anonymizer_provider.initialize()
                logger.info(f"Anonymizer provider initialized: {anonymizer_config.provider_type}/{anonymizer_config.model_name}")

            # Initialize embeddings
            embedding_success = self.embedding_model.initialize()

            self.initialized = True
            logger.info("LLM Manager initialized with per-function providers (dual mode)")

            return True
        except Exception as e:
            logger.error(f"Failed to initialize function providers: {e}")
            return False

    def switch_provider(self, provider_type: str, model_name: str, api_key: Optional[str] = None) -> bool:
        """
        Switch to a different LLM provider

        Args:
            provider_type: Type of provider to switch to
            model_name: Name of the model to use
            api_key: API key for cloud providers

        Returns:
            True if switch successful
        """
        try:
            # Cleanup current provider
            if self.provider:
                self.provider.cleanup()

            # Create new provider
            kwargs = {"model_name": model_name}
            if provider_type in ["openai", "anthropic"]:
                kwargs["api_key"] = api_key
            elif provider_type in ["ollama", "transformers"]:
                kwargs["model_path"] = self.model_path

            self.provider = LLMProviderFactory.create(provider_type, **kwargs)

            # Initialize new provider
            success = self.provider.initialize()

            if success:
                logger.info(f"Switched to {provider_type} provider with model {model_name}")

            return success
        except Exception as e:
            logger.error(f"Failed to switch provider: {e}")
            return False

    def list_providers(self) -> List[str]:
        """List available LLM providers"""
        return LLMProviderFactory.list_providers()

    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze the intent of a database query

        Args:
            query: SQL query or natural language question

        Returns:
            Dict with intent type, confidence, and metadata
        """
        if not self.initialized:
            raise RuntimeError("LLM Manager not initialized")

        # Simple rule-based intent detection (can be enhanced with LLM)
        query_lower = query.lower().strip()

        # Determine intent type
        intent_type = IntentType.UNKNOWN
        confidence = 0.0
        metadata = {}

        # Check for performance queries first (more specific)
        if any(keyword in query_lower for keyword in ['create index', 'drop index', 'optimize', 'analyze']):
            intent_type = IntentType.PERFORMANCE
            confidence = 0.9
            metadata['operation'] = 'optimization'
        elif any(keyword in query_lower for keyword in ['select', 'show', 'describe', 'explain']):
            intent_type = IntentType.QUERY
            confidence = 0.9
            metadata['operation'] = 'read'
        elif any(keyword in query_lower for keyword in ['insert', 'update', 'delete', 'create', 'drop', 'alter']):
            intent_type = IntentType.MUTATION
            confidence = 0.9
            metadata['operation'] = 'write'
        elif any(keyword in query_lower for keyword in ['schema', 'structure', 'tables', 'columns']):
            intent_type = IntentType.SCHEMA
            confidence = 0.85
            metadata['operation'] = 'introspection'

        # Use LLM for complex queries
        if confidence < 0.8:
            intent_type, confidence, metadata = self._llm_intent_analysis(query)

        return {
            'intent': intent_type.value,
            'confidence': confidence,
            'metadata': metadata,
            'original_query': query
        }

    def _llm_intent_analysis(self, query: str) -> Tuple[IntentType, float, Dict[str, Any]]:
        """Use LLM to analyze complex query intent"""
        prompt = f"""Analyze this database query and determine its intent.

Query: {query}

Respond with JSON in this format:
{{
    "intent": "query|mutation|schema|performance|unknown",
    "confidence": 0.0-1.0,
    "metadata": {{"operation": "...", "details": "..."}}
}}"""

        try:
            # Use intent-specific provider if available, otherwise use default
            provider = self.intent_provider if self.intent_provider else self.provider

            response = provider.generate(prompt, max_tokens=200, temperature=0.3)

            # Parse JSON response
            result = json.loads(response)
            intent_type = IntentType(result.get('intent', 'unknown'))
            confidence = float(result.get('confidence', 0.5))
            metadata = result.get('metadata', {})

            return intent_type, confidence, metadata
        except Exception as e:
            logger.error(f"LLM intent analysis failed: {e}")
            return IntentType.UNKNOWN, 0.5, {}

    def anonymize_query(self, query: str) -> Tuple[str, Dict[str, str]]:
        """
        Pseudo-anonymize sensitive data in query

        Args:
            query: Original SQL query

        Returns:
            Tuple of (anonymized_query, mapping_dict)
        """
        anonymized = query
        mapping = {}

        # Patterns to anonymize
        patterns = [
            (r"'([^']*@[^']*)'", 'EMAIL'),  # Email addresses
            (r"'(\d{3}-\d{2}-\d{4})'", 'SSN'),  # SSN
            (r"'([A-Z][a-z]+ [A-Z][a-z]+)'", 'NAME'),  # Names
            (r"'(\d{4}-\d{4}-\d{4}-\d{4})'", 'CARD'),  # Card numbers
            (r"'(\d{10,})'", 'PHONE'),  # Phone numbers
        ]

        for pattern, data_type in patterns:
            matches = re.finditer(pattern, anonymized)
            for match in matches:
                original = match.group(1)
                placeholder = self._get_placeholder(original, data_type)

                # Store mapping
                mapping[placeholder] = original
                self.anonymization_map[placeholder] = original
                self.reverse_map[original] = placeholder

                # Replace in query
                anonymized = anonymized.replace(f"'{original}'", f"'{placeholder}'")

        return anonymized, mapping

    def deanonymize_result(self, result: str, mapping: Optional[Dict[str, str]] = None) -> str:
        """
        Restore original values from anonymized result

        Args:
            result: Anonymized result
            mapping: Optional mapping dict (uses stored map if not provided)

        Returns:
            De-anonymized result
        """
        deanonymized = result

        # Use provided mapping or stored mapping
        use_mapping = mapping if mapping is not None else self.anonymization_map

        for placeholder, original in use_mapping.items():
            deanonymized = deanonymized.replace(placeholder, original)

        return deanonymized

    def _get_placeholder(self, value: str, data_type: str) -> str:
        """Generate consistent placeholder for value"""
        # Use hash for consistency
        hash_value = hashlib.md5(value.encode()).hexdigest()[:8]
        return f"{data_type}_{hash_value}"

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.initialized:
            raise RuntimeError("LLM Manager not initialized")

        embeddings = self.embedding_model.encode(texts)
        return embeddings.tolist()

    def find_similar_queries(self, query: str, query_history: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar queries from history

        Args:
            query: Current query
            query_history: List of historical queries
            top_k: Number of similar queries to return

        Returns:
            List of (query, similarity_score) tuples
        """
        if not self.initialized:
            raise RuntimeError("LLM Manager not initialized")

        return self.embedding_model.find_most_similar(query, query_history, top_k)

    def explain_query(self, query: str, context: Optional[str] = None) -> str:
        """
        Generate natural language explanation of query (uses completion provider)

        Args:
            query: SQL query to explain
            context: Optional context about database schema

        Returns:
            Natural language explanation
        """
        if not self.initialized:
            raise RuntimeError("LLM Manager not initialized")

        prompt = f"""Explain this SQL query in simple terms:

Query: {query}

{f'Database Context: {context}' if context else ''}

Provide a clear, concise explanation of what this query does."""

        try:
            # Use completion provider if available, otherwise use default
            provider = self.completion_provider if self.completion_provider else self.provider

            explanation = provider.generate(prompt, max_tokens=300, temperature=0.5)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Query explanation failed: {e}")
            return "Unable to generate explanation."

    def suggest_optimization(self, query: str, execution_plan: Optional[str] = None) -> List[str]:
        """
        Suggest query optimizations (uses completion provider)

        Args:
            query: SQL query to optimize
            execution_plan: Optional execution plan

        Returns:
            List of optimization suggestions
        """
        if not self.initialized:
            raise RuntimeError("LLM Manager not initialized")

        prompt = f"""Analyze this SQL query and suggest optimizations:

Query: {query}

{f'Execution Plan: {execution_plan}' if execution_plan else ''}

Provide 3-5 specific optimization suggestions. Format as a JSON array of strings."""

        try:
            # Use completion provider if available, otherwise use default
            provider = self.completion_provider if self.completion_provider else self.provider

            response = provider.generate(prompt, max_tokens=500, temperature=0.4)

            # Try to parse as JSON
            try:
                suggestions = json.loads(response)
                if isinstance(suggestions, list):
                    return suggestions
            except:
                pass

            # Fallback: split by newlines
            suggestions = [s.strip() for s in response.split('\n') if s.strip() and not s.strip().startswith('[')]
            return suggestions[:5]
        except Exception as e:
            logger.error(f"Optimization suggestion failed: {e}")
            return []

    def cleanup(self):
        """Cleanup resources"""
        if self.provider:
            self.provider.cleanup()
        if self.embedding_model:
            self.embedding_model.cleanup()

        self.anonymization_map.clear()
        self.reverse_map.clear()
        self.initialized = False

        logger.info("LLM Manager cleaned up")


# Alias for backward compatibility with tests
LLMManager = LocalLLMManager
