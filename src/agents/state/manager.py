"""
State Manager Implementation

Provides workflow state persistence, checkpoint management, and audit logging
using SQLite for reliable storage and recovery.
"""

from typing import Dict, Any, List, Optional
import sqlite3
import json
import time
from datetime import datetime
from dataclasses import dataclass
import os
import asyncio
from pathlib import Path


@dataclass
class Checkpoint:
    """
    Workflow checkpoint data structure

    Attributes:
        checkpoint_id: Unique identifier for the checkpoint
        task_id: ID of the task this checkpoint belongs to
        checkpoint_name: Human-readable name for the checkpoint
        checkpoint_data: Serialized checkpoint data
        timestamp: When the checkpoint was created
        sequence_number: Sequential number for ordering checkpoints
    """
    checkpoint_id: str
    task_id: str
    checkpoint_name: str
    checkpoint_data: Dict[str, Any]
    timestamp: datetime
    sequence_number: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary"""
        return {
            'checkpoint_id': self.checkpoint_id,
            'task_id': self.task_id,
            'checkpoint_name': self.checkpoint_name,
            'checkpoint_data': self.checkpoint_data,
            'timestamp': self.timestamp.isoformat(),
            'sequence_number': self.sequence_number
        }


class StateManager:
    """
    Manages workflow state and checkpointing

    Responsibilities:
    - State persistence to SQLite database
    - Checkpoint creation and retrieval
    - Recovery support for failed workflows
    - Audit logging for all workflow events

    The StateManager uses SQLite for reliable, transactional storage of
    workflow state, checkpoints, and execution logs. All operations are
    async-compatible for integration with async workflows.

    Database Schema:
    - checkpoints: Stores workflow checkpoints
    - workflow_state: Stores current workflow state
    - execution_log: Stores audit log of all events

    Usage:
        state_manager = StateManager()

        # Save checkpoint
        checkpoint_id = await state_manager.save_checkpoint(
            task_id="task_001",
            checkpoint_name="step_1_complete",
            data={"result": "success", "output": "backup_001.sql"}
        )

        # Retrieve checkpoint
        checkpoint = await state_manager.get_checkpoint(checkpoint_id)

        # Get all checkpoints for a task
        checkpoints = await state_manager.get_checkpoints("task_001")

        # Restore from checkpoint
        data = await state_manager.restore_from_checkpoint(checkpoint_id)

        # Log event
        await state_manager.log_event(
            task_id="task_001",
            event_type="step_executed",
            event_data={"step": "backup", "status": "success"}
        )
    """

    def __init__(self, db_path: str = ".aishell/workflow_state.db"):
        """
        Initialize StateManager

        Args:
            db_path: Path to SQLite database file. Defaults to .aishell/workflow_state.db
                     Parent directories will be created if they don't exist.
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_database(self) -> None:
        """
        Initialize state database with required tables and indexes

        Creates three tables:
        1. checkpoints: Stores workflow checkpoints with sequence numbers
        2. workflow_state: Stores current state of active workflows
        3. execution_log: Stores audit log of all workflow events

        Indexes are created for efficient querying by task_id and sequence.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create checkpoints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                checkpoint_name TEXT NOT NULL,
                checkpoint_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sequence_number INTEGER NOT NULL
            )
        """)

        # Create indexes for checkpoints table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_id
            ON checkpoints (task_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sequence
            ON checkpoints (task_id, sequence_number)
        """)

        # Create workflow_state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_state (
                task_id TEXT PRIMARY KEY,
                workflow_type TEXT NOT NULL,
                current_state TEXT NOT NULL,
                state_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create execution_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                log_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Create index for execution_log table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_log
            ON execution_log (task_id)
        """)

        conn.commit()
        conn.close()

    async def save_checkpoint(
        self,
        task_id: str,
        checkpoint_name: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Save workflow checkpoint

        Creates a new checkpoint for the specified task with automatic
        sequence numbering. Each checkpoint is assigned a unique ID and
        sequence number for ordering.

        Args:
            task_id: ID of the task to checkpoint
            checkpoint_name: Human-readable name for this checkpoint
            data: Dictionary containing checkpoint data to persist

        Returns:
            checkpoint_id: Unique identifier for the created checkpoint

        Raises:
            sqlite3.Error: If database operation fails

        Example:
            checkpoint_id = await state_manager.save_checkpoint(
                task_id="backup_task_001",
                checkpoint_name="backup_created",
                data={
                    "backup_path": "/backups/prod_backup.sql",
                    "size_bytes": 1024000,
                    "checksum": "abc123..."
                }
            )
        """
        # Run database operation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._save_checkpoint_sync,
            task_id,
            checkpoint_name,
            data
        )

    def _save_checkpoint_sync(
        self,
        task_id: str,
        checkpoint_name: str,
        data: Dict[str, Any]
    ) -> str:
        """Synchronous implementation of save_checkpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get next sequence number for this task
            cursor.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM checkpoints WHERE task_id = ?",
                (task_id,)
            )
            sequence_number = cursor.fetchone()[0]

            # Generate checkpoint ID
            checkpoint_id = f"{task_id}_cp_{sequence_number}"

            # Insert checkpoint
            cursor.execute("""
                INSERT INTO checkpoints
                (checkpoint_id, task_id, checkpoint_name, checkpoint_data, timestamp, sequence_number)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                checkpoint_id,
                task_id,
                checkpoint_name,
                json.dumps(data),
                datetime.utcnow().isoformat(),
                sequence_number
            ))

            conn.commit()
            return checkpoint_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Retrieve specific checkpoint by ID

        Args:
            checkpoint_id: Unique identifier of the checkpoint to retrieve

        Returns:
            Checkpoint object if found, None otherwise

        Example:
            checkpoint = await state_manager.get_checkpoint("task_001_cp_1")
            if checkpoint:
                print(f"Checkpoint: {checkpoint.checkpoint_name}")
                print(f"Data: {checkpoint.checkpoint_data}")
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_checkpoint_sync,
            checkpoint_id
        )

    def _get_checkpoint_sync(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Synchronous implementation of get_checkpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT checkpoint_id, task_id, checkpoint_name, checkpoint_data,
                       timestamp, sequence_number
                FROM checkpoints
                WHERE checkpoint_id = ?
            """, (checkpoint_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return Checkpoint(
                checkpoint_id=row[0],
                task_id=row[1],
                checkpoint_name=row[2],
                checkpoint_data=json.loads(row[3]),
                timestamp=datetime.fromisoformat(row[4]),
                sequence_number=row[5]
            )

        finally:
            conn.close()

    async def get_checkpoints(self, task_id: str) -> List[str]:
        """
        Get all checkpoint IDs for a task, ordered by sequence number

        Args:
            task_id: ID of the task to get checkpoints for

        Returns:
            List of checkpoint IDs in sequential order

        Example:
            checkpoint_ids = await state_manager.get_checkpoints("task_001")
            print(f"Found {len(checkpoint_ids)} checkpoints")
            for cp_id in checkpoint_ids:
                checkpoint = await state_manager.get_checkpoint(cp_id)
                print(f"  - {checkpoint.checkpoint_name}")
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_checkpoints_sync,
            task_id
        )

    def _get_checkpoints_sync(self, task_id: str) -> List[str]:
        """Synchronous implementation of get_checkpoints"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT checkpoint_id
                FROM checkpoints
                WHERE task_id = ?
                ORDER BY sequence_number
            """, (task_id,))

            checkpoints = [row[0] for row in cursor.fetchall()]
            return checkpoints

        finally:
            conn.close()

    async def get_latest_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
        """
        Get most recent checkpoint for a task

        Retrieves the checkpoint with the highest sequence number for
        the specified task.

        Args:
            task_id: ID of the task to get latest checkpoint for

        Returns:
            Latest Checkpoint object if any exist, None otherwise

        Example:
            latest = await state_manager.get_latest_checkpoint("task_001")
            if latest:
                print(f"Latest checkpoint: {latest.checkpoint_name}")
                print(f"Sequence: {latest.sequence_number}")
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_latest_checkpoint_sync,
            task_id
        )

    def _get_latest_checkpoint_sync(self, task_id: str) -> Optional[Checkpoint]:
        """Synchronous implementation of get_latest_checkpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT checkpoint_id, task_id, checkpoint_name, checkpoint_data,
                       timestamp, sequence_number
                FROM checkpoints
                WHERE task_id = ?
                ORDER BY sequence_number DESC
                LIMIT 1
            """, (task_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return Checkpoint(
                checkpoint_id=row[0],
                task_id=row[1],
                checkpoint_name=row[2],
                checkpoint_data=json.loads(row[3]),
                timestamp=datetime.fromisoformat(row[4]),
                sequence_number=row[5]
            )

        finally:
            conn.close()

    async def restore_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Restore workflow state from checkpoint

        Retrieves the checkpoint data for resuming workflow execution
        from the specified checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore from

        Returns:
            Dictionary containing the checkpoint data

        Raises:
            ValueError: If checkpoint not found

        Example:
            try:
                data = await state_manager.restore_from_checkpoint("task_001_cp_3")
                print(f"Restored data: {data}")
                # Resume workflow execution using restored data
            except ValueError as e:
                print(f"Restore failed: {e}")
        """
        checkpoint = await self.get_checkpoint(checkpoint_id)

        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        return checkpoint.checkpoint_data

    async def log_event(
        self,
        task_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Log workflow event for audit trail

        Records an event in the execution log for auditing and debugging.
        All events are timestamped and associated with a task.

        Args:
            task_id: ID of task this event belongs to
            event_type: Type/category of event (e.g., "step_executed", "error", "approval_requested")
            event_data: Dictionary containing event details

        Example:
            await state_manager.log_event(
                task_id="backup_task_001",
                event_type="step_executed",
                event_data={
                    "step": "create_backup",
                    "status": "success",
                    "duration_seconds": 45.2
                }
            )

            await state_manager.log_event(
                task_id="backup_task_001",
                event_type="error",
                event_data={
                    "step": "verify_backup",
                    "error": "Checksum mismatch",
                    "severity": "high"
                }
            )
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._log_event_sync,
            task_id,
            event_type,
            event_data
        )

    def _log_event_sync(
        self,
        task_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Synchronous implementation of log_event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Generate unique log ID with timestamp
            log_id = f"{task_id}_{event_type}_{int(time.time() * 1000000)}"

            cursor.execute("""
                INSERT INTO execution_log
                (log_id, task_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                log_id,
                task_id,
                event_type,
                json.dumps(event_data),
                datetime.utcnow().isoformat()
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def update_workflow_state(
        self,
        task_id: str,
        workflow_type: str,
        current_state: str,
        state_data: Dict[str, Any]
    ) -> None:
        """
        Update or create workflow state record

        Maintains the current state of a workflow for monitoring and recovery.

        Args:
            task_id: ID of the workflow task
            workflow_type: Type of workflow (e.g., "backup", "migration", "optimization")
            current_state: Current state of workflow (e.g., "planning", "executing", "completed")
            state_data: Additional state data

        Example:
            await state_manager.update_workflow_state(
                task_id="task_001",
                workflow_type="backup",
                current_state="executing",
                state_data={"current_step": 2, "total_steps": 5}
            )
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._update_workflow_state_sync,
            task_id,
            workflow_type,
            current_state,
            state_data
        )

    def _update_workflow_state_sync(
        self,
        task_id: str,
        workflow_type: str,
        current_state: str,
        state_data: Dict[str, Any]
    ) -> None:
        """Synchronous implementation of update_workflow_state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.utcnow().isoformat()

            # Check if record exists
            cursor.execute(
                "SELECT task_id FROM workflow_state WHERE task_id = ?",
                (task_id,)
            )
            exists = cursor.fetchone()

            if exists:
                # Update existing record
                cursor.execute("""
                    UPDATE workflow_state
                    SET workflow_type = ?,
                        current_state = ?,
                        state_data = ?,
                        updated_at = ?
                    WHERE task_id = ?
                """, (
                    workflow_type,
                    current_state,
                    json.dumps(state_data),
                    now,
                    task_id
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO workflow_state
                    (task_id, workflow_type, current_state, state_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    workflow_type,
                    current_state,
                    json.dumps(state_data),
                    now,
                    now
                ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    async def get_workflow_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current workflow state

        Args:
            task_id: ID of the workflow task

        Returns:
            Dictionary containing workflow state, or None if not found

        Example:
            state = await state_manager.get_workflow_state("task_001")
            if state:
                print(f"State: {state['current_state']}")
                print(f"Type: {state['workflow_type']}")
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_workflow_state_sync,
            task_id
        )

    def _get_workflow_state_sync(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous implementation of get_workflow_state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT workflow_type, current_state, state_data, created_at, updated_at
                FROM workflow_state
                WHERE task_id = ?
            """, (task_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'task_id': task_id,
                'workflow_type': row[0],
                'current_state': row[1],
                'state_data': json.loads(row[2]),
                'created_at': row[3],
                'updated_at': row[4]
            }

        finally:
            conn.close()

    async def get_execution_log(
        self,
        task_id: str,
        event_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve execution log entries for a task

        Args:
            task_id: ID of the task
            event_type: Optional filter by event type
            limit: Optional maximum number of entries to return

        Returns:
            List of log entries, most recent first

        Example:
            # Get all logs
            logs = await state_manager.get_execution_log("task_001")

            # Get only errors
            errors = await state_manager.get_execution_log(
                "task_001",
                event_type="error"
            )

            # Get last 10 entries
            recent = await state_manager.get_execution_log(
                "task_001",
                limit=10
            )
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_execution_log_sync,
            task_id,
            event_type,
            limit
        )

    def _get_execution_log_sync(
        self,
        task_id: str,
        event_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous implementation of get_execution_log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
                SELECT log_id, event_type, event_data, timestamp
                FROM execution_log
                WHERE task_id = ?
            """
            params = [task_id]

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            query += " ORDER BY timestamp DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)

            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'log_id': row[0],
                    'task_id': task_id,
                    'event_type': row[1],
                    'event_data': json.loads(row[2]),
                    'timestamp': row[3]
                })

            return logs

        finally:
            conn.close()
