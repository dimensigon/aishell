"""Database module for AI-Shell.

Provides unified interface for database operations with risk analysis,
NLP to SQL conversion, history management, backup/restore, and migrations.
"""

from .module import DatabaseModule
from .risk_analyzer import SQLRiskAnalyzer, RiskLevel
from .nlp_to_sql import NLPToSQL
from .history import SQLHistoryManager
from .backup import BackupSystem, BackupType, BackupStatus, BackupRotationPolicy
from .restore import RestoreSystem, RestoreStatus
from .migration import MigrationAssistant, MigrationType, MigrationStatus

__all__ = [
    'DatabaseModule',
    'SQLRiskAnalyzer',
    'RiskLevel',
    'NLPToSQL',
    'SQLHistoryManager',
    'BackupSystem',
    'BackupType',
    'BackupStatus',
    'BackupRotationPolicy',
    'RestoreSystem',
    'RestoreStatus',
    'MigrationAssistant',
    'MigrationType',
    'MigrationStatus',
]
