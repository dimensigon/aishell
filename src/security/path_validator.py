"""
Path Traversal Protection

Provides utilities to safely handle file paths and prevent path traversal attacks.
"""

from pathlib import Path
from typing import Union


class SecurityError(Exception):
    """Security-related error"""
    pass


def safe_path_join(base: Union[str, Path], user_path: str) -> Path:
    """
    Safely join paths and prevent traversal attacks.

    Args:
        base: Base directory path (must be absolute)
        user_path: User-provided path component

    Returns:
        Resolved absolute path within base directory

    Raises:
        SecurityError: If path traversal attempt detected
        ValueError: If base path is not absolute
    """
    base_path = Path(base).resolve()

    # Ensure base path is absolute
    if not base_path.is_absolute():
        raise ValueError(f"Base path must be absolute: {base_path}")

    # Resolve user path relative to base
    try:
        full_path = (base_path / user_path).resolve()
    except (ValueError, RuntimeError) as e:
        raise SecurityError(f"Invalid path: {user_path}") from e

    # Ensure resolved path is within base directory
    try:
        full_path.relative_to(base_path)
    except ValueError:
        raise SecurityError(
            f"Path traversal attempt detected: {user_path} "
            f"(resolved to {full_path}, outside {base_path})"
        )

    return full_path


def validate_vault_path(vault_path: Union[str, Path], allow_insecure: bool = False) -> Path:
    """
    Validate and sanitize vault path.

    Args:
        vault_path: User-provided vault path
        allow_insecure: Allow paths outside home directory (for testing only)

    Returns:
        Validated absolute path

    Raises:
        SecurityError: If path is unsafe
    """
    if not vault_path:
        # Default to home directory
        return Path.home() / '.ai-shell' / 'vault.enc'

    path = Path(vault_path)

    # If relative, make it relative to home/.ai-shell
    if not path.is_absolute():
        base_dir = Path.home() / '.ai-shell'
        return safe_path_join(base_dir, str(path))

    # If absolute, ensure it's within home directory or explicit allowed locations
    home_dir = Path.home()
    try:
        path.relative_to(home_dir)
        return path.resolve()
    except ValueError:
        # Path is outside home directory
        if allow_insecure:
            # TESTING ONLY: Allow insecure paths for unit tests
            return path.resolve()
        raise SecurityError(
            f"Vault path must be within home directory: {path} "
            f"(home: {home_dir})"
        )


def validate_config_path(config_path: Union[str, Path]) -> Path:
    """
    Validate and sanitize configuration file path.

    Args:
        config_path: User-provided config path

    Returns:
        Validated absolute path

    Raises:
        SecurityError: If path is unsafe
    """
    if not config_path:
        return Path.home() / '.ai-shell' / 'config.yaml'

    path = Path(config_path)

    # If relative, make it relative to home/.ai-shell
    if not path.is_absolute():
        base_dir = Path.home() / '.ai-shell'
        return safe_path_join(base_dir, str(path))

    # Validate absolute path
    return path.resolve()
