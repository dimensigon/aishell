"""Test utilities for agent testing"""

from typing import Dict, Any, List, Optional


class MockStateManager:
    """Mock state manager for testing that implements checkpoint functionality"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._checkpoint_list: Dict[str, List[str]] = {}

    async def save_checkpoint(self, task_id: str, checkpoint_name: str, data: Any) -> None:
        """Save a checkpoint"""
        key = f"{task_id}:{checkpoint_name}"
        self._checkpoints[key] = data

        if task_id not in self._checkpoint_list:
            self._checkpoint_list[task_id] = []
        if checkpoint_name not in self._checkpoint_list[task_id]:
            self._checkpoint_list[task_id].append(checkpoint_name)

    async def load_checkpoint(self, task_id: str, checkpoint_name: str) -> Optional[Any]:
        """Load a checkpoint"""
        key = f"{task_id}:{checkpoint_name}"
        return self._checkpoints.get(key)

    async def get_checkpoints(self, task_id: str) -> List[str]:
        """Get list of checkpoint names for a task"""
        return self._checkpoint_list.get(task_id, [])

    def save_state(self, agent_id: str, state: Dict[str, Any]) -> None:
        """Save agent state"""
        key = f"state:{agent_id}"
        self._checkpoints[key] = state

    def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state"""
        key = f"state:{agent_id}"
        return self._checkpoints.get(key)
