"""
AI Module - Advanced AI-Powered Features for v2.0.0

This module provides AI-enhanced query assistance including:
- Natural language to complex SQL conversion via Claude API
- Query explanation in plain English
- Performance optimization suggestions
- Schema understanding and context awareness
- Query correction and validation
- Learning from query patterns
"""

from src.ai.query_assistant import QueryAssistant, QueryContext, QueryResponse
from src.ai.prompt_templates import PromptTemplates
from src.ai.conversation_manager import ConversationManager

__all__ = [
    'QueryAssistant',
    'QueryContext',
    'QueryResponse',
    'PromptTemplates',
    'ConversationManager'
]

__version__ = '2.0.0'
