"""
Safety and Approval System for Agentic AI Workflows

This module provides comprehensive safety validation, approval mechanisms,
and risk management for agent operations in AIShell.

Classes:
    ApprovalRequirement: Enumeration of approval requirement levels
    SafetyController: Central safety validation and approval system

The SafetyController integrates with:
- Database risk analyzer for SQL operation analysis
- Tool registry for risk level assessment
- Agent configuration for safety level enforcement
- Interactive CLI for approval prompts

Usage:
    from src.agents.safety import SafetyController, ApprovalRequirement
    from src.database.risk_analyzer import SQLRiskAnalyzer

    risk_analyzer = SQLRiskAnalyzer()
    safety_controller = SafetyController(risk_analyzer)

    # Validate step safety
    validation = safety_controller.validate_step(step, agent_config)

    # Request approval if needed
    if validation['requires_approval']:
        approval = await safety_controller.request_approval(
            step, validation, approval_callback
        )
"""

from .controller import SafetyController, ApprovalRequirement

__all__ = ['SafetyController', 'ApprovalRequirement']
