"""Plugin discovery system for finding and cataloging plugins."""

import ast
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers plugins in specified directories."""

    def __init__(self, search_paths: List[str]):
        """
        Initialize plugin discovery.

        Args:
            search_paths: List of directory paths to search for plugins
        """
        self.search_paths = [Path(p) for p in search_paths]
        self.logger = logging.getLogger("plugin.discovery")

    def discover(self, plugin_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover plugins in search paths.

        Args:
            plugin_type: Optional filter by plugin type

        Returns:
            List of plugin metadata dictionaries
        """
        discovered = []

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            for plugin_file in search_path.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue

                try:
                    metadata = self._extract_metadata(plugin_file)
                    if metadata:
                        # Filter by type if specified
                        if plugin_type is None or metadata.get("plugin_type") == plugin_type:
                            discovered.append(metadata)
                except Exception as e:
                    self.logger.debug(f"Failed to extract metadata from {plugin_file}: {e}")

        return discovered

    def _extract_metadata(self, plugin_file: Path) -> Optional[Dict[str, Any]]:
        """
        Extract plugin metadata from Python file.

        Args:
            plugin_file: Path to plugin file

        Returns:
            Plugin metadata dictionary or None if invalid
        """
        try:
            with open(plugin_file, 'r') as f:
                content = f.read()

            # Parse Python AST
            tree = ast.parse(content)

            # Find class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metadata = self._extract_class_metadata(node)
                    if metadata:
                        metadata["file_path"] = str(plugin_file)
                        return metadata

            return None

        except SyntaxError:
            # Invalid Python syntax - ignore
            return None
        except Exception as e:
            self.logger.error(f"Error parsing {plugin_file}: {e}")
            return None

    def _extract_class_metadata(self, class_node: ast.ClassDef) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from class definition.

        Args:
            class_node: AST ClassDef node

        Returns:
            Metadata dictionary or None
        """
        metadata = {}

        # Look for class attributes
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id

                        # Extract constant values
                        if isinstance(item.value, ast.Constant):
                            metadata[attr_name] = item.value.value
                        elif isinstance(item.value, ast.Str):  # Python 3.7 compatibility
                            metadata[attr_name] = item.value.s
                        elif isinstance(item.value, ast.List):
                            # Extract list values
                            metadata[attr_name] = [
                                elt.value if isinstance(elt, ast.Constant) else elt.s
                                for elt in item.value.elts
                                if isinstance(elt, (ast.Constant, ast.Str))
                            ]

        # Check if this looks like a plugin class
        if "name" in metadata:
            return metadata

        return None
