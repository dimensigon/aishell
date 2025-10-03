"""Natural Language to SQL converter."""

from typing import Dict, List, Optional
import re


class NLPToSQL:
    """Converts natural language queries to SQL statements."""

    # Common NLP patterns and their SQL templates
    PATTERNS = [
        # SELECT patterns
        {
            'pattern': r'show (?:me )?(?:all )?(\w+)',
            'template': 'SELECT * FROM {table};',
            'params': ['table'],
        },
        {
            'pattern': r'get (?:all )?(\w+) from (\w+)',
            'template': 'SELECT {columns} FROM {table};',
            'params': ['columns', 'table'],
        },
        {
            'pattern': r'list (?:all )?(\w+)',
            'template': 'SELECT * FROM {table};',
            'params': ['table'],
        },
        {
            'pattern': r'find (\w+) where (\w+) (?:is |equals? |= )(.+)',
            'template': 'SELECT * FROM {table} WHERE {column} = {value};',
            'params': ['table', 'column', 'value'],
        },

        # COUNT patterns
        {
            'pattern': r'count (?:all )?(\w+)',
            'template': 'SELECT COUNT(*) FROM {table};',
            'params': ['table'],
        },
        {
            'pattern': r'how many (\w+)',
            'template': 'SELECT COUNT(*) FROM {table};',
            'params': ['table'],
        },

        # INSERT patterns
        {
            'pattern': r'(?:add|insert|create) (?:a )?(\w+) (?:with |where )?(.+)',
            'template': 'INSERT INTO {table} {values};',
            'params': ['table', 'values'],
        },

        # UPDATE patterns
        {
            'pattern': r'update (\w+) set (\w+) (?:to |= )(.+) where (\w+) (?:is |= )(.+)',
            'template': 'UPDATE {table} SET {column} = {value} WHERE {where_column} = {where_value};',
            'params': ['table', 'column', 'value', 'where_column', 'where_value'],
        },

        # DELETE patterns
        {
            'pattern': r'delete (?:from )?(\w+) where (\w+) (?:is |= )(.+)',
            'template': 'DELETE FROM {table} WHERE {column} = {value};',
            'params': ['table', 'column', 'value'],
        },
        {
            'pattern': r'remove (?:from )?(\w+) where (\w+) (?:is |= )(.+)',
            'template': 'DELETE FROM {table} WHERE {column} = {value};',
            'params': ['table', 'column', 'value'],
        },
    ]

    def __init__(self):
        """Initialize the NLP to SQL converter."""
        self.compiled_patterns = [
            {
                'regex': re.compile(p['pattern'], re.IGNORECASE),
                'template': p['template'],
                'params': p['params'],
            }
            for p in self.PATTERNS
        ]

    def convert(self, nlp_query: str) -> Dict[str, any]:
        """Convert natural language query to SQL.

        Args:
            nlp_query: Natural language query

        Returns:
            Dict containing SQL query, confidence, and metadata
        """
        nlp_query = nlp_query.strip().lower()

        # Try to match against patterns
        for pattern_info in self.compiled_patterns:
            match = pattern_info['regex'].match(nlp_query)
            if match:
                # Extract parameters from match
                params = {}
                for i, param_name in enumerate(pattern_info['params'], 1):
                    value = match.group(i)
                    # Clean up value (remove quotes if present)
                    value = value.strip('\'"')
                    params[param_name] = value

                # Generate SQL from template
                sql = pattern_info['template'].format(**params)

                return {
                    'sql': sql,
                    'confidence': 'high',
                    'matched_pattern': pattern_info['template'],
                    'parameters': params,
                    'original_query': nlp_query,
                }

        # No pattern matched
        return {
            'sql': None,
            'confidence': 'none',
            'error': 'Could not convert query to SQL',
            'original_query': nlp_query,
            'suggestions': self._get_suggestions(nlp_query),
        }

    def _get_suggestions(self, query: str) -> List[str]:
        """Get suggestions for queries that couldn't be converted.

        Args:
            query: Original query

        Returns:
            List of suggestion strings
        """
        suggestions = [
            "Try phrases like:",
            "  - 'show me users'",
            "  - 'get all products from inventory'",
            "  - 'count orders'",
            "  - 'find users where status is active'",
            "  - 'update users set active to true where id is 1'",
            "  - 'delete from logs where date is 2024-01-01'",
        ]

        # Check if query contains table-like words
        words = query.split()
        potential_tables = [w for w in words if len(w) > 3 and w.isalnum()]

        if potential_tables:
            suggestions.append(f"\nDetected potential table names: {', '.join(potential_tables)}")

        return suggestions

    def is_supported(self, nlp_query: str) -> bool:
        """Check if a query can be converted.

        Args:
            nlp_query: Natural language query

        Returns:
            True if query matches a known pattern
        """
        result = self.convert(nlp_query)
        return result['sql'] is not None
