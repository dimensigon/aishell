"""
Test Agent Implementation for Benchmarking

Provides a lightweight concrete agent implementation for performance testing.
"""

from typing import Dict, Any, List
from src.agents.base import BaseAgent, TaskContext


class TestAgent(BaseAgent):
    """Concrete agent implementation for testing."""

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Create simple test plan."""
        return [{'action': 'test', 'data': 'mock'}]

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test step."""
        return {'status': 'completed', 'step': step}

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test step safety."""
        return {
            'requires_approval': False,
            'safe': True,
            'risk_level': 'low'
        }
