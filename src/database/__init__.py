"""Database module for AI-Shell.

Provides unified interface for database operations with risk analysis,
NLP to SQL conversion, and history management.
"""

from .module import DatabaseModule
from .risk_analyzer import SQLRiskAnalyzer, RiskLevel
from .nlp_to_sql import NLPToSQL
from .history import SQLHistoryManager

__all__ = [
    'DatabaseModule',
    'SQLRiskAnalyzer',
    'RiskLevel',
    'NLPToSQL',
    'SQLHistoryManager',
]
