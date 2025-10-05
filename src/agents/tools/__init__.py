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


def register_migration_tools(registry: ToolRegistry) -> None:
    """
    Register migration tools with the registry

    Args:
        registry: ToolRegistry instance to populate
    """
    from .migration_tools import MIGRATION_TOOLS

    for tool_def in MIGRATION_TOOLS:
        registry.register_tool(ToolDefinition(
            name=tool_def['name'],
            description=f"Database migration tool: {tool_def['name']}",
            category=ToolCategory.MIGRATION,
            risk_level=ToolRiskLevel.HIGH,
            required_capabilities=["database_write", "schema_modify"],
            parameters_schema=tool_def['schema'],
            returns_schema={"type": "object"},
            implementation=tool_def['func'],
            requires_approval=True,
            max_execution_time=300
        ))


def register_optimizer_tools(registry: ToolRegistry) -> None:
    """
    Register optimizer tools with the registry

    Args:
        registry: ToolRegistry instance to populate
    """
    from .optimizer_tools import OPTIMIZER_TOOLS

    for tool_def in OPTIMIZER_TOOLS:
        registry.register_tool(ToolDefinition(
            name=tool_def['name'],
            description=f"Database optimization tool: {tool_def['name']}",
            category=ToolCategory.OPTIMIZATION,
            risk_level=ToolRiskLevel.MEDIUM,
            required_capabilities=["database_read", "performance_analyze"],
            parameters_schema=tool_def['schema'],
            returns_schema={"type": "object"},
            implementation=tool_def['func'],
            requires_approval=False,
            max_execution_time=120
        ))


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

    # Register tool groups
    register_database_tools(registry)
    # register_backup_tools(registry)
    register_migration_tools(registry)
    register_optimizer_tools(registry)


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
    'register_migration_tools',
    'register_optimizer_tools',
    'create_default_registry'
]
