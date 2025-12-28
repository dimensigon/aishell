"""
N+1 Query Detection Module

Detects N+1 query patterns that cause performance problems by analyzing
query execution logs for repetitive patterns indicating loop-based queries.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re
from enum import Enum


class OptimizationLevel(Enum):
    """Optimization severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class OptimizationType(Enum):
    """Types of optimization suggestions"""
    N_PLUS_ONE = "n_plus_one"


@dataclass
class OptimizationSuggestion:
    """Represents a query optimization suggestion"""
    type: OptimizationType
    level: OptimizationLevel
    message: str
    original_query: str
    suggested_query: Optional[str] = None
    estimated_improvement: Optional[str] = None
    explanation: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryPattern:
    """Represents a pattern of similar queries"""
    template: str
    count: int = 0
    params_list: List[Any] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)


class NPlusOneDetector:
    """
    Detects N+1 query patterns from execution logs.

    N+1 queries occur when an initial query loads records, then subsequent
    queries load related data in a loop (1 initial query + N queries for each record).

    Example N+1 pattern:
        users = db.query("SELECT * FROM users")          # 1 query
        for user in users:
            orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)  # N queries!

    Better approach:
        results = db.query("SELECT * FROM users JOIN orders ON orders.user_id = users.id")
    """

    def __init__(
        self,
        time_window_ms: int = 1000,
        threshold: int = 10
    ):
        """
        Initialize N+1 detector.

        Args:
            time_window_ms: Time window in milliseconds to consider queries related (default 1s)
            threshold: Minimum number of similar queries to flag as N+1 (default 10)
        """
        self.time_window_ms = time_window_ms
        self.threshold = threshold

    def detect_n_plus_one(
        self,
        query_log: List[Dict[str, Any]],
    ) -> List[OptimizationSuggestion]:
        """
        Detect N+1 query patterns from execution log.

        Args:
            query_log: List of executed queries with timestamps
                Format: [{'query': str, 'timestamp': float, 'params': list}, ...]

        Returns:
            List of optimization suggestions for detected N+1 patterns
        """
        if not query_log:
            return []

        suggestions = []
        patterns: Dict[str, QueryPattern] = defaultdict(
            lambda: QueryPattern('', 0, [], [], [])
        )

        # Step 1: Normalize queries to templates
        for entry in query_log:
            query = entry.get('query', '')
            timestamp = entry.get('timestamp', 0.0)
            params = entry.get('params', [])

            if not query:
                continue

            # Create template by replacing parameters
            template = self._normalize_to_template(query)

            pattern = patterns[template]
            pattern.template = template
            pattern.count += 1
            pattern.params_list.append(params)
            pattern.timestamps.append(timestamp)
            pattern.queries.append(query)

        # Step 2: Analyze patterns for N+1
        for template, pattern in patterns.items():
            if pattern.count < self.threshold:
                continue

            # Check if queries occurred in rapid succession
            if not pattern.timestamps:
                continue

            time_span = max(pattern.timestamps) - min(pattern.timestamps)
            if time_span > self.time_window_ms:
                continue

            # Check if params suggest loop iteration
            if self._params_suggest_loop(pattern.params_list):
                # Extract table name and suggest JOIN
                table_name = self._extract_table_name(template)
                suggested_query = self._suggest_batch_query(template, pattern)

                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.N_PLUS_ONE,
                    level=OptimizationLevel.CRITICAL,
                    message=f"N+1 query detected: {pattern.count} similar queries in {time_span:.0f}ms",
                    original_query=pattern.queries[0],
                    suggested_query=suggested_query,
                    estimated_improvement=f"{pattern.count}x faster with batch loading or JOIN",
                    explanation=(
                        f"Detected {pattern.count} similar queries executing in rapid succession. "
                        f"This is a classic N+1 query problem. Consider:\n"
                        f"1. Use JOINs to fetch related data in a single query\n"
                        f"2. Use batch loading (SELECT ... WHERE id IN (...))\n"
                        f"3. Use eager loading in your ORM\n"
                        f"4. Cache the repeated queries"
                    ),
                    details={
                        'pattern_count': pattern.count,
                        'time_window_ms': time_span,
                        'table': table_name,
                        'sample_params': pattern.params_list[:5]
                    }
                ))

        return suggestions

    def _normalize_to_template(self, query: str) -> str:
        """
        Normalize query to template by replacing parameters.

        Args:
            query: SQL query string

        Returns:
            Normalized template string
        """
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)

        # Replace numeric literals
        query = re.sub(r'\b\d+\b', '?', query)

        # Replace string literals
        query = re.sub(r"'[^']*'", '?', query)
        query = re.sub(r'"[^"]*"', '?', query)

        # Normalize whitespace
        query = ' '.join(query.split())

        return query.upper()

    def _params_suggest_loop(self, params_list: List[Any]) -> bool:
        """
        Check if params suggest loop iteration (e.g., sequential IDs).

        Args:
            params_list: List of parameter lists from multiple queries

        Returns:
            True if parameters suggest loop iteration
        """
        if len(params_list) < 3:
            return False

        # Check for sequential numeric params
        try:
            # Extract first parameter from each query
            first_params = []
            for p in params_list[:min(10, len(params_list))]:
                if isinstance(p, (list, tuple)) and len(p) > 0:
                    first_params.append(p[0])
                elif p is not None:
                    first_params.append(p)

            if not first_params:
                return True  # Conservative: assume loop if we can't determine

            # Check if all are numeric
            if all(isinstance(p, (int, float)) for p in first_params):
                # Check if parameters are sequential or follow a pattern
                diffs = [
                    first_params[i+1] - first_params[i]
                    for i in range(len(first_params)-1)
                ]
                # If differences are consistent, likely sequential
                if len(set(diffs)) <= 2:
                    return True

            # Check for distinct values (likely iterating through a set)
            if len(set(str(p) for p in first_params)) >= len(first_params) * 0.8:
                return True

        except (TypeError, IndexError, ValueError):
            pass

        # If we can't determine, assume loop (conservative)
        return True

    def _extract_table_name(self, template: str) -> str:
        """
        Extract table name from query template.

        Args:
            template: Normalized query template

        Returns:
            Table name or 'unknown'
        """
        # Match FROM clause
        match = re.search(r'FROM\s+(\w+)', template, re.IGNORECASE)
        if match:
            return match.group(1)
        return 'unknown'

    def _suggest_batch_query(
        self,
        template: str,
        pattern: QueryPattern
    ) -> str:
        """
        Generate suggested batch query using IN clause.

        Args:
            template: Normalized query template
            pattern: Query pattern data

        Returns:
            Suggested optimized query
        """
        # Extract WHERE clause condition
        where_match = re.search(
            r'WHERE\s+(\w+)\s*=\s*\?',
            template,
            re.IGNORECASE
        )

        if where_match:
            column = where_match.group(1)
            base_query = template.split('WHERE')[0].strip()

            return (
                f"{base_query}\nWHERE {column} IN (?)\n"
                f"-- Replace ? with array of IDs: [1, 2, 3, ...]\n"
                f"-- This will fetch all results in one query instead of {pattern.count}"
            )

        # Try to suggest JOIN if we can identify pattern
        table_name = self._extract_table_name(template)
        return (
            f"-- Consider using a JOIN to fetch related data:\n"
            f"-- SELECT parent.*, child.*\n"
            f"-- FROM parent_table\n"
            f"-- JOIN {table_name} ON parent_table.id = {table_name}.parent_id\n"
            f"-- This replaces {pattern.count} queries with a single JOIN"
        )


def create_detector(
    time_window_ms: int = 1000,
    threshold: int = 10
) -> NPlusOneDetector:
    """
    Factory function to create N+1 detector.

    Args:
        time_window_ms: Time window in milliseconds (default 1s)
        threshold: Minimum query count to flag (default 10)

    Returns:
        Configured NPlusOneDetector instance
    """
    return NPlusOneDetector(
        time_window_ms=time_window_ms,
        threshold=threshold
    )
