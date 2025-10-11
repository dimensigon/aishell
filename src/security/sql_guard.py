"""
SQL injection prevention and query validation.

Provides SQL query safety checks and injection detection.
"""

import re
from typing import Dict, List, Any


class SQLGuard:
    """Guards against SQL injection and unsafe queries."""

    # SQL injection patterns
    INJECTION_PATTERNS = [
        r";\s*DROP\s+TABLE",
        r";\s*DROP\s+DATABASE",
        r";\s*DELETE\s+FROM",
        r";\s*UPDATE\s+",
        r";\s*INSERT\s+INTO",
        r"--\s*$",
        r"\/\*.*\*\/",
        r"UNION\s+SELECT",
        r"OR\s+1\s*=\s*1",
        r"OR\s+'1'\s*=\s*'1'",
        r"OR\s+\"1\"\s*=\s*\"1\"",
        r"'\s+OR\s+'",
        r'"\s+OR\s+"',
        r";\s*EXEC",
        r";\s*EXECUTE",
        r"xp_cmdshell",
        r"sp_executesql",
    ]

    # Dangerous SQL keywords
    DANGEROUS_KEYWORDS = [
        'DROP',
        'TRUNCATE',
        'ALTER',
        'EXEC',
        'EXECUTE',
        'xp_',
        'sp_',
    ]

    def __init__(self):
        """Initialize SQL guard."""
        self._injection_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.INJECTION_PATTERNS
        ]

    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate SQL query for safety.

        Args:
            query: SQL query to validate

        Returns:
            Dictionary with validation results
        """
        result = {
            'is_safe': True,
            'threat_type': None,
            'threats_detected': [],
            'severity': 'none',
            'recommendations': []
        }

        # Check for injection patterns
        for pattern in self._injection_patterns:
            if pattern.search(query):
                result['is_safe'] = False
                result['threat_type'] = 'SQL Injection'
                result['threats_detected'].append({
                    'type': 'injection_pattern',
                    'pattern': pattern.pattern,
                    'description': 'Potential SQL injection detected'
                })
                result['severity'] = 'critical'
                result['recommendations'].append(
                    'Use parameterized queries instead of string concatenation'
                )
                break

        # Check for multiple statements (statement chaining) - but treat as injection
        if ';' in query:
            statements = [s.strip() for s in query.split(';') if s.strip()]
            if len(statements) > 1:
                result['is_safe'] = False
                result['threat_type'] = 'SQL Injection'  # Chaining is a form of injection
                result['threats_detected'].append({
                    'type': 'sql_injection',
                    'count': len(statements),
                    'description': 'SQL injection via statement chaining detected'
                })
                result['severity'] = 'high'
                result['recommendations'].append(
                    'Execute statements separately using parameterized queries'
                )

        # Check for dangerous keywords
        query_upper = query.upper()
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                result['threats_detected'].append({
                    'type': 'dangerous_keyword',
                    'keyword': keyword,
                    'description': f'Dangerous keyword {keyword} detected'
                })
                if result['severity'] != 'critical':
                    result['severity'] = 'high'

        # Check for comments (can be used to hide malicious code)
        if '--' in query or '/*' in query:
            result['threats_detected'].append({
                'type': 'sql_comment',
                'description': 'SQL comments detected (potential obfuscation)'
            })

        # Update is_safe based on severity
        if result['severity'] in ['critical', 'high']:
            result['is_safe'] = False

        return result

    def sanitize_input(self, value: str) -> str:
        """Sanitize user input for SQL queries.

        Args:
            value: Input value to sanitize

        Returns:
            Sanitized value
        """
        # Escape single quotes
        sanitized = value.replace("'", "''")

        # Remove dangerous characters
        sanitized = re.sub(r'[;\-\/*]', '', sanitized)

        return sanitized

    def check_parameterization(self, query: str) -> bool:
        """Check if query uses parameterization.

        Args:
            query: SQL query to check

        Returns:
            True if query appears to use parameters
        """
        # Check for common parameter markers
        parameter_markers = ['?', ':param', '@param', '%s', '%(', '$1']

        for marker in parameter_markers:
            if marker in query:
                return True

        return False

    def suggest_parameterization(self, query: str) -> Dict[str, Any]:
        """Suggest parameterized version of query.

        Args:
            query: Original query

        Returns:
            Dictionary with suggestions
        """
        suggestions = {
            'original': query,
            'parameterized': None,
            'parameters': [],
            'benefits': [
                'Prevents SQL injection',
                'Improves query plan caching',
                'Better performance'
            ]
        }

        # Try to identify string literals to parameterize
        string_literals = re.findall(r"'([^']*)'", query)

        if string_literals:
            parameterized = query
            parameters = []

            for i, literal in enumerate(string_literals, 1):
                param_name = f'param{i}'
                parameterized = parameterized.replace(f"'{literal}'", f':{param_name}', 1)
                parameters.append({
                    'name': param_name,
                    'value': literal
                })

            suggestions['parameterized'] = parameterized
            suggestions['parameters'] = parameters

        return suggestions

    def detect_sql_keywords(self, text: str) -> List[str]:
        """Detect SQL keywords in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected SQL keywords
        """
        sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
            'ALTER', 'TRUNCATE', 'FROM', 'WHERE', 'JOIN', 'UNION'
        ]

        detected = []
        text_upper = text.upper()

        for keyword in sql_keywords:
            if re.search(r'\b' + keyword + r'\b', text_upper):
                detected.append(keyword)

        return detected
