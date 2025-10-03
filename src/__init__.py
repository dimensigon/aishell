"""
AI-Shell: AI-powered database management and shell interface.

A production-ready AI assistant for database operations with multi-provider support,
intelligent caching, and comprehensive monitoring.
"""

# Import only existing modules
from . import mcp_clients

__version__ = "1.0.0"

__all__ = [
    'mcp_clients',
]
