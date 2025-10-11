"""Plugin hook system for event-driven plugin interactions."""

import logging
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class Hook:
    """Represents a single hook registration."""

    def __init__(self, callback: Callable, priority: int = 0):
        """
        Initialize hook.

        Args:
            callback: Function to call when hook is executed
            priority: Hook priority (higher = executed first)
        """
        self.callback = callback
        self.priority = priority


class HookManager:
    """Manages plugin hooks and event-driven interactions."""

    def __init__(self):
        """Initialize hook manager."""
        self.logger = logging.getLogger("plugin.hooks")
        self._hooks: Dict[str, List[Hook]] = defaultdict(list)

    def register_hook(self, event_name: str, callback: Callable, priority: int = 0) -> None:
        """
        Register a hook for an event.

        Args:
            event_name: Name of the event
            callback: Function to call when event occurs
            priority: Hook priority (higher priority = executed first)
        """
        hook = Hook(callback, priority)
        self._hooks[event_name].append(hook)

        # Sort hooks by priority (descending)
        self._hooks[event_name].sort(key=lambda h: h.priority, reverse=True)

        self.logger.debug(f"Registered hook for '{event_name}' with priority {priority}")

    def unregister_hook(self, event_name: str, callback: Callable) -> bool:
        """
        Unregister a hook.

        Args:
            event_name: Name of the event
            callback: Callback function to remove

        Returns:
            True if hook was removed, False if not found
        """
        if event_name not in self._hooks:
            return False

        original_count = len(self._hooks[event_name])
        self._hooks[event_name] = [
            h for h in self._hooks[event_name]
            if h.callback != callback
        ]

        return len(self._hooks[event_name]) < original_count

    def execute_hook(self, event_name: str, data: Any = None) -> Any:
        """
        Execute all hooks registered for an event.

        Args:
            event_name: Name of the event
            data: Data to pass to hooks

        Returns:
            Result from the last hook executed, or original data if no hooks
        """
        if event_name not in self._hooks:
            return data

        result = data

        for hook in self._hooks[event_name]:
            try:
                result = hook.callback(result)
            except Exception as e:
                self.logger.error(f"Error executing hook for '{event_name}': {e}")

        return result

    def execute_hooks_async(self, event_name: str, data: Any = None) -> List[Any]:
        """
        Execute all hooks in parallel and return all results.

        Args:
            event_name: Name of the event
            data: Data to pass to hooks

        Returns:
            List of results from all hooks
        """
        if event_name not in self._hooks:
            return []

        results = []

        for hook in self._hooks[event_name]:
            try:
                result = hook.callback(data)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error executing hook for '{event_name}': {e}")
                results.append(None)

        return results

    def has_hooks(self, event_name: str) -> bool:
        """
        Check if any hooks are registered for an event.

        Args:
            event_name: Name of the event

        Returns:
            True if hooks are registered
        """
        return event_name in self._hooks and len(self._hooks[event_name]) > 0

    def get_hook_count(self, event_name: str) -> int:
        """
        Get number of hooks registered for an event.

        Args:
            event_name: Name of the event

        Returns:
            Number of registered hooks
        """
        return len(self._hooks.get(event_name, []))

    def clear_hooks(self, event_name: Optional[str] = None) -> None:
        """
        Clear hooks for an event or all events.

        Args:
            event_name: Name of event to clear, or None to clear all
        """
        if event_name is None:
            self._hooks.clear()
        elif event_name in self._hooks:
            del self._hooks[event_name]
