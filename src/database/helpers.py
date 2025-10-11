"""
Database operation helper functions for property-based tests.

Provides utility functions for pagination, query generation, and batch operations.
"""

from typing import Dict, List, Any
import re


def calculate_pagination(total_records: int, page_size: int) -> Dict[str, int]:
    """
    Calculate pagination information.

    Args:
        total_records: Total number of records
        page_size: Number of records per page

    Returns:
        Dictionary with pagination metadata
    """
    if total_records <= 0:
        return {
            'total_records': total_records,
            'page_size': page_size,
            'total_pages': 0,
            'last_page_size': 0
        }

    total_pages = (total_records + page_size - 1) // page_size
    last_page_size = total_records % page_size or page_size

    return {
        'total_records': total_records,
        'page_size': page_size,
        'total_pages': total_pages,
        'last_page_size': last_page_size
    }


def generate_in_clause(column: str, values: List[Any]) -> str:
    """
    Generate SQL IN clause for a list of values.

    Args:
        column: Column name
        values: List of values

    Returns:
        SQL IN clause string
    """
    if len(values) == 0:
        return f"{column} IN ()"

    # Format values as strings
    formatted_values = [str(v) for v in values]
    values_str = ", ".join(formatted_values)

    return f"{column} IN ({values_str})"


def is_valid_identifier(identifier: str) -> bool:
    """
    Check if string is a valid SQL identifier.

    Args:
        identifier: String to validate

    Returns:
        True if valid SQL identifier
    """
    if not identifier:
        return False

    # SQL identifiers must start with letter or underscore
    # and contain only letters, numbers, and underscores
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, identifier))


def validate_query_length(query: str, max_length: int) -> Dict[str, Any]:
    """
    Validate query length.

    Args:
        query: SQL query string
        max_length: Maximum allowed length

    Returns:
        Validation result dictionary
    """
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
            'error': f'Query too long: {query_length} characters (max: {max_length})'
        }
