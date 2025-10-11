"""
Mock state manager for testing.

Provides lightweight state management for performance testing.
"""

from typing import Dict, Any, Optional, List
import json


class StateManager:
    """Mock state manager for testing."""

    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}

    def save_state(self, agent_id: str, state: Dict[str, Any]) -> None:
        """Save agent state."""
        self._states[agent_id] = json.loads(json.dumps(state))  # Deep copy

    def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state."""
        return self._states.get(agent_id)

    def delete_state(self, agent_id: str) -> None:
        """Delete agent state."""
        if agent_id in self._states:
            del self._states[agent_id]

    def list_states(self) -> List[str]:
        """List all states."""
        return list(self._states.keys())
