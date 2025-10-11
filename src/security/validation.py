"""
Input validation helpers for security and data integrity.

Provides validation functions for emails, identifiers, and other inputs.
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        True if valid email format
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email validation pattern
    # Must have @ and at least one dot after @
    if '@' not in email:
        return False

    local, domain = email.rsplit('@', 1)

    # Local part must not be empty
    if not local:
        return False

    # Domain must have at least one dot
    if '.' not in domain:
        return False

    # Domain must not start or end with dot
    if domain.startswith('.') or domain.endswith('.'):
        return False

    return True


def validate_sql_identifier(identifier: str) -> bool:
    """
    Validate SQL identifier (table name, column name, etc.).

    Args:
        identifier: Identifier to validate

    Returns:
        True if valid SQL identifier
    """
    if not identifier or not isinstance(identifier, str):
        return False

    # SQL identifiers must start with letter or underscore
    # and contain only letters, numbers, and underscores
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, identifier))


def validate_query_length(query: str, max_length: int = 5000) -> dict:
    """
    Validate query length against maximum.

    Args:
        query: Query string
        max_length: Maximum allowed length

    Returns:
        Validation result with 'valid' and optional 'error' keys
    """
    if not query:
        return {'valid': True, 'length': 0}

    query_length = len(query)

    if query_length <= max_length:
        return {
            'valid': True,
            'length': query_length,
            'max_length': max_length
        }
    else:
        return {
            'valid': False,
            'length': query_length,
            'max_length': max_length,
            'error': f'Query too long: {query_length} characters exceeds maximum of {max_length}'
        }
