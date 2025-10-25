"""Agent state management for persistent workflows."""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import threading
import os
import tempfile


class StateManager:
    """Manages agent state persistence across sessions."""

    def __init__(self, storage_path: Optional[str] = None):
        self._storage_path = storage_path or os.path.join(tempfile.gettempdir(), 'agent_state')
        self._states: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        os.makedirs(self._storage_path, exist_ok=True)

    def save_state(self, agent_id: str, state: Dict[str, Any]) -> None:
        """Save agent state."""
        with self._lock:
            state_with_metadata = {
                'agent_id': agent_id,
                'saved_at': datetime.now().isoformat(),
                'state': state
            }
            self._states[agent_id] = state_with_metadata
            state_file = os.path.join(self._storage_path, f'{agent_id}.json')
            with open(state_file, 'w') as f:
                json.dump(state_with_metadata, f, indent=2, default=str)

    def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state."""
        if agent_id in self._states:
            return self._states[agent_id]['state']
        state_file = os.path.join(self._storage_path, f'{agent_id}.json')
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state_with_metadata = json.load(f)
                    self._states[agent_id] = state_with_metadata
                    return state_with_metadata['state']
            except Exception:
                pass
        return None
