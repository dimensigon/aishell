"""
AI-Shell Core Module

This module contains the foundational components of the AI-Shell system:
- AIShellCore: Main application orchestrator
- Event bus for inter-module communication
- Configuration management
"""

from .ai_shell import AIShellCore
from .event_bus import AsyncEventBus, Event
from .config import ConfigManager

__all__ = ['AIShellCore', 'AsyncEventBus', 'Event', 'ConfigManager']
