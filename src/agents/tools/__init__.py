"""
Agent Tools Module

This module provides the tool registry system and core tool implementations
for agentic AI workflows in AIShell.
"""

from .registry import (
    ToolCategory,
    ToolRiskLevel,
    ToolDefinition,
    ToolRegistry
)


def register_core_tools(registry: ToolRegistry) -> None:
    """
    Register all core tools with the registry

    This function registers essential tools for database operations,
    backups, migrations, and optimizations. Additional tools can be
    registered by importing specific tool modules.

    Args:
        registry: ToolRegistry instance to populate

    Example:
        >>> registry = ToolRegistry()
        >>> register_core_tools(registry)
        >>> print(f"Registered {len(registry.list_tools())} tools")
    """
    # Import tool implementations
    from .database_tools import register_database_tools
    # from .backup_tools import register_backup_tools
    # from .migration_tools import register_migration_tools
    # from .optimizer_tools import register_optimizer_tools

    # Register tool groups
    register_database_tools(registry)
    # register_backup_tools(registry)
    # register_migration_tools(registry)
    # register_optimizer_tools(registry)


def create_default_registry() -> ToolRegistry:
    """
    Create a ToolRegistry with all core tools registered

    Returns:
        Configured ToolRegistry instance

    Example:
        >>> registry = create_default_registry()
        >>> tools = registry.find_tools(category=ToolCategory.BACKUP)
    """
    registry = ToolRegistry()
    register_core_tools(registry)
    return registry


__all__ = [
    'ToolCategory',
    'ToolRiskLevel',
    'ToolDefinition',
    'ToolRegistry',
    'register_core_tools',
    'create_default_registry'
]
