"""
Tool Registry System for Agentic AI Workflows

This module provides the core tool registry infrastructure for agents,
including tool definitions, categorization, risk assessment, and validation.
"""

from typing import Dict, Any, Callable, List, Optional, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import json
import jsonschema
from jsonschema import validate, ValidationError


class ToolCategory(Enum):
    """Tool categorization for filtering and organization"""
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    DATABASE_DDL = "database_ddl"
    FILE_SYSTEM = "file_system"
    BACKUP = "backup"
    ANALYSIS = "analysis"
    MIGRATION = "migration"
    OPTIMIZATION = "optimization"


class ToolRiskLevel(Enum):
    """Risk levels for tools determining approval requirements"""
    SAFE = "safe"          # Read-only, no side effects
    LOW = "low"            # Minor modifications
    MEDIUM = "medium"      # Significant modifications
    HIGH = "high"          # Potentially destructive
    CRITICAL = "critical"  # Irreversible operations


@dataclass
class ToolDefinition:
    """
    Tool definition with metadata and execution capabilities

    Attributes:
        name: Unique tool identifier
        description: Human-readable description
        category: Tool category for filtering
        risk_level: Risk assessment level
        required_capabilities: Capabilities agent must have
        parameters_schema: JSON schema for parameter validation
        returns_schema: JSON schema for return value structure
        implementation: Async callable that executes the tool
        requires_approval: Whether human approval is needed
        max_execution_time: Maximum allowed execution time in seconds
        rate_limit: Optional rate limit in calls per minute
        examples: Example usage patterns for documentation
    """
    name: str
    description: str
    category: ToolCategory
    risk_level: ToolRiskLevel
    required_capabilities: List[str]
    parameters_schema: Dict[str, Any]
    returns_schema: Dict[str, Any]
    implementation: Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[Dict[str, Any]]]

    # Safety constraints
    requires_approval: bool
    max_execution_time: int  # seconds
    rate_limit: Optional[int] = None  # calls per minute

    # Documentation
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters against JSON schema

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate(instance=params, schema=self.parameters_schema)
            return True, None
        except ValidationError as e:
            return False, f"Parameter validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_return_value(self, result: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate return value against JSON schema

        Args:
            result: Return value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate(instance=result, schema=self.returns_schema)
            return True, None
        except ValidationError as e:
            return False, f"Return value validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool with validated parameters

        Args:
            params: Tool parameters
            context: Execution context (database_module, llm_manager, etc.)

        Returns:
            Tool execution result

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If execution fails
        """
        # Validate parameters
        is_valid, error_msg = self.validate_parameters(params)
        if not is_valid:
            raise ValueError(f"Invalid parameters for tool {self.name}: {error_msg}")

        # Execute implementation
        try:
            result = await self.implementation(params, context)
        except Exception as e:
            raise RuntimeError(f"Tool {self.name} execution failed: {str(e)}") from e

        # Validate return value
        is_valid, error_msg = self.validate_return_value(result)
        if not is_valid:
            raise RuntimeError(f"Invalid return value from tool {self.name}: {error_msg}")

        return result


class ToolRegistry:
    """
    Central registry for all agent tools

    Provides:
    - Tool registration and discovery
    - Capability-based filtering
    - Safety validation
    - Execution tracking
    - LLM-friendly tool descriptions
    """

    def __init__(self):
        """Initialize empty tool registry"""
        self._tools: Dict[str, ToolDefinition] = {}
        self._execution_log: List[Dict[str, Any]] = []
        self._rate_limit_tracking: Dict[str, List[float]] = {}

    def register_tool(self, tool: ToolDefinition) -> None:
        """
        Register a new tool

        Args:
            tool: Tool definition to register

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        self._tools[tool.name] = tool

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        Get tool by name

        Args:
            name: Tool name

        Returns:
            Tool definition or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def find_tools(
        self,
        category: Optional[ToolCategory] = None,
        max_risk: Optional[ToolRiskLevel] = None,
        capabilities: Optional[List[str]] = None
    ) -> List[ToolDefinition]:
        """
        Find tools matching criteria

        Args:
            category: Filter by tool category
            max_risk: Filter by maximum risk level
            capabilities: Filter by required capabilities (agent must have all)

        Returns:
            List of matching tool definitions
        """
        tools = list(self._tools.values())

        # Filter by category
        if category:
            tools = [t for t in tools if t.category == category]

        # Filter by risk level
        if max_risk:
            risk_levels = [
                ToolRiskLevel.SAFE,
                ToolRiskLevel.LOW,
                ToolRiskLevel.MEDIUM,
                ToolRiskLevel.HIGH,
                ToolRiskLevel.CRITICAL
            ]
            max_index = risk_levels.index(max_risk)
            tools = [t for t in tools if risk_levels.index(t.risk_level) <= max_index]

        # Filter by capabilities
        if capabilities:
            tools = [
                t for t in tools
                if all(cap in capabilities for cap in t.required_capabilities)
            ]

        return tools

    def get_tool_description(self, name: str) -> str:
        """
        Get human-readable tool description for LLM prompts

        Args:
            name: Tool name

        Returns:
            Formatted tool description
        """
        tool = self.get_tool(name)
        if not tool:
            return f"Tool '{name}' not found"

        examples_str = ""
        if tool.examples:
            examples_str = "\nExamples:\n" + json.dumps(tool.examples, indent=2)

        return f"""
Tool: {tool.name}
Description: {tool.description}
Category: {tool.category.value}
Risk Level: {tool.risk_level.value}
Requires Approval: {tool.requires_approval}

Parameters:
{json.dumps(tool.parameters_schema, indent=2)}

Returns:
{json.dumps(tool.returns_schema, indent=2)}
{examples_str}
""".strip()

    def get_available_tools_for_llm(
        self,
        capabilities: List[str],
        max_risk: Optional[ToolRiskLevel] = None,
        category: Optional[ToolCategory] = None
    ) -> str:
        """
        Get formatted tool descriptions for LLM prompt

        Args:
            capabilities: Agent capabilities to filter by
            max_risk: Maximum risk level to include
            category: Optional category filter

        Returns:
            Formatted string of all available tools
        """
        tools = self.find_tools(
            category=category,
            max_risk=max_risk,
            capabilities=capabilities
        )

        if not tools:
            return "No tools available for the specified criteria."

        descriptions = [self.get_tool_description(t.name) for t in tools]

        return "\n\n" + "="*60 + "\n\n".join(descriptions)

    def log_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Log tool execution for audit trail

        Args:
            tool_name: Name of executed tool
            params: Parameters used
            result: Execution result
            execution_time: Time taken in seconds
            success: Whether execution succeeded
            error: Error message if failed
        """
        import time

        log_entry = {
            'timestamp': time.time(),
            'tool_name': tool_name,
            'params': params,
            'result': result if success else None,
            'execution_time': execution_time,
            'success': success,
            'error': error
        }

        self._execution_log.append(log_entry)

    def get_execution_log(
        self,
        tool_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get execution log entries

        Args:
            tool_name: Filter by tool name
            limit: Maximum number of entries to return

        Returns:
            List of log entries
        """
        logs = self._execution_log

        if tool_name:
            logs = [log for log in logs if log['tool_name'] == tool_name]

        if limit:
            logs = logs[-limit:]

        return logs

    def check_rate_limit(self, tool_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if tool is within rate limit

        Args:
            tool_name: Tool to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        import time

        tool = self.get_tool(tool_name)
        if not tool or not tool.rate_limit:
            return True, None

        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        # Initialize tracking if needed
        if tool_name not in self._rate_limit_tracking:
            self._rate_limit_tracking[tool_name] = []

        # Remove old entries outside the window
        self._rate_limit_tracking[tool_name] = [
            t for t in self._rate_limit_tracking[tool_name]
            if t > window_start
        ]

        # Check rate limit
        call_count = len(self._rate_limit_tracking[tool_name])
        if call_count >= tool.rate_limit:
            return False, f"Rate limit exceeded: {call_count}/{tool.rate_limit} calls per minute"

        # Record this call attempt
        self._rate_limit_tracking[tool_name].append(current_time)

        return True, None

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics

        Returns:
            Statistics about registered tools and executions
        """
        total_tools = len(self._tools)

        # Count by category
        by_category = {}
        for tool in self._tools.values():
            cat = tool.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Count by risk level
        by_risk = {}
        for tool in self._tools.values():
            risk = tool.risk_level.value
            by_risk[risk] = by_risk.get(risk, 0) + 1

        # Execution stats
        total_executions = len(self._execution_log)
        successful_executions = sum(1 for log in self._execution_log if log['success'])

        return {
            'total_tools': total_tools,
            'tools_by_category': by_category,
            'tools_by_risk_level': by_risk,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': total_executions - successful_executions
        }
