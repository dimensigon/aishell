"""
SQL Impact Estimator

Estimates the number of affected rows for SQL commands.
Provides mock estimation with ±20% accuracy target for various SQL operations.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import random


logger = logging.getLogger(__name__)


class OperationType(Enum):
    """SQL operation types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    TRUNCATE = "TRUNCATE"
    UNKNOWN = "UNKNOWN"


class ImpactEstimator:
    """
    Estimates the impact of SQL commands on database rows.

    This is a mock implementation that provides realistic estimations
    for demonstration purposes. In production, this would connect to
    actual database statistics.

    Features:
    - Parse SQL operations (SELECT/UPDATE/DELETE/INSERT)
    - Estimate affected rows with confidence level
    - Mock estimation with ±20% accuracy target
    - Async-compatible interface

    Attributes:
        mock_table_sizes: Dictionary of table names to row counts (for testing)
        default_table_size: Default row count for unknown tables
    """

    def __init__(
        self,
        mock_table_sizes: Optional[Dict[str, int]] = None,
        default_table_size: int = 1000
    ):
        """
        Initialize the impact estimator.

        Args:
            mock_table_sizes: Optional dictionary of table sizes for testing
            default_table_size: Default row count for unknown tables
        """
        self.mock_table_sizes = mock_table_sizes or {
            'users': 50000,
            'orders': 150000,
            'products': 5000,
            'customers': 30000,
            'transactions': 200000,
            'logs': 1000000,
            'sessions': 80000,
            'inventory': 10000,
        }
        self.default_table_size = default_table_size

    async def estimate_impact(
        self,
        sql: str,
        db_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate the impact of a SQL command.

        Args:
            sql: SQL command to analyze
            db_config: Optional database configuration (not used in mock)

        Returns:
            Dictionary with:
            - estimated_rows: Estimated number of affected rows
            - confidence: Confidence level (0.0 - 1.0)
            - operation_type: Type of SQL operation
            - table_name: Affected table name (if detected)
            - has_where_clause: Whether command has WHERE clause
            - is_safe: Whether operation is considered safe
        """
        sql = sql.strip()

        # Parse the SQL command
        operation_type = self._detect_operation_type(sql)
        table_name = self._extract_table_name(sql, operation_type)
        has_where_clause = self._has_where_clause(sql)

        # Get table size
        table_size = self.mock_table_sizes.get(
            table_name.lower() if table_name else '',
            self.default_table_size
        )

        # Estimate affected rows and confidence
        estimated_rows, confidence = self._estimate_rows(
            operation_type,
            table_size,
            has_where_clause,
            sql
        )

        # Determine safety
        is_safe = self._is_safe_operation(
            operation_type,
            estimated_rows,
            has_where_clause
        )

        result = {
            'estimated_rows': estimated_rows,
            'confidence': confidence,
            'operation_type': operation_type.value,
            'table_name': table_name or 'unknown',
            'has_where_clause': has_where_clause,
            'is_safe': is_safe,
            'table_size': table_size
        }

        logger.debug(
            f"Impact estimation: {operation_type.value} on {table_name} - "
            f"~{estimated_rows} rows (confidence: {confidence:.0%})"
        )

        return result

    def _detect_operation_type(self, sql: str) -> OperationType:
        """
        Detect the type of SQL operation.

        Args:
            sql: SQL command

        Returns:
            OperationType enum value
        """
        sql_upper = sql.upper().strip()

        if sql_upper.startswith('SELECT'):
            return OperationType.SELECT
        elif sql_upper.startswith('INSERT'):
            return OperationType.INSERT
        elif sql_upper.startswith('UPDATE'):
            return OperationType.UPDATE
        elif sql_upper.startswith('DELETE'):
            return OperationType.DELETE
        elif sql_upper.startswith('CREATE'):
            return OperationType.CREATE
        elif sql_upper.startswith('DROP'):
            return OperationType.DROP
        elif sql_upper.startswith('ALTER'):
            return OperationType.ALTER
        elif sql_upper.startswith('TRUNCATE'):
            return OperationType.TRUNCATE
        else:
            return OperationType.UNKNOWN

    def _extract_table_name(
        self,
        sql: str,
        operation_type: OperationType
    ) -> Optional[str]:
        """
        Extract table name from SQL command.

        Args:
            sql: SQL command
            operation_type: Detected operation type

        Returns:
            Table name or None if not found
        """
        patterns = {
            OperationType.SELECT: r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            OperationType.INSERT: r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            OperationType.UPDATE: r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            OperationType.DELETE: r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            OperationType.TRUNCATE: r'TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            OperationType.DROP: r'TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            OperationType.ALTER: r'TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        }

        pattern = patterns.get(operation_type)
        if not pattern:
            return None

        match = re.search(pattern, sql, re.IGNORECASE)
        return match.group(1) if match else None

    def _has_where_clause(self, sql: str) -> bool:
        """
        Check if SQL command has a WHERE clause.

        Args:
            sql: SQL command

        Returns:
            True if WHERE clause is present
        """
        return bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))

    def _estimate_rows(
        self,
        operation_type: OperationType,
        table_size: int,
        has_where_clause: bool,
        sql: str
    ) -> Tuple[int, float]:
        """
        Estimate number of affected rows and confidence.

        Args:
            operation_type: Type of SQL operation
            table_size: Size of the target table
            has_where_clause: Whether command has WHERE clause
            sql: SQL command (for additional analysis)

        Returns:
            Tuple of (estimated_rows, confidence)
            Confidence is between 0.0 and 1.0
        """
        # Default estimation
        estimated_rows = 0
        confidence = 0.5

        if operation_type == OperationType.SELECT:
            if has_where_clause:
                # WHERE clause - estimate partial result
                estimated_rows = self._estimate_where_selectivity(sql, table_size)
                confidence = 0.7
            else:
                # No WHERE - full table scan
                estimated_rows = table_size
                confidence = 0.9

        elif operation_type == OperationType.INSERT:
            # INSERT typically affects 1 row (or batch)
            if 'VALUES' in sql.upper():
                # Count number of value sets
                value_count = sql.upper().count('VALUES')
                estimated_rows = value_count
                confidence = 0.95
            else:
                # INSERT ... SELECT
                estimated_rows = int(table_size * 0.1)  # Estimate 10% of table
                confidence = 0.5

        elif operation_type == OperationType.UPDATE:
            if has_where_clause:
                estimated_rows = self._estimate_where_selectivity(sql, table_size)
                confidence = 0.7
            else:
                # No WHERE - affects entire table
                estimated_rows = table_size
                confidence = 0.95

        elif operation_type == OperationType.DELETE:
            if has_where_clause:
                estimated_rows = self._estimate_where_selectivity(sql, table_size)
                confidence = 0.7
            else:
                # No WHERE - deletes entire table
                estimated_rows = table_size
                confidence = 0.95

        elif operation_type in [OperationType.TRUNCATE, OperationType.DROP]:
            # These operations affect entire table
            estimated_rows = table_size
            confidence = 1.0

        elif operation_type == OperationType.ALTER:
            # ALTER affects table structure, not rows
            estimated_rows = 0
            confidence = 0.9

        # Add variance to simulate ±20% accuracy
        if estimated_rows > 0:
            variance = random.uniform(-0.2, 0.2)
            estimated_rows = int(estimated_rows * (1 + variance))
            estimated_rows = max(1, estimated_rows)  # Ensure at least 1 for operations that affect rows

        return estimated_rows, confidence

    def _estimate_where_selectivity(self, sql: str, table_size: int) -> int:
        """
        Estimate selectivity of WHERE clause.

        This is a simplified heuristic-based estimation.

        Args:
            sql: SQL command
            table_size: Size of the target table

        Returns:
            Estimated number of rows affected
        """
        # Default selectivity: 10% of table
        selectivity = 0.1

        sql_upper = sql.upper()

        # Check for equality conditions (high selectivity)
        if re.search(r'=\s*[\'"]?\w+[\'"]?', sql):
            selectivity = 0.01  # 1% of table

        # Check for LIKE with wildcards (lower selectivity)
        elif 'LIKE' in sql_upper:
            selectivity = 0.15  # 15% of table

        # Check for range conditions (medium selectivity)
        elif any(op in sql_upper for op in ['BETWEEN', '>', '<', '>=', '<=']):
            selectivity = 0.25  # 25% of table

        # Check for IN clause
        elif 'IN' in sql_upper:
            # Count items in IN clause
            in_match = re.search(r'IN\s*\(([^)]+)\)', sql, re.IGNORECASE)
            if in_match:
                items = in_match.group(1).split(',')
                selectivity = min(len(items) * 0.01, 0.3)  # 1% per item, max 30%

        # Multiple conditions with AND (higher selectivity)
        and_count = sql_upper.count(' AND ')
        if and_count > 0:
            selectivity *= (0.5 ** and_count)  # Each AND reduces by 50%

        # Multiple conditions with OR (lower selectivity)
        or_count = sql_upper.count(' OR ')
        if or_count > 0:
            selectivity *= (1.5 ** or_count)  # Each OR increases by 50%

        selectivity = min(selectivity, 1.0)  # Cap at 100%
        estimated_rows = int(table_size * selectivity)

        return max(1, estimated_rows)  # At least 1 row

    def _is_safe_operation(
        self,
        operation_type: OperationType,
        estimated_rows: int,
        has_where_clause: bool
    ) -> bool:
        """
        Determine if operation is considered safe.

        Args:
            operation_type: Type of SQL operation
            estimated_rows: Estimated affected rows
            has_where_clause: Whether command has WHERE clause

        Returns:
            True if operation is safe
        """
        # SELECT is always safe
        if operation_type == OperationType.SELECT:
            return True

        # CREATE is generally safe
        if operation_type == OperationType.CREATE:
            return True

        # INSERT is safe if not too many rows
        if operation_type == OperationType.INSERT:
            return estimated_rows < 1000

        # UPDATE/DELETE safe if has WHERE and affects < 1000 rows
        if operation_type in [OperationType.UPDATE, OperationType.DELETE]:
            return has_where_clause and estimated_rows < 1000

        # DROP, TRUNCATE, ALTER are risky
        if operation_type in [OperationType.DROP, OperationType.TRUNCATE, OperationType.ALTER]:
            return False

        return True

    def get_table_size(self, table_name: str) -> int:
        """
        Get the size of a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        return self.mock_table_sizes.get(
            table_name.lower(),
            self.default_table_size
        )

    def set_table_size(self, table_name: str, size: int) -> None:
        """
        Set the size of a table (for testing).

        Args:
            table_name: Name of the table
            size: Number of rows
        """
        self.mock_table_sizes[table_name.lower()] = size
