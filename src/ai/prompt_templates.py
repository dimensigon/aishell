"""
Prompt Templates for AI Query Assistant

Carefully crafted prompts for different query assistance tasks.
"""

from typing import Dict, Any, Optional
from src.ai.query_assistant import QueryContext


class PromptTemplates:
    """Collection of prompt templates for Claude API"""

    def generate_sql_prompt(self, natural_query: str, context: QueryContext) -> str:
        """Generate prompt for SQL generation from natural language"""

        schema_context = self._format_schema_context(context)
        recent_queries = self._format_recent_queries(context)

        prompt = f"""You are an expert SQL database assistant. Generate a SQL query based on the user's natural language request.

DATABASE CONTEXT:
- Database Type: {context.database_type}
- Available Tables: {', '.join(context.table_names) if context.table_names else 'Not specified'}

{schema_context}

{recent_queries}

USER REQUEST:
"{natural_query}"

INSTRUCTIONS:
1. Generate a valid SQL query that fulfills the user's request
2. Use proper SQL syntax for {context.database_type}
3. Consider joins, subqueries, and aggregations where appropriate
4. Include appropriate WHERE clauses and filters
5. Optimize for performance (use indexes, avoid SELECT *, etc.)
6. Provide a clear explanation of what the query does

OUTPUT FORMAT (JSON):
```json
{{
  "sql": "YOUR SQL QUERY HERE",
  "explanation": "Clear explanation of what this query does",
  "optimizations": ["List any optimization techniques used"],
  "warnings": ["Any warnings or considerations"],
  "confidence": 0.0-1.0
}}
```

Generate the SQL query now:"""

        return prompt

    def explain_query_prompt(
        self,
        sql_query: str,
        context: QueryContext,
        detail_level: str = "medium"
    ) -> str:
        """Generate prompt for explaining SQL query"""

        detail_instructions = {
            'simple': "Provide a brief, one-paragraph explanation suitable for non-technical users.",
            'medium': "Provide a clear explanation with moderate technical detail.",
            'detailed': "Provide a comprehensive, technical explanation including query execution flow, joins, performance considerations, and potential issues."
        }

        schema_context = self._format_schema_context(context)

        prompt = f"""You are an expert SQL database assistant. Explain the following SQL query in plain English.

DATABASE CONTEXT:
- Database Type: {context.database_type}
{schema_context}

SQL QUERY:
```sql
{sql_query}
```

EXPLANATION LEVEL: {detail_level.upper()}
{detail_instructions.get(detail_level, detail_instructions['medium'])}

INSTRUCTIONS:
1. Explain what the query does step by step
2. Describe which tables and columns are involved
3. Explain any JOINs, subqueries, or complex operations
4. Mention the expected output/result
5. Note any performance implications if relevant
6. Use {detail_level} technical language

Provide your explanation now:"""

        return prompt

    def optimize_query_prompt(
        self,
        sql_query: str,
        context: QueryContext,
        performance_data: Optional[Dict] = None
    ) -> str:
        """Generate prompt for query optimization"""

        schema_context = self._format_schema_context(context)
        perf_context = ""

        if performance_data:
            perf_context = f"""
CURRENT PERFORMANCE:
- Execution Time: {performance_data.get('execution_time', 'N/A')}
- Rows Affected: {performance_data.get('rows_affected', 'N/A')}
- Rows Scanned: {performance_data.get('rows_scanned', 'N/A')}
"""

        prompt = f"""You are an expert SQL performance optimization specialist. Analyze and optimize the following SQL query.

DATABASE CONTEXT:
- Database Type: {context.database_type}
{schema_context}
{perf_context}

SQL QUERY TO OPTIMIZE:
```sql
{sql_query}
```

OPTIMIZATION GOALS:
1. Improve query execution speed
2. Reduce resource consumption (CPU, memory, I/O)
3. Minimize table scans
4. Optimize JOIN operations
5. Suggest appropriate indexes
6. Eliminate redundant operations

INSTRUCTIONS:
1. Analyze the current query for performance bottlenecks
2. Provide an optimized version of the query
3. List specific optimization techniques applied
4. Suggest database schema improvements (indexes, partitions, etc.)
5. Explain the expected performance improvement
6. Note any trade-offs or considerations

OUTPUT FORMAT:
1. **Optimized Query:** (SQL code block)
2. **Optimizations Applied:** (numbered list)
3. **Index Recommendations:** (specific CREATE INDEX statements)
4. **Expected Improvement:** (percentage or description)
5. **Additional Recommendations:** (any other suggestions)

Provide your optimization analysis now:"""

        return prompt

    def fix_query_prompt(
        self,
        sql_query: str,
        error_message: str,
        context: QueryContext
    ) -> str:
        """Generate prompt for fixing broken SQL query"""

        schema_context = self._format_schema_context(context)

        prompt = f"""You are an expert SQL debugging specialist. Fix the following broken SQL query.

DATABASE CONTEXT:
- Database Type: {context.database_type}
{schema_context}

BROKEN SQL QUERY:
```sql
{sql_query}
```

ERROR MESSAGE:
{error_message}

INSTRUCTIONS:
1. Identify the root cause of the error
2. Provide a corrected version of the query
3. Explain what was wrong and how you fixed it
4. Suggest best practices to avoid similar errors

OUTPUT FORMAT (JSON):
```json
{{
  "sql": "CORRECTED SQL QUERY HERE",
  "explanation": "Explanation of the error and fix",
  "error_cause": "Root cause of the error",
  "best_practices": ["List of best practices to avoid this error"],
  "confidence": 0.0-1.0
}}
```

Provide the fixed query now:"""

        return prompt

    def analyze_schema_prompt(
        self,
        schema_info: Dict[str, Any],
        analysis_type: str = "general"
    ) -> str:
        """Generate prompt for schema analysis"""

        schema_str = self._format_schema_info(schema_info)

        analysis_instructions = {
            'general': "Provide a general overview of the database schema, including key tables, relationships, and design patterns.",
            'relationships': "Focus on analyzing table relationships, foreign keys, and data dependencies.",
            'optimization': "Focus on schema optimization opportunities, including index recommendations, normalization issues, and performance improvements."
        }

        prompt = f"""You are an expert database architect. Analyze the following database schema.

DATABASE SCHEMA:
{schema_str}

ANALYSIS TYPE: {analysis_type.upper()}
{analysis_instructions.get(analysis_type, analysis_instructions['general'])}

INSTRUCTIONS:
1. Provide insights about the schema structure
2. Identify strengths and potential issues
3. Suggest improvements if applicable
4. Consider scalability and maintainability
5. Note any best practices or anti-patterns

Provide your schema analysis now:"""

        return prompt

    def _format_schema_context(self, context: QueryContext) -> str:
        """Format schema information for prompts"""
        if not context.schema_info:
            return "- Schema Information: Not available"

        lines = ["SCHEMA INFORMATION:"]
        for table_name, table_info in context.schema_info.items():
            lines.append(f"  Table: {table_name}")
            if 'columns' in table_info:
                lines.append("    Columns:")
                for col in table_info['columns']:
                    col_type = col.get('type', 'unknown')
                    constraints = col.get('constraints', [])
                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    lines.append(f"      - {col['name']}: {col_type}{constraint_str}")

        return '\n'.join(lines)

    def _format_recent_queries(self, context: QueryContext) -> str:
        """Format recent queries for context"""
        if not context.recent_queries:
            return ""

        lines = ["RECENT QUERIES (for context):"]
        for i, query in enumerate(context.recent_queries[-3:], 1):
            lines.append(f"  {i}. {query[:100]}...")

        return '\n'.join(lines)

    def _format_schema_info(self, schema_info: Dict[str, Any]) -> str:
        """Format full schema information"""
        lines = []
        for table_name, table_info in schema_info.items():
            lines.append(f"Table: {table_name}")
            if 'columns' in table_info:
                lines.append("  Columns:")
                for col in table_info['columns']:
                    lines.append(f"    - {col['name']}: {col.get('type', 'unknown')}")

            if 'indexes' in table_info:
                lines.append("  Indexes:")
                for idx in table_info['indexes']:
                    lines.append(f"    - {idx}")

            if 'foreign_keys' in table_info:
                lines.append("  Foreign Keys:")
                for fk in table_info['foreign_keys']:
                    lines.append(f"    - {fk}")

            lines.append("")

        return '\n'.join(lines)
