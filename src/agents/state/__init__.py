"""
State Management and Checkpointing System

This module provides state persistence, checkpoint management, and recovery
capabilities for agent workflows.

Key Components:
- StateManager: Main state management and checkpointing interface
- Checkpoint: Data class representing a workflow checkpoint
- Recovery: Workflow recovery and restoration utilities

Usage:
    from src.agents.state import StateManager, Checkpoint

    state_manager = StateManager()
    checkpoint_id = await state_manager.save_checkpoint(
        task_id="task_001",
        checkpoint_name="step_1_complete",
        data={"result": "success"}
    )
"""

from src.agents.state.manager import StateManager, Checkpoint

__all__ = ["StateManager", "Checkpoint"]
