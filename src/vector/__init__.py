"""Vector database system for AI-Shell intelligent completion."""

from .store import VectorDatabase
from .autocomplete import IntelligentCompleter

__all__ = ['VectorDatabase', 'IntelligentCompleter']
