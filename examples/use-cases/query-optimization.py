#!/usr/bin/env python3
"""
Query Optimization Agent for agentic-aishell

This example demonstrates how to build an autonomous agent that:
- Analyzes SQL query performance
- Suggests and applies optimizations
- Generates indexes automatically
- Rewrites inefficient queries
- Monitors query execution plans

Features:
- Passive mode: Suggestions only
- Active mode: Automatic optimization with approval
- Learning mode: Improves based on past optimizations

See examples/use-cases/README.md for full documentation.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizationMode(Enum):
    """Optimization agent modes"""
    PASSIVE = "passive"      # Suggestions only
    ACTIVE = "active"        # Auto-optimize with approval
    LEARNING = "learning"    # Learn from past optimizations


@dataclass
class QueryAnalysis:
    """Query performance analysis"""
    query: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    index_used: Optional[str]
    issues: List[str]
    optimization_score: float  # 0-100


@dataclass
class OptimizationSuggestion:
    """Query optimization suggestion"""
    query: str
    issue: str
    suggestion: str
    optimized_query: Optional[str]
    estimated_improvement: float  # percentage
    confidence: float  # 0-1


class QueryOptimizationAgent:
    """
    Autonomous query optimization agent.

    Features:
    - Analyzes query execution plans
    - Detects performance anti-patterns
    - Suggests optimizations
    - Can automatically apply improvements
    - Learns from optimization results
    """

    def __init__(self, mode: OptimizationMode = OptimizationMode.PASSIVE):
        """
        Initialize optimization agent.

        Args:
            mode: Agent operation mode
        """
        self.mode = mode
        self.optimization_history: List[Dict] = []
        self.index_recommendations: List[str] = []

    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a SQL query for performance issues.

        Args:
            query: SQL query to analyze

        Returns:
            QueryAnalysis with findings
        """
        logger.info(f"Analyzing query: {query[:100]}...")

        # Simulate query execution analysis
        # In production, use EXPLAIN ANALYZE
        issues = []

        # Check for common anti-patterns
        if 'SELECT *' in query.upper():
            issues.append("SELECT * returns unnecessary columns")

        if 'WHERE' not in query.upper() and 'FROM' in query.upper():
            issues.append("No WHERE clause - full table scan")

        if re.search(r'OR\s+\w+\s*=', query, re.IGNORECASE):
            issues.append("OR conditions prevent index usage")

        if 'LIKE' in query.upper() and re.search(r"LIKE\s+'%", query, re.IGNORECASE):
            issues.append("Leading wildcard LIKE prevents index usage")

        if re.search(r'ORDER BY.*LIMIT', query, re.IGNORECASE) and 'INDEX' not in query.upper():
            issues.append("ORDER BY with LIMIT may need index")

        # Calculate optimization score (inverse of issues)
        score = max(0, 100 - (len(issues) * 20))

        return QueryAnalysis(
            query=query,
            execution_time_ms=125.5,  # Simulated
            rows_examined=1000,
            rows_returned=10,
            index_used=None,
            issues=issues,
            optimization_score=score
        )

    async def suggest_optimizations(
        self,
        analysis: QueryAnalysis
    ) -> List[OptimizationSuggestion]:
        """
        Generate optimization suggestions for a query.

        Args:
            analysis: Query analysis result

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        for issue in analysis.issues:
            suggestion = await self._generate_suggestion(analysis.query, issue)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    async def _generate_suggestion(
        self,
        query: str,
        issue: str
    ) -> Optional[OptimizationSuggestion]:
        """Generate specific optimization suggestion"""

        if "SELECT *" in issue:
            # Suggest explicit columns
            optimized = query.replace('SELECT *', 'SELECT id, name, email')
            return OptimizationSuggestion(
                query=query,
                issue=issue,
                suggestion="Replace SELECT * with explicit column list",
                optimized_query=optimized,
                estimated_improvement=15.0,
                confidence=0.9
            )

        elif "No WHERE clause" in issue:
            return OptimizationSuggestion(
                query=query,
                issue=issue,
                suggestion="Add WHERE clause to filter data",
                optimized_query=None,
                estimated_improvement=80.0,
                confidence=0.95
            )

        elif "OR conditions" in issue:
            # Suggest rewriting OR as UNION
            return OptimizationSuggestion(
                query=query,
                issue=issue,
                suggestion="Rewrite OR conditions as UNION for better index usage",
                optimized_query=self._rewrite_or_to_union(query),
                estimated_improvement=40.0,
                confidence=0.75
            )

        elif "Leading wildcard" in issue:
            return OptimizationSuggestion(
                query=query,
                issue=issue,
                suggestion="Use full-text search instead of leading wildcard LIKE",
                optimized_query=None,
                estimated_improvement=90.0,
                confidence=0.8
            )

        elif "ORDER BY with LIMIT" in issue:
            # Extract table and column
            match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            table = match.group(1) if match else 'table_name'

            match = re.search(r'ORDER BY\s+(\w+)', query, re.IGNORECASE)
            column = match.group(1) if match else 'column_name'

            index_suggestion = f"CREATE INDEX idx_{table}_{column} ON {table}({column})"
            self.index_recommendations.append(index_suggestion)

            return OptimizationSuggestion(
                query=query,
                issue=issue,
                suggestion=f"Create index: {index_suggestion}",
                optimized_query=None,
                estimated_improvement=70.0,
                confidence=0.85
            )

        return None

    def _rewrite_or_to_union(self, query: str) -> str:
        """Rewrite OR conditions as UNION (simplified example)"""
        # This is a simplified example - production code would use proper SQL parsing
        if 'WHERE' in query.upper():
            base_query = query.split('WHERE')[0]
            conditions = query.split('WHERE')[1]

            if ' OR ' in conditions.upper():
                parts = [c.strip() for c in re.split(r'\s+OR\s+', conditions, flags=re.IGNORECASE)]
                union_queries = [f"{base_query}WHERE {part}" for part in parts]
                return '\nUNION\n'.join(union_queries)

        return query

    async def apply_optimization(
        self,
        suggestion: OptimizationSuggestion,
        auto_approve: bool = False
    ) -> bool:
        """
        Apply an optimization suggestion.

        Args:
            suggestion: Optimization to apply
            auto_approve: Skip approval prompt

        Returns:
            True if optimization was applied
        """
        if self.mode == OptimizationMode.PASSIVE:
            logger.info("Passive mode: Optimization not applied automatically")
            return False

        if not auto_approve and self.mode != OptimizationMode.LEARNING:
            # In production, prompt for approval
            logger.info(f"Approval required for: {suggestion.suggestion}")
            # approved = await prompt_for_approval(suggestion)
            approved = True  # Simulate approval for demo
            if not approved:
                return False

        # Apply optimization
        logger.info(f"Applying optimization: {suggestion.suggestion}")

        # Record in history
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'query': suggestion.query,
            'optimization': suggestion.suggestion,
            'estimated_improvement': suggestion.estimated_improvement
        })

        return True

    async def optimize_query(
        self,
        query: str,
        auto_apply: bool = False
    ) -> Tuple[QueryAnalysis, List[OptimizationSuggestion]]:
        """
        Complete optimization workflow for a query.

        Args:
            query: SQL query to optimize
            auto_apply: Automatically apply optimizations

        Returns:
            Tuple of (analysis, suggestions)
        """
        # Analyze query
        analysis = await self.analyze_query(query)

        # Generate suggestions
        suggestions = await self.suggest_optimizations(analysis)

        # Apply if requested
        if auto_apply and suggestions:
            for suggestion in suggestions:
                if suggestion.confidence > 0.7:
                    await self.apply_optimization(suggestion, auto_approve=True)

        return analysis, suggestions

    def get_optimization_report(self) -> Dict:
        """Generate optimization report"""
        total_optimizations = len(self.optimization_history)
        avg_improvement = sum(
            opt['estimated_improvement'] for opt in self.optimization_history
        ) / total_optimizations if total_optimizations > 0 else 0

        return {
            'total_optimizations': total_optimizations,
            'avg_improvement': avg_improvement,
            'index_recommendations': len(self.index_recommendations),
            'mode': self.mode.value
        }


async def main():
    """Example usage"""
    print("=== Query Optimization Agent ===\n")
    print("This agent analyzes SQL queries and suggests optimizations.\n")

    # Create agent in passive mode
    agent = QueryOptimizationAgent(mode=OptimizationMode.PASSIVE)

    # Example queries to analyze
    queries = [
        "SELECT * FROM users WHERE status = 'active'",
        "SELECT name FROM products ORDER BY price DESC LIMIT 10",
        "SELECT * FROM orders",
        "SELECT * FROM customers WHERE name LIKE '%Smith%' OR email LIKE '%gmail.com'"
    ]

    print("Analyzing sample queries...\n")

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print('='*60)

        analysis, suggestions = await agent.optimize_query(query)

        print(f"\nOptimization Score: {analysis.optimization_score}/100")
        print(f"Execution Time: {analysis.execution_time_ms}ms")
        print(f"Rows Examined: {analysis.rows_examined}")
        print(f"Rows Returned: {analysis.rows_returned}")

        if analysis.issues:
            print(f"\nIssues Found ({len(analysis.issues)}):")
            for issue in analysis.issues:
                print(f"  ⚠️  {issue}")

        if suggestions:
            print(f"\nOptimization Suggestions ({len(suggestions)}):")
            for j, sug in enumerate(suggestions, 1):
                print(f"\n  {j}. {sug.suggestion}")
                print(f"     Estimated Improvement: {sug.estimated_improvement}%")
                print(f"     Confidence: {sug.confidence*100:.0f}%")
                if sug.optimized_query:
                    print(f"     Optimized Query: {sug.optimized_query[:100]}...")

    # Show report
    print("\n\n" + "="*60)
    print("Optimization Report")
    print("="*60)
    report = agent.get_optimization_report()
    print(f"Mode: {report['mode']}")
    print(f"Total Queries Analyzed: {len(queries)}")
    print(f"Index Recommendations: {report['index_recommendations']}")

    if agent.index_recommendations:
        print("\nRecommended Indexes:")
        for idx in agent.index_recommendations:
            print(f"  • {idx}")


if __name__ == "__main__":
    print("Query Optimization Agent for agentic-aishell")
    print("See examples/use-cases/README.md for full documentation\n")
    asyncio.run(main())
