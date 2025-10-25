"""Database module with unified interface for SQL operations."""

from typing import Dict, List, Optional, Any
import sqlite3
from pathlib import Path

from .risk_analyzer import SQLRiskAnalyzer, RiskLevel
from .nlp_to_sql import NLPToSQL
from .history import SQLHistoryManager


class DatabaseModule:
    """Unified database module for AI-Shell."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        history_file: Optional[str] = None,
        auto_confirm: bool = False,
    ):
        """Initialize the database module.

        Args:
            db_path: Path to SQLite database. If None, uses in-memory database.
            history_file: Path to history file. If None, uses default location.
            auto_confirm: If True, skip confirmations for risky queries (use with caution)
        """
        self.db_path = db_path or ':memory:'
        self.auto_confirm = auto_confirm

        # Initialize components
        self.risk_analyzer = SQLRiskAnalyzer()
        self.nlp_converter = NLPToSQL()
        self.history = SQLHistoryManager(history_file)

        # Database connection
        self.connection = None
        self._connect()

    def _connect(self):
        """Establish database connection."""
        if self.connection:
            self.connection.close()

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable column name access

    def execute_sql(
        self,
        sql: str,
        params: Optional[tuple] = None,
        skip_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """Execute SQL query with risk analysis and history tracking.

        Args:
            sql: SQL query to execute
            params: Query parameters for parameterized queries
            skip_confirmation: Skip confirmation even for risky queries

        Returns:
            Dict containing execution results and metadata
        """
        import time

        # Analyze risk
        analysis = self.risk_analyzer.analyze(sql)

        # Check if confirmation is needed
        if analysis['requires_confirmation'] and not (self.auto_confirm or skip_confirmation):
            return {
                'status': 'requires_confirmation',
                'analysis': analysis,
                'confirmation_message': self.risk_analyzer.get_confirmation_message(analysis),
            }

        # Execute query
        start_time = time.time()
        cursor = self.connection.cursor()

        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # Commit if needed
            if analysis['risk_level'] != RiskLevel.LOW.value:
                self.connection.commit()

            # Get results
            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                rows_affected = len(results)
            else:
                results = None
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    self.connection.commit()

            execution_time = time.time() - start_time

            # Add to history
            self.history.add_entry(
                sql=sql,
                risk_level=analysis['risk_level'],
                success=True,
                rows_affected=rows_affected,
                execution_time=execution_time,
            )

            return {
                'status': 'success',
                'results': results,
                'rows_affected': rows_affected,
                'execution_time': execution_time,
                'analysis': analysis,
            }

        except sqlite3.Error as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            # Add to history
            self.history.add_entry(
                sql=sql,
                risk_level=analysis['risk_level'],
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

            return {
                'status': 'error',
                'error': error_msg,
                'execution_time': execution_time,
                'analysis': analysis,
            }

        finally:
            cursor.close()

    def execute_nlp(self, nlp_query: str) -> Dict[str, Any]:
        """Execute natural language query.

        Args:
            nlp_query: Natural language query

        Returns:
            Dict containing execution results
        """
        # Convert NLP to SQL
        conversion = self.nlp_converter.convert(nlp_query)

        if not conversion['sql']:
            return {
                'status': 'conversion_failed',
                'conversion': conversion,
            }

        # Execute converted SQL
        result = self.execute_sql(conversion['sql'])
        result['conversion'] = conversion

        return result

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent query history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent history entries
        """
        return self.history.get_recent(limit)

    def get_statistics(self) -> Dict[str, Any]:
        """Get query statistics.

        Returns:
            Dict containing statistics
        """
        return self.history.get_statistics()

    def search_history(self, keyword: str) -> List[Dict]:
        """Search query history.

        Args:
            keyword: Keyword to search for

        Returns:
            List of matching history entries
        """
        return self.history.search(keyword)

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
