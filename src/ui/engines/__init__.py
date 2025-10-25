"""UI engines package for AIShell.

This package contains intelligent UI engines for enhanced user experience:
- Context-aware suggestion engine for autocomplete
- Additional engines can be added here
"""

from .context_suggestion import (
    ContextAwareSuggestionEngine,
    SuggestionContext
)

__all__ = [
    'ContextAwareSuggestionEngine',
    'SuggestionContext'
]
