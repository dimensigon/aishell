"""Plugin sandboxing for resource limits and file system access control."""

import logging
import os
from pathlib import Path
from typing import Set, Optional

logger = logging.getLogger(__name__)


class PluginSandbox:
    """Manages sandboxed file system access for plugins."""

    def __init__(self):
        """Initialize plugin sandbox."""
        self.logger = logging.getLogger("plugin.sandbox")
        self._allowed_paths: Set[Path] = set()
        self._denied_paths: Set[Path] = {
            Path("/etc"),
            Path("/sys"),
            Path("/proc"),
            Path("/dev"),
            Path("/boot"),
        }

    def allow_path(self, path: str) -> None:
        """
        Allow access to a path.

        Args:
            path: Path to allow
        """
        path_obj = Path(path).resolve()
        self._allowed_paths.add(path_obj)
        self.logger.debug(f"Allowed path: {path_obj}")

    def deny_path(self, path: str) -> None:
        """
        Deny access to a path.

        Args:
            path: Path to deny
        """
        path_obj = Path(path).resolve()
        self._denied_paths.add(path_obj)
        self.logger.debug(f"Denied path: {path_obj}")

    def can_access(self, path: str) -> bool:
        """
        Check if a path can be accessed.

        Args:
            path: Path to check

        Returns:
            True if access is allowed
        """
        try:
            path_obj = Path(path).resolve()

            # Check if path is explicitly denied
            for denied in self._denied_paths:
                try:
                    path_obj.relative_to(denied)
                    return False
                except ValueError:
                    continue

            # Check if path is explicitly allowed
            for allowed in self._allowed_paths:
                try:
                    path_obj.relative_to(allowed)
                    return True
                except ValueError:
                    continue

            # Default deny if no explicit allow
            return False

        except Exception as e:
            self.logger.error(f"Error checking path access: {e}")
            return False

    def clear_allowed_paths(self) -> None:
        """Clear all allowed paths."""
        self._allowed_paths.clear()

    def get_allowed_paths(self) -> Set[Path]:
        """
        Get all allowed paths.

        Returns:
            Set of allowed Path objects
        """
        return self._allowed_paths.copy()


class ResourceLimiter:
    """Enforces resource limits for plugins."""

    def __init__(self, max_memory_mb: int = 100, max_cpu_percent: int = 50):
        """
        Initialize resource limiter.

        Args:
            max_memory_mb: Maximum memory in MB
            max_cpu_percent: Maximum CPU usage percentage
        """
        self.logger = logging.getLogger("plugin.resources")
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self._usage = {}

    def track_usage(self, plugin_name: str, memory_mb: int = 0, cpu_percent: int = 0) -> None:
        """
        Track resource usage for a plugin.

        Args:
            plugin_name: Name of the plugin
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage
        """
        self._usage[plugin_name] = {
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent
        }

        self.logger.debug(
            f"Plugin {plugin_name} usage: {memory_mb}MB memory, {cpu_percent}% CPU"
        )

    def within_limits(self, plugin_name: str) -> bool:
        """
        Check if plugin is within resource limits.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if within limits
        """
        if plugin_name not in self._usage:
            return True

        usage = self._usage[plugin_name]

        memory_ok = usage["memory_mb"] <= self.max_memory_mb
        cpu_ok = usage["cpu_percent"] <= self.max_cpu_percent

        if not memory_ok:
            self.logger.warning(
                f"Plugin {plugin_name} exceeded memory limit: "
                f"{usage['memory_mb']}MB > {self.max_memory_mb}MB"
            )

        if not cpu_ok:
            self.logger.warning(
                f"Plugin {plugin_name} exceeded CPU limit: "
                f"{usage['cpu_percent']}% > {self.max_cpu_percent}%"
            )

        return memory_ok and cpu_ok

    def get_usage(self, plugin_name: str) -> Optional[dict]:
        """
        Get current usage for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Usage dictionary or None
        """
        return self._usage.get(plugin_name)

    def clear_usage(self, plugin_name: str) -> None:
        """
        Clear usage tracking for a plugin.

        Args:
            plugin_name: Name of the plugin
        """
        if plugin_name in self._usage:
            del self._usage[plugin_name]
