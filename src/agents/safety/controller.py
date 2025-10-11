"""
Safety Controller for Agentic AI Workflows

This module implements the central safety validation and approval system
for database agent operations, providing multi-layer risk assessment and
human-in-the-loop approval mechanisms.
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
from datetime import datetime
import asyncio

# Import from existing AIShell modules
from src.agents.base import AgentConfig
from src.agents.tools.registry import ToolRiskLevel, ToolCategory
from src.database.risk_analyzer import SQLRiskAnalyzer, RiskLevel


class SafetyLevel(Enum):
    """
    Safety levels for agent operations

    Levels:
        LOW: Minimal safety checks
        MEDIUM: Standard safety validation
        HIGH: Strict safety enforcement
        CRITICAL: Maximum safety with multiple approvals
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequirement(Enum):
    """
    Approval requirement levels for agent operations

    Levels:
        NONE: No approval needed, safe to execute automatically
        OPTIONAL: Approval is recommended but not required
        REQUIRED: Approval must be obtained before execution
        MULTI_PARTY: Requires multiple approvals (future enhancement)
    """
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"
    MULTI_PARTY = "multi_party"  # Requires multiple approvals


class SafetyViolation(Exception):
    """
    Exception raised when a safety violation is detected

    Attributes:
        message: Description of the violation
        risk_level: Risk level that triggered the violation
        details: Additional context about the violation
    """
    def __init__(self, message: str, risk_level: str = "unknown", details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.risk_level = risk_level
        self.details = details or {}
        super().__init__(self.message)


class SafetyPolicy:
    """
    Safety policy configuration for agent operations

    Attributes:
        safety_level: Required safety level
        require_approval_for: List of operations requiring approval
        blocked_operations: List of completely blocked operations
        allow_destructive: Whether destructive operations are allowed
    """
    def __init__(
        self,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM,
        require_approval_for: Optional[List[str]] = None,
        blocked_operations: Optional[List[str]] = None,
        allow_destructive: bool = False
    ):
        self.safety_level = safety_level
        self.require_approval_for = require_approval_for or []
        self.blocked_operations = blocked_operations or []
        self.allow_destructive = allow_destructive

    def is_operation_allowed(self, operation: str) -> bool:
        """Check if an operation is allowed under this policy"""
        return operation not in self.blocked_operations

    def requires_approval(self, operation: str) -> bool:
        """Check if an operation requires approval"""
        return operation in self.require_approval_for


class SafetyController:
    """
    Central safety validation and approval system

    Provides comprehensive safety checks for agent operations including:
    - Risk assessment based on tool type and parameters
    - Safety level enforcement per agent configuration
    - SQL-specific risk analysis via database risk analyzer
    - Interactive approval workflows with detailed risk display
    - Complete audit trail of all approval decisions

    Attributes:
        risk_analyzer: SQL risk analyzer for database operations
        approval_history: Audit trail of all approval requests and decisions

    Example:
        >>> risk_analyzer = SQLRiskAnalyzer()
        >>> controller = SafetyController(risk_analyzer)
        >>> validation = controller.validate_step(step, agent_config)
        >>> if validation['requires_approval']:
        ...     approval = await controller.request_approval(step, validation)
    """

    def __init__(self, risk_analyzer: SQLRiskAnalyzer) -> None:
        """
        Initialize Safety Controller

        Args:
            risk_analyzer: SQL risk analyzer instance for database operation analysis
        """
        self.risk_analyzer = risk_analyzer
        self.approval_history: List[Dict[str, Any]] = []

    def validate_step(self, step: Dict[str, Any],
                     agent_config: AgentConfig) -> Dict[str, Any]:
        """
        Validate safety of a planned agent step

        Performs comprehensive safety analysis including:
        1. Tool risk level assessment
        2. Agent safety level compatibility check
        3. Operation type-specific validations
        4. SQL risk analysis for database operations
        5. Destructive operation detection

        Args:
            step: Step definition containing tool name, params, and tool_definition
            agent_config: Agent configuration with safety level settings

        Returns:
            Dictionary containing:
                - safe: Boolean indicating if step is safe to execute
                - risk_level: String risk level (safe/low/medium/high/critical)
                - requires_approval: Boolean indicating if approval is needed
                - approval_requirement: ApprovalRequirement enum value
                - risks: List of identified risks
                - mitigations: List of available risk mitigations
                - sql_analysis: Optional SQL-specific risk analysis

        Example:
            >>> validation = controller.validate_step(
            ...     {'tool': 'execute_migration', 'params': {...}},
            ...     agent_config
            ... )
            >>> print(validation['requires_approval'])
            True
        """
        tool_name = step['tool']
        tool_params = step.get('params', {})

        # Get tool definition from step
        tool = step.get('tool_definition')

        # Initialize validation result
        validation = {
            'safe': True,
            'risk_level': 'safe',
            'requires_approval': False,
            'approval_requirement': ApprovalRequirement.NONE,
            'risks': [],
            'mitigations': []
        }

        # If no tool definition provided, apply conservative defaults
        if not tool:
            validation['risk_level'] = 'unknown'
            validation['requires_approval'] = True
            validation['approval_requirement'] = ApprovalRequirement.REQUIRED
            validation['risks'].append("Tool definition not available for validation")
            return validation

        # Set base risk level from tool
        validation['risk_level'] = tool.risk_level.value
        validation['requires_approval'] = tool.requires_approval

        # Apply safety level based enforcement
        if agent_config.safety_level == 'strict':
            # Strict mode: require approval for HIGH and CRITICAL operations
            if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
                validation['requires_approval'] = True
                validation['approval_requirement'] = ApprovalRequirement.REQUIRED
                validation['risks'].append(
                    f"Strict safety mode requires approval for {tool.risk_level.value} risk operations"
                )

        elif agent_config.safety_level == 'moderate':
            # Moderate mode: require approval only for CRITICAL operations
            if tool.risk_level == ToolRiskLevel.CRITICAL:
                validation['requires_approval'] = True
                validation['approval_requirement'] = ApprovalRequirement.REQUIRED
                validation['risks'].append(
                    "Critical operation requires approval even in moderate safety mode"
                )
            elif tool.risk_level == ToolRiskLevel.HIGH:
                validation['approval_requirement'] = ApprovalRequirement.OPTIONAL

        # Safety level 'permissive' would only require explicit tool approval flags

        # Category-specific validations
        if tool.category == ToolCategory.DATABASE_WRITE:
            validation['risks'].append("Data modification operation")
            validation['mitigations'].append("Backup created before execution")

            # Analyze SQL if present in parameters
            if 'sql' in tool_params or 'query' in tool_params:
                sql = tool_params.get('sql') or tool_params.get('query')
                sql_analysis = self.risk_analyzer.analyze(sql)
                validation['sql_analysis'] = sql_analysis

                # Upgrade risk level if SQL analysis indicates higher risk
                if sql_analysis['risk_level'] in ['HIGH', 'CRITICAL']:
                    validation['requires_approval'] = True
                    validation['risks'].extend(sql_analysis.get('warnings', []))

        if tool.category == ToolCategory.DATABASE_DDL:
            validation['risks'].append("Schema modification operation")
            validation['mitigations'].append("Rollback script generated")
            # DDL operations always require approval
            validation['requires_approval'] = True
            validation['approval_requirement'] = ApprovalRequirement.REQUIRED

            # Analyze DDL SQL if present
            if 'migration_sql' in tool_params or 'sql' in tool_params:
                sql = tool_params.get('migration_sql') or tool_params.get('sql')
                sql_analysis = self.risk_analyzer.analyze(sql)
                validation['sql_analysis'] = sql_analysis
                validation['risks'].extend(sql_analysis.get('warnings', []))

        # Check for destructive operations
        if self._is_destructive_operation(step):
            validation['requires_approval'] = True
            validation['approval_requirement'] = ApprovalRequirement.MULTI_PARTY
            validation['risks'].append("Potentially irreversible destructive operation")
            validation['mitigations'].append("Multi-party approval required")

        # Set safe flag based on final risk assessment
        validation['safe'] = validation['risk_level'] in ['safe', 'low', 'medium']

        return validation

    def _is_destructive_operation(self, step: Dict[str, Any]) -> bool:
        """
        Check if operation is potentially destructive

        Destructive operations are those that may result in irreversible
        data loss or system changes. These require the highest level of
        approval and safety checks.

        Args:
            step: Step definition to check

        Returns:
            True if operation is destructive, False otherwise
        """
        destructive_tools = [
            'execute_migration',
            'drop_table',
            'drop_database',
            'truncate_table',
            'delete_backup',
            'restore_backup',  # Restore is destructive as it overwrites current state
            'drop_index',
            'drop_schema'
        ]

        tool_name = step.get('tool', '')

        # Check if tool name matches destructive operations
        if tool_name in destructive_tools:
            return True

        # Check SQL content for destructive patterns if available
        params = step.get('params', {})
        sql_content = params.get('sql') or params.get('migration_sql') or params.get('query') or ''

        if sql_content:
            destructive_patterns = ['DROP', 'TRUNCATE', 'DELETE FROM']
            sql_upper = sql_content.upper()
            for pattern in destructive_patterns:
                if pattern in sql_upper:
                    return True

        return False

    async def request_approval(
        self,
        step: Dict[str, Any],
        validation: Dict[str, Any],
        approval_callback: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Request approval for a risky step

        Handles the approval workflow by either:
        1. Calling a custom approval callback if provided
        2. Falling back to interactive CLI approval

        The approval request includes full context about the operation,
        risks, and available mitigations. All approvals are logged to
        the audit trail.

        Args:
            step: Step requiring approval
            validation: Validation result from validate_step
            approval_callback: Optional custom approval handler

        Returns:
            Dictionary containing:
                - approved: Boolean indicating if operation was approved
                - reason: Explanation for approval/rejection
                - approver: Identifier of who approved (e.g., 'user', 'admin')
                - timestamp: ISO format timestamp of decision
                - conditions: List of any conditions attached to approval

        Example:
            >>> approval = await controller.request_approval(
            ...     step={'tool': 'execute_migration', 'params': {...}},
            ...     validation={'risk_level': 'critical', ...}
            ... )
            >>> if approval['approved']:
            ...     # Proceed with operation
        """
        approval_request = {
            'step': step,
            'validation': validation,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Use custom callback if provided, otherwise use interactive approval
        if approval_callback:
            approval = await approval_callback(approval_request)
        else:
            # Interactive CLI approval
            approval = await self._interactive_approval(approval_request)

        # Log approval to history for audit trail
        self.approval_history.append({
            'request': approval_request,
            'approval': approval,
            'decision_timestamp': datetime.utcnow().isoformat()
        })

        return approval

    async def _interactive_approval(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interactive CLI approval prompt

        Displays comprehensive information about the operation requiring
        approval including:
        - Tool name and operation type
        - Risk level assessment
        - Operation parameters
        - Identified risks
        - Available mitigations
        - SQL analysis (if applicable)

        Prompts user for approval decision and optional rejection reason.

        Args:
            request: Approval request containing step and validation info

        Returns:
            Dictionary with approval decision details
        """
        step = request['step']
        validation = request['validation']

        # Display approval prompt header
        print("\n" + "=" * 70)
        print("⚠️  APPROVAL REQUIRED FOR AGENT OPERATION")
        print("=" * 70)

        # Display operation details
        print(f"\n🔧 Tool: {step['tool']}")
        print(f"⚡ Risk Level: {validation['risk_level'].upper()}")
        print(f"🛡️  Approval Requirement: {validation['approval_requirement'].value}")

        # Display parameters
        print(f"\n📋 Parameters:")
        for key, value in step.get('params', {}).items():
            # Truncate long values for readability
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            print(f"  • {key}: {value_str}")

        # Display SQL analysis if available
        if 'sql_analysis' in validation:
            sql_analysis = validation['sql_analysis']
            print(f"\n🔍 SQL Analysis:")
            print(f"  • SQL Risk Level: {sql_analysis['risk_level']}")
            print(f"  • Requires Confirmation: {sql_analysis['requires_confirmation']}")
            if sql_analysis.get('issues'):
                print(f"  • Issues: {', '.join(sql_analysis['issues'])}")

        # Display identified risks
        if validation['risks']:
            print(f"\n⚠️  Identified Risks:")
            for risk in validation['risks']:
                print(f"  • {risk}")

        # Display available mitigations
        if validation['mitigations']:
            print(f"\n✅ Available Mitigations:")
            for mitigation in validation['mitigations']:
                print(f"  • {mitigation}")

        print("\n" + "=" * 70)

        # Prompt for approval decision
        print("\n⚡ This operation requires your approval to proceed.")
        response = input("Approve this operation? (yes/no): ").strip().lower()

        if response in ['yes', 'y']:
            return {
                'approved': True,
                'reason': 'User approved via interactive prompt',
                'approver': 'user',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }
        else:
            # If rejected, ask for reason
            reason = input("Rejection reason (optional): ").strip()
            return {
                'approved': False,
                'reason': reason or 'User rejected operation',
                'approver': 'user',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }

    def get_approval_history(
        self,
        limit: Optional[int] = None,
        approved_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get approval history for audit purposes

        Args:
            limit: Maximum number of records to return (None for all)
            approved_only: If True, return only approved operations

        Returns:
            List of approval history entries
        """
        history = self.approval_history

        if approved_only:
            history = [h for h in history if h['approval']['approved']]

        if limit:
            history = history[-limit:]

        return history

    def clear_approval_history(self):
        """Clear approval history (use with caution)"""
        self.approval_history = []
