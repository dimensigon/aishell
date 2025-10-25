"""Plugin dependency management and resolution."""

import logging
import re
from typing import Dict, List, Set, Any, Optional
from packaging import version

logger = logging.getLogger(__name__)


class DependencyResolver:
    """Resolves plugin dependencies and manages versions."""

    def __init__(self):
        """Initialize dependency resolver."""
        self.logger = logging.getLogger("plugin.dependencies")
        self._available_plugins: Dict[str, str] = {}
        self._plugin_deps: Dict[str, List[str]] = {}

    def register_available(self, plugin_name: str, plugin_version: str) -> None:
        """
        Register an available plugin.

        Args:
            plugin_name: Name of the plugin
            plugin_version: Version string
        """
        self._available_plugins[plugin_name] = plugin_version
        self.logger.debug(f"Registered plugin: {plugin_name} v{plugin_version}")

    def register_plugin(self, plugin_name: str, dependencies: Optional[List[str]] = None) -> None:
        """
        Register a plugin with its dependencies.

        Args:
            plugin_name: Name of the plugin
            dependencies: List of dependency specifications
        """
        self._plugin_deps[plugin_name] = dependencies or []

    def check_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """
        Check if dependencies are satisfied.

        Args:
            dependencies: List of dependency specifications (e.g., "plugin_a>=1.0.0")

        Returns:
            Dictionary with 'satisfied' bool and 'missing' list
        """
        missing = []
        incompatible = []

        for dep_spec in dependencies:
            dep_name, dep_version = self._parse_dependency(dep_spec)

            if dep_name not in self._available_plugins:
                missing.append(dep_name)
            elif dep_version:
                available_version = self._available_plugins[dep_name]
                if not self._check_version_compatibility(available_version, dep_version):
                    incompatible.append(f"{dep_name} (requires {dep_version}, has {available_version})")

        return {
            "satisfied": len(missing) == 0 and len(incompatible) == 0,
            "missing": missing,
            "incompatible": incompatible
        }

    def resolve_load_order(self) -> Dict[str, Any]:
        """
        Resolve the correct load order for plugins based on dependencies.

        Returns:
            Dictionary with 'order' list and 'errors' list
        """
        # Detect circular dependencies
        circular = self._detect_circular_dependencies()
        if circular:
            return {
                "order": [],
                "errors": ["circular_dependency"],
                "circular": circular
            }

        # Topological sort
        try:
            order = self._topological_sort()
            return {
                "order": order,
                "errors": []
            }
        except Exception as e:
            return {
                "order": [],
                "errors": [str(e)]
            }

    def _parse_dependency(self, dep_spec: str) -> tuple:
        """
        Parse dependency specification.

        Args:
            dep_spec: Dependency string (e.g., "plugin_a>=1.0.0")

        Returns:
            Tuple of (plugin_name, version_spec)
        """
        # Match patterns like "plugin_name>=1.0.0", "plugin_name==1.0.0", etc.
        match = re.match(r'([a-zA-Z0-9_-]+)(>=|==|<=|>|<)?(.+)?', dep_spec)

        if match:
            name = match.group(1)
            operator = match.group(2)
            ver = match.group(3)

            if operator and ver:
                return (name, f"{operator}{ver}")
            return (name, None)

        return (dep_spec, None)

    def _check_version_compatibility(self, available: str, required: str) -> bool:
        """
        Check if version satisfies requirement.

        Args:
            available: Available version string
            required: Required version spec (e.g., ">=1.0.0")

        Returns:
            True if compatible
        """
        try:
            available_ver = version.parse(available)

            # Parse operator and version
            if required.startswith(">="):
                required_ver = version.parse(required[2:])
                return available_ver >= required_ver
            elif required.startswith("<="):
                required_ver = version.parse(required[2:])
                return available_ver <= required_ver
            elif required.startswith(">"):
                required_ver = version.parse(required[1:])
                return available_ver > required_ver
            elif required.startswith("<"):
                required_ver = version.parse(required[1:])
                return available_ver < required_ver
            elif required.startswith("=="):
                required_ver = version.parse(required[2:])
                return available_ver == required_ver
            else:
                # Default to ==
                required_ver = version.parse(required)
                return available_ver == required_ver

        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return False

    def _detect_circular_dependencies(self) -> Optional[List[str]]:
        """
        Detect circular dependencies.

        Returns:
            List of plugins in circular dependency, or None if no circles
        """
        visited = set()
        rec_stack = set()

        def visit(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Get dependencies
            deps = self._plugin_deps.get(node, [])

            for dep_spec in deps:
                dep_name, _ = self._parse_dependency(dep_spec)

                if dep_name not in visited:
                    result = visit(dep_name, path.copy())
                    if result:
                        return result
                elif dep_name in rec_stack:
                    # Found circular dependency
                    return path + [dep_name]

            rec_stack.remove(node)
            return None

        for plugin in self._plugin_deps.keys():
            if plugin not in visited:
                result = visit(plugin, [])
                if result:
                    return result

        return None

    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort on plugin dependencies.

        Returns:
            Ordered list of plugin names
        """
        in_degree = {plugin: 0 for plugin in self._plugin_deps}

        # Calculate in-degrees
        for plugin, deps in self._plugin_deps.items():
            for dep_spec in deps:
                dep_name, _ = self._parse_dependency(dep_spec)
                if dep_name in in_degree:
                    in_degree[dep_name] += 1

        # Find plugins with no dependencies
        queue = [p for p, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            plugin = queue.pop(0)
            result.append(plugin)

            # Reduce in-degree for dependents
            for other_plugin, deps in self._plugin_deps.items():
                for dep_spec in deps:
                    dep_name, _ = self._parse_dependency(dep_spec)
                    if dep_name == plugin and other_plugin in in_degree:
                        in_degree[other_plugin] -= 1
                        if in_degree[other_plugin] == 0:
                            queue.append(other_plugin)

        return result
