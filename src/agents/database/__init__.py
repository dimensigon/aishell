"""
Database Agents Module

This module contains specialized agents for database operations including:
- BackupAgent: Automated database backup and restoration
- MigrationAgent: Schema migration management
- OptimizerAgent: Query and database optimization

Each agent extends the BaseAgent class and implements autonomous workflows
for database management tasks with safety controls and approval mechanisms.
"""

from .backup import BackupAgent

__all__ = ['BackupAgent']
