"""
Query Optimization Engine

Provides query analysis, optimization suggestions, and performance improvements
for SQL queries across different database systems.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add performance module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from performance.cache import QueryCache

# Import N+1 detector
try:
    from .n_plus_one_detector import NPlusOneDetector
except ImportError:
    from n_plus_one_detector import NPlusOneDetector


class OptimizationLevel(Enum):
    """Optimization severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class OptimizationType(Enum):
    """Types of optimization suggestions"""
    MISSING_INDEX = "missing_index"
    FULL_TABLE_SCAN = "full_table_scan"
    QUERY_REWRITE = "query_rewrite"
    INEFFICIENT_JOIN = "inefficient_join"
    SUBQUERY_OPTIMIZATION = "subquery_optimization"
    MISSING_WHERE = "missing_where"
    SELECT_STAR = "select_star"
    MISSING_LIMIT = "missing_limit"
    CARTESIAN_PRODUCT = "cartesian_product"
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
    details: Optional[Dict[str, Any]] = None


class QueryOptimizer:
    """
    Query optimization engine with pattern-based analysis and caching.

    Detects common performance issues and suggests improvements.
    """

    def __init__(self, database_type: str = 'postgresql'):
        """
        Initialize query optimizer with cache integration.

        Args:
            database_type: Target database type (postgresql, mysql, oracle)
        """
        self.database_type = database_type.lower()
        # Initialize query cache with 5 minute TTL
        self.cache = QueryCache(ttl=300)

        # Pre-compile regex patterns for better performance
        self._select_star_pattern = re.compile(r'SELECT\s+\*\s+FROM', re.IGNORECASE)
        self._like_leading_wildcard_pattern = re.compile(r"LIKE\s+['\"]%", re.IGNORECASE)
        self._function_in_where_pattern = re.compile(r'WHERE\s+\w+\s*\((\w+)\)', re.IGNORECASE)

        # Initialize N+1 detector
        self.n_plus_one_detector = NPlusOneDetector()

    def analyze_query(self, query: str) -> List[OptimizationSuggestion]:
        """
        Analyze query for optimization opportunities with caching.

        Args:
            query: SQL query string

        Returns:
            List of optimization suggestions
        """
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        suggestions = []
        query_clean = query.strip()
        query_upper = query_clean.upper()

        # Check for SELECT *
        suggestions.extend(self._check_select_star(query_clean, query_upper))

        # Check for missing WHERE clause
        suggestions.extend(self._check_missing_where(query_clean, query_upper))

        # Check for missing indexes
        suggestions.extend(self._check_missing_indexes(query_clean, query_upper))

        # Check for full table scans
        suggestions.extend(self._check_full_table_scan(query_clean, query_upper))

        # Check for inefficient joins
        suggestions.extend(self._check_inefficient_joins(query_clean, query_upper))

        # Check for subquery optimization
        suggestions.extend(self._check_subquery_optimization(query_clean, query_upper))

        # Check for missing LIMIT
        suggestions.extend(self._check_missing_limit(query_clean, query_upper))

        # Check for Cartesian products
        suggestions.extend(self._check_cartesian_product(query_clean, query_upper))

        # Cache the result with extended TTL (10 minutes)
        self.cache.set(cache_key, suggestions, ttl=600)

        return suggestions

    def _check_select_star(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Check for SELECT * usage with pre-compiled regex"""
        suggestions = []

        if self._select_star_pattern.search(query):
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.SELECT_STAR,
                level=OptimizationLevel.WARNING,
                message="Using SELECT * can be inefficient. Specify only required columns.",
                original_query=query,
                suggested_query=None,
                estimated_improvement="10-30% faster query execution",
                explanation="SELECT * retrieves all columns, increasing network transfer and memory usage. "
                           "Specifying only needed columns reduces data transfer and improves cache efficiency."
            ))

        return suggestions

    def _check_missing_where(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Check for queries without WHERE clause"""
        suggestions = []

        # Check if it's a SELECT, UPDATE, or DELETE without WHERE
        if re.search(r'(SELECT|DELETE).*FROM', query_upper):
            if 'WHERE' not in query_upper:
                level = OptimizationLevel.CRITICAL if 'DELETE' in query_upper else OptimizationLevel.WARNING

                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.MISSING_WHERE,
                    level=level,
                    message="Query without WHERE clause will scan entire table.",
                    original_query=query,
                    suggested_query=None,
                    estimated_improvement="Could be 100x+ faster with proper WHERE clause",
                    explanation="Without a WHERE clause, the database must scan all rows. "
                               "Add filtering conditions to limit the result set."
                ))

        # Check for UPDATE without WHERE separately
        if re.match(r'UPDATE\s+\w+\s+SET', query_upper) and 'WHERE' not in query_upper:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.MISSING_WHERE,
                level=OptimizationLevel.CRITICAL,
                message="UPDATE without WHERE clause will modify all rows!",
                original_query=query,
                suggested_query=None,
                estimated_improvement="Add WHERE clause to prevent unintended updates",
                explanation="UPDATE without WHERE modifies every row in the table. "
                           "This is usually unintentional and can cause data loss."
            ))

        return suggestions

    def _check_missing_indexes(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Detect potential missing indexes"""
        suggestions = []

        # Look for WHERE clause columns
        where_match = re.search(r'WHERE\s+(\w+)', query_upper)
        if where_match:
            column = where_match.group(1)

            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.MISSING_INDEX,
                level=OptimizationLevel.INFO,
                message=f"Consider adding an index on column '{column}' used in WHERE clause.",
                original_query=query,
                suggested_query=self._generate_index_suggestion(column, query),
                estimated_improvement="10-1000x faster depending on table size",
                explanation=f"Queries filtering on '{column}' could benefit from an index. "
                           "Indexes allow the database to quickly locate rows instead of scanning the entire table."
            ))

        # Check for JOIN conditions
        join_matches = re.finditer(r'JOIN\s+\w+\s+ON\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)', query_upper)
        for match in join_matches:
            col1, col2 = match.groups()
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.MISSING_INDEX,
                level=OptimizationLevel.WARNING,
                message=f"Consider indexes on JOIN columns: {col1}, {col2}",
                original_query=query,
                suggested_query=f"-- Consider:\n-- CREATE INDEX idx_{col1} ON table_name({col1});\n-- CREATE INDEX idx_{col2} ON table_name({col2});",
                estimated_improvement="Significantly faster JOIN operations",
                explanation="JOIN operations benefit greatly from indexes on the join columns."
            ))

        return suggestions

    def _check_full_table_scan(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Detect queries likely to cause full table scans with pre-compiled regex"""
        suggestions = []

        # Check for LIKE with leading wildcard
        if self._like_leading_wildcard_pattern.search(query):
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.FULL_TABLE_SCAN,
                level=OptimizationLevel.WARNING,
                message="LIKE with leading wildcard (LIKE '%...') forces full table scan.",
                original_query=query,
                suggested_query=None,
                estimated_improvement="Consider full-text search or alternative patterns",
                explanation="Leading wildcards prevent index usage. Use trailing wildcards (LIKE 'text%') when possible, "
                           "or consider full-text search for better performance."
            ))

        # Check for function calls on indexed columns
        if self._function_in_where_pattern.search(query):
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.FULL_TABLE_SCAN,
                level=OptimizationLevel.WARNING,
                message="Functions on columns in WHERE clause prevent index usage.",
                original_query=query,
                suggested_query=None,
                estimated_improvement="Rewrite to allow index usage",
                explanation="Functions applied to columns prevent index usage. "
                           "Consider computed columns, function-based indexes, or query rewriting."
            ))

        return suggestions

    def _check_inefficient_joins(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Check for inefficient JOIN patterns"""
        suggestions = []

        # Count number of joins
        join_count = len(re.findall(r'\bJOIN\b', query_upper))

        if join_count > 5:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.INEFFICIENT_JOIN,
                level=OptimizationLevel.WARNING,
                message=f"Query has {join_count} JOINs. Consider query redesign or denormalization.",
                original_query=query,
                suggested_query=None,
                estimated_improvement="Consider breaking into multiple queries or materialized views",
                explanation="Complex queries with many JOINs can be slow. "
                           "Consider denormalization, materialized views, or breaking into smaller queries."
            ))

        # Check for OUTER JOIN that could be INNER JOIN
        if 'LEFT OUTER JOIN' in query_upper or 'RIGHT OUTER JOIN' in query_upper:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.INEFFICIENT_JOIN,
                level=OptimizationLevel.INFO,
                message="Verify if OUTER JOIN is necessary. INNER JOIN is typically faster.",
                original_query=query,
                suggested_query=None,
                estimated_improvement="INNER JOIN can be 2-10x faster than OUTER JOIN",
                explanation="OUTER JOINs are more expensive than INNER JOINs. "
                           "Use INNER JOIN when you don't need unmatched rows."
            ))

        return suggestions

    def _check_subquery_optimization(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Check for subquery optimization opportunities"""
        suggestions = []

        # Check for IN subquery
        if re.search(r'IN\s*\(SELECT', query_upper):
            suggested = re.sub(
                r'IN\s*\(SELECT.*?\)',
                'EXISTS (SELECT 1 FROM ...)',
                query,
                flags=re.IGNORECASE
            )

            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.SUBQUERY_OPTIMIZATION,
                level=OptimizationLevel.WARNING,
                message="IN subquery can often be replaced with EXISTS or JOIN for better performance.",
                original_query=query,
                suggested_query=f"-- Consider using EXISTS instead:\n-- {suggested}",
                estimated_improvement="2-10x faster for large datasets",
                explanation="EXISTS stops at the first match, while IN evaluates all results. "
                           "Consider JOIN for even better performance when appropriate."
            ))

        # Check for correlated subqueries
        subquery_count = len(re.findall(r'\(SELECT.*?\)', query_upper))
        if subquery_count > 0:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.SUBQUERY_OPTIMIZATION,
                level=OptimizationLevel.INFO,
                message="Subqueries detected. Consider JOINs or CTEs for better readability and potential performance.",
                original_query=query,
                suggested_query="-- Consider rewriting with JOIN or WITH clause (CTE)",
                estimated_improvement="Variable, but often more maintainable",
                explanation="Common Table Expressions (CTEs) improve readability and can be optimized by the query planner."
            ))

        return suggestions

    def _check_missing_limit(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Check for SELECT queries without LIMIT"""
        suggestions = []

        if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper and 'TOP' not in query_upper:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.MISSING_LIMIT,
                level=OptimizationLevel.INFO,
                message="SELECT query without LIMIT. Consider limiting results for better performance.",
                original_query=query,
                suggested_query=f"{query.rstrip(';')} LIMIT 100;",
                estimated_improvement="Prevents excessive data transfer",
                explanation="Without LIMIT, queries return all matching rows. "
                           "For exploratory queries or UI pagination, add LIMIT to reduce data transfer."
            ))

        return suggestions

    def _check_cartesian_product(self, query: str, query_upper: str) -> List[OptimizationSuggestion]:
        """Check for potential Cartesian products"""
        suggestions = []

        # Check for multiple tables in FROM without JOIN
        from_match = re.search(r'FROM\s+([\w\s,]+?)(?:WHERE|GROUP|ORDER|LIMIT|$)', query_upper)
        if from_match:
            tables = [t.strip() for t in from_match.group(1).split(',')]
            if len(tables) > 1 and 'JOIN' not in query_upper:
                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.CARTESIAN_PRODUCT,
                    level=OptimizationLevel.CRITICAL,
                    message=f"Potential Cartesian product: {len(tables)} tables without explicit JOIN.",
                    original_query=query,
                    suggested_query="-- Rewrite using explicit JOIN syntax",
                    estimated_improvement="Can be 100-1000x+ faster with proper JOINs",
                    explanation="Cartesian products multiply row counts exponentially. "
                               "Always use explicit JOIN conditions."
                ))

        return suggestions

    def _generate_index_suggestion(self, column: str, query: str) -> str:
        """Generate index creation suggestion"""
        # Extract table name
        table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        table_name = table_match.group(1) if table_match else 'table_name'

        if self.database_type == 'mysql':
            return f"CREATE INDEX idx_{column} ON {table_name}({column});"
        elif self.database_type == 'postgresql':
            return f"CREATE INDEX idx_{column} ON {table_name}({column});"
        elif self.database_type == 'oracle':
            return f"CREATE INDEX idx_{column} ON {table_name}({column});"
        else:
            return f"CREATE INDEX idx_{column} ON {table_name}({column});"

    def analyze_explain_plan(self, explain_output: str) -> List[OptimizationSuggestion]:
        """
        Analyze EXPLAIN plan output for optimization opportunities

        Args:
            explain_output: EXPLAIN output from database

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Check for Seq Scan (PostgreSQL)
        if 'Seq Scan' in explain_output:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.FULL_TABLE_SCAN,
                level=OptimizationLevel.WARNING,
                message="Sequential scan detected. Consider adding appropriate indexes.",
                original_query="",
                estimated_improvement="Index scan can be 10-1000x faster",
                explanation="Sequential scans read entire tables. Indexes allow direct row access."
            ))

        # Check for high cost
        cost_match = re.search(r'cost=[\d.]+\.\.([\d.]+)', explain_output)
        if cost_match:
            cost = float(cost_match.group(1))
            if cost > 10000:
                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.QUERY_REWRITE,
                    level=OptimizationLevel.WARNING,
                    message=f"High query cost detected ({cost:.2f}). Consider optimization.",
                    original_query="",
                    estimated_improvement="Various optimization strategies available",
                    explanation="High cost indicates expensive operations. Review indexes, joins, and query structure."
                ))

        return suggestions

    def get_optimization_report(self, query: str, explain_output: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive optimization report

        Args:
            query: SQL query string
            explain_output: Optional EXPLAIN plan output

        Returns:
            Dictionary with optimization report
        """
        query_suggestions = self.analyze_query(query)
        explain_suggestions = self.analyze_explain_plan(explain_output) if explain_output else []

        all_suggestions = query_suggestions + explain_suggestions

        # Categorize by level
        critical = [s for s in all_suggestions if s.level == OptimizationLevel.CRITICAL]
        warnings = [s for s in all_suggestions if s.level == OptimizationLevel.WARNING]
        info = [s for s in all_suggestions if s.level == OptimizationLevel.INFO]

        return {
            'query': query,
            'total_suggestions': len(all_suggestions),
            'critical_issues': len(critical),
            'warnings': len(warnings),
            'info': len(info),
            'suggestions': {
                'critical': [self._suggestion_to_dict(s) for s in critical],
                'warning': [self._suggestion_to_dict(s) for s in warnings],
                'info': [self._suggestion_to_dict(s) for s in info]
            },
            'optimization_score': self._calculate_score(all_suggestions)
        }

    def _suggestion_to_dict(self, suggestion: OptimizationSuggestion) -> Dict[str, Any]:
        """Convert suggestion to dictionary"""
        return {
            'type': suggestion.type.value,
            'level': suggestion.level.value,
            'message': suggestion.message,
            'suggested_query': suggestion.suggested_query,
            'estimated_improvement': suggestion.estimated_improvement,
            'explanation': suggestion.explanation
        }

    def _calculate_score(self, suggestions: List[OptimizationSuggestion]) -> float:
        """Calculate optimization score (0-100, higher is better)"""
        if not suggestions:
            return 100.0

        # Weight by severity
        penalty = sum([
            15 for s in suggestions if s.level == OptimizationLevel.CRITICAL
        ] + [
            5 for s in suggestions if s.level == OptimizationLevel.WARNING
        ] + [
            1 for s in suggestions if s.level == OptimizationLevel.INFO
        ])

        score = max(0, 100 - penalty)
        return score

    def analyze_query_log(
        self,
        query_log: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """
        Analyze query log for N+1 patterns and other issues.

        Args:
            query_log: List of executed queries with timestamps
                Format: [{'query': str, 'timestamp': float, 'params': list}, ...]

        Returns:
            List of optimization suggestions including N+1 detections
        """
        return self.n_plus_one_detector.detect_n_plus_one(query_log)

    def analyze_query_log_file(self, log_file_path: str) -> List[OptimizationSuggestion]:
        """
        Analyze query log from file for N+1 patterns.

        Args:
            log_file_path: Path to JSON file containing query log

        Returns:
            List of optimization suggestions
        """
        with open(log_file_path, 'r') as f:
            query_log = json.load(f)

        return self.analyze_query_log(query_log)

    def detect_n_plus_one(
        self,
        query_log: List[Dict[str, Any]],
        time_window_ms: Optional[int] = None,
        threshold: Optional[int] = None
    ) -> List[OptimizationSuggestion]:
        """
        Detect N+1 query patterns from execution log.

        Args:
            query_log: List of executed queries with timestamps
            time_window_ms: Optional custom time window (default 1000ms)
            threshold: Optional custom threshold (default 10 queries)

        Returns:
            List of N+1 optimization suggestions
        """
        if time_window_ms is not None or threshold is not None:
            # Create custom detector with specified parameters
            detector = NPlusOneDetector(
                time_window_ms=time_window_ms or 1000,
                threshold=threshold or 10
            )
            return detector.detect_n_plus_one(query_log)

        return self.n_plus_one_detector.detect_n_plus_one(query_log)
