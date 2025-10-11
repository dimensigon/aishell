"""
SQL input sanitization helpers for property-based tests.

Provides functions to sanitize SQL inputs and prevent injection attacks.
"""

import re
from typing import Any, List, Dict


def sanitize_sql_input(input_text: str) -> str:
    """
    Sanitize SQL input by escaping dangerous characters.

    Args:
        input_text: Raw input text

    Returns:
        Sanitized text safe for SQL operations
    """
    if not isinstance(input_text, str):
        input_text = str(input_text)

    # Escape single quotes
    sanitized = input_text.replace("'", "\\'")

    # Remove SQL comments
    sanitized = sanitized.replace("--", "")
    sanitized = sanitized.replace("/*", "")
    sanitized = sanitized.replace("*/", "")

    # Escape semicolons
    sanitized = sanitized.replace(";", "\\;")

    return sanitized


def sanitize_input(value: Any) -> str:
    """
    Sanitize any input value and convert to safe string.

    Args:
        value: Input value of any type

    Returns:
        Sanitized string representation
    """
    # Convert to string
    if isinstance(value, str):
        text = value
    elif isinstance(value, (int, float)):
        text = str(value)
    elif isinstance(value, bool):
        text = str(value)
    elif value is None:
        text = "NULL"
    else:
        text = str(value)

    # Apply SQL sanitization
    return sanitize_sql_input(text)


def sanitize_batch(input_list: List[Any]) -> List[str]:
    """
    Sanitize a list of inputs.

    Args:
        input_list: List of input values

    Returns:
        List of sanitized strings
    """
    return [sanitize_input(item) for item in input_list]


def sanitize_dict(input_dict: Dict[str, Any]) -> Dict[str, str]:
    """
    Sanitize all values in a dictionary.

    Args:
        input_dict: Dictionary with any values

    Returns:
        Dictionary with sanitized string values
    """
    result = {}
    for key, value in input_dict.items():
        result[key] = sanitize_input(value)
    return result
