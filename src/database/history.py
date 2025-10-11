"""SQL history manager for tracking executed queries."""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from pathlib import Path


class SQLHistoryManager:
    """Manages history of executed SQL queries."""

    def __init__(self, history_file: Optional[str] = None) -> None:
        """Initialize the history manager.

        Args:
            history_file: Path to history file. If None, uses default location.
        """
        if history_file:
            self.history_file = Path(history_file)
        else:
            # Default to user's home directory
            home = Path.home()
            self.history_file = home / '.ai_shell' / 'sql_history.json'

        # Ensure directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file.

        Returns:
            List of history entries
        """
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, 'r') as f:
                data: List[Dict[str, Any]] = json.load(f)
                return data
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, start fresh
            return []

    def _save_history(self) -> None:
        """Save history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save history: {e}")

    def add_entry(
        self,
        sql: str,
        risk_level: str,
        success: bool,
        rows_affected: Optional[int] = None,
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
    ) -> None:
        """Add a query to history.

        Args:
            sql: SQL query executed
            risk_level: Risk level of the query
            success: Whether execution was successful
            rows_affected: Number of rows affected (if applicable)
            error: Error message (if failed)
            execution_time: Execution time in seconds
        """
        entry: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'sql': sql,
            'risk_level': risk_level,
            'success': success,
        }

        if rows_affected is not None:
            entry['rows_affected'] = rows_affected

        if error:
            entry['error'] = error

        if execution_time is not None:
            entry['execution_time'] = execution_time

        self.history.append(entry)
        self._save_history()

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent history entries
        """
        return self.history[-limit:][::-1]  # Most recent first

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """Search history for queries containing keyword.

        Args:
            keyword: Keyword to search for

        Returns:
            List of matching history entries
        """
        keyword = keyword.lower()
        return [
            entry for entry in self.history
            if keyword in entry['sql'].lower()
        ]

    def get_by_risk_level(self, risk_level: str) -> List[Dict[str, Any]]:
        """Get queries by risk level.

        Args:
            risk_level: Risk level to filter by

        Returns:
            List of history entries with specified risk level
        """
        return [
            entry for entry in self.history
            if entry['risk_level'] == risk_level
        ]

    def get_failed_queries(self) -> List[Dict[str, Any]]:
        """Get all failed queries.

        Returns:
            List of failed query entries
        """
        return [
            entry for entry in self.history
            if not entry.get('success', False)
        ]

    def clear(self) -> None:
        """Clear all history."""
        self.history = []
        self._save_history()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about query history.

        Returns:
            Dict containing various statistics
        """
        if not self.history:
            return {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'risk_level_distribution': {},
            }

        total = len(self.history)
        successful = sum(1 for e in self.history if e.get('success', False))

        # Risk level distribution
        risk_dist: Dict[str, int] = {}
        for entry in self.history:
            level = entry.get('risk_level', 'UNKNOWN')
            risk_dist[level] = risk_dist.get(level, 0) + 1

        return {
            'total_queries': total,
            'successful_queries': successful,
            'failed_queries': total - successful,
            'risk_level_distribution': risk_dist,
            'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
        }
