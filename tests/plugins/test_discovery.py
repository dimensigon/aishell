"""Comprehensive tests for plugin discovery module."""

import pytest
import ast
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.plugins.discovery import PluginDiscovery


class TestPluginDiscovery:
    """Test suite for PluginDiscovery class."""

    @pytest.fixture
    def discovery(self, tmp_path):
        """Create a discovery instance with temp search paths."""
        return PluginDiscovery([str(tmp_path)])

    @pytest.fixture
    def sample_plugin_file(self, tmp_path):
        """Create a sample plugin file."""
        plugin_file = tmp_path / "sample_plugin.py"
        plugin_file.write_text("""
class SamplePlugin:
    name = "sample"
    version = "1.0.0"
    plugin_type = "utility"
    author = "Test Author"
    description = "Test plugin"
    dependencies = ["dep1", "dep2"]

    def activate(self):
        return True
""")
        return plugin_file

    def test_discovery_initialization(self, tmp_path):
        """Test discovery initialization."""
        paths = [str(tmp_path), "/another/path"]
        discovery = PluginDiscovery(paths)

        assert len(discovery.search_paths) == 2
        assert all(isinstance(p, Path) for p in discovery.search_paths)

    def test_discover_no_plugins(self, discovery):
        """Test discovery with no plugins available."""
        discovered = discovery.discover()
        assert discovered == []

    def test_discover_single_plugin(self, discovery, sample_plugin_file):
        """Test discovering a single plugin."""
        discovered = discovery.discover()

        assert len(discovered) == 1
        metadata = discovered[0]

        assert metadata["name"] == "sample"
        assert metadata["version"] == "1.0.0"
        assert metadata["plugin_type"] == "utility"
        assert "file_path" in metadata
        assert metadata["file_path"] == str(sample_plugin_file)

    def test_discover_multiple_plugins(self, discovery, tmp_path):
        """Test discovering multiple plugins."""
        # Create multiple plugin files
        for i in range(3):
            plugin_file = tmp_path / f"plugin_{i}.py"
            plugin_file.write_text(f"""
class Plugin{i}:
    name = "plugin_{i}"
    version = "1.{i}.0"
    plugin_type = "utility"
""")

        discovered = discovery.discover()
        assert len(discovered) == 3

        names = [p["name"] for p in discovered]
        assert "plugin_0" in names
        assert "plugin_1" in names
        assert "plugin_2" in names

    def test_discover_skip_private_files(self, discovery, tmp_path):
        """Test that files starting with _ are skipped."""
        # Create public plugin
        public = tmp_path / "public.py"
        public.write_text("""
class PublicPlugin:
    name = "public"
""")

        # Create private file
        private = tmp_path / "_private.py"
        private.write_text("""
class PrivatePlugin:
    name = "private"
""")

        discovered = discovery.discover()

        assert len(discovered) == 1
        assert discovered[0]["name"] == "public"

    def test_discover_with_type_filter(self, discovery, tmp_path):
        """Test filtering plugins by type."""
        # Create plugins of different types
        util = tmp_path / "util.py"
        util.write_text("""
class UtilPlugin:
    name = "util"
    plugin_type = "utility"
""")

        ext = tmp_path / "ext.py"
        ext.write_text("""
class ExtPlugin:
    name = "ext"
    plugin_type = "extension"
""")

        # Discover only utility plugins
        discovered = discovery.discover(plugin_type="utility")

        assert len(discovered) == 1
        assert discovered[0]["name"] == "util"

    def test_discover_nonexistent_path(self, tmp_path):
        """Test discovery with non-existent search path."""
        discovery = PluginDiscovery(["/nonexistent/path"])
        discovered = discovery.discover()
        assert discovered == []

    def test_discover_invalid_syntax_file(self, discovery, tmp_path):
        """Test discovery with invalid Python syntax."""
        invalid = tmp_path / "invalid.py"
        invalid.write_text("class Invalid\n    pass")  # Missing colon

        discovered = discovery.discover()
        # Should skip invalid files
        assert discovered == []

    def test_discover_file_without_metadata(self, discovery, tmp_path):
        """Test discovery of file without plugin metadata."""
        no_meta = tmp_path / "no_meta.py"
        no_meta.write_text("""
class NoMetadata:
    def some_method(self):
        pass
""")

        discovered = discovery.discover()
        # Should skip files without metadata
        assert discovered == []

    def test_extract_metadata_success(self, discovery, sample_plugin_file):
        """Test successful metadata extraction."""
        metadata = discovery._extract_metadata(sample_plugin_file)

        assert metadata is not None
        assert metadata["name"] == "sample"
        assert metadata["version"] == "1.0.0"
        assert metadata["plugin_type"] == "utility"
        assert metadata["author"] == "Test Author"
        assert metadata["description"] == "Test plugin"
        assert "dependencies" in metadata
        assert len(metadata["dependencies"]) == 2

    def test_extract_metadata_minimal(self, discovery, tmp_path):
        """Test metadata extraction with minimal attributes."""
        minimal = tmp_path / "minimal.py"
        minimal.write_text("""
class MinimalPlugin:
    name = "minimal"
""")

        metadata = discovery._extract_metadata(minimal)

        assert metadata is not None
        assert metadata["name"] == "minimal"
        assert "version" not in metadata or metadata.get("version") is None

    def test_extract_metadata_no_class(self, discovery, tmp_path):
        """Test metadata extraction from file with no class."""
        no_class = tmp_path / "no_class.py"
        no_class.write_text("""
VALUE = 100

def helper():
    pass
""")

        metadata = discovery._extract_metadata(no_class)
        assert metadata is None

    def test_extract_metadata_multiple_classes(self, discovery, tmp_path):
        """Test metadata extraction with multiple classes."""
        multi = tmp_path / "multi.py"
        multi.write_text("""
class Helper:
    value = 1

class ActualPlugin:
    name = "actual"
    version = "2.0.0"
""")

        metadata = discovery._extract_metadata(multi)

        # Should find first class with name attribute
        assert metadata is not None
        assert metadata["name"] == "actual"

    def test_extract_class_metadata_string_attributes(self, discovery):
        """Test extracting string attributes from class."""
        code = """
class TestPlugin:
    name = "test"
    description = "A test plugin"
"""
        tree = ast.parse(code)
        class_node = tree.body[0]

        metadata = discovery._extract_class_metadata(class_node)

        assert metadata is not None
        assert metadata["name"] == "test"
        assert metadata["description"] == "A test plugin"

    def test_extract_class_metadata_list_attributes(self, discovery):
        """Test extracting list attributes from class."""
        code = """
class TestPlugin:
    name = "test"
    dependencies = ["dep1", "dep2", "dep3"]
    tags = ["tag1", "tag2"]
"""
        tree = ast.parse(code)
        class_node = tree.body[0]

        metadata = discovery._extract_class_metadata(class_node)

        assert metadata is not None
        assert "dependencies" in metadata
        assert len(metadata["dependencies"]) == 3
        assert "dep1" in metadata["dependencies"]
        assert "tags" in metadata
        assert len(metadata["tags"]) == 2

    def test_extract_class_metadata_no_name(self, discovery):
        """Test extracting metadata from class without name."""
        code = """
class NoName:
    version = "1.0.0"
    description = "No name"
"""
        tree = ast.parse(code)
        class_node = tree.body[0]

        metadata = discovery._extract_class_metadata(class_node)
        # Should return None without name attribute
        assert metadata is None

    def test_extract_class_metadata_mixed_types(self, discovery):
        """Test extracting metadata with mixed attribute types."""
        code = """
class MixedPlugin:
    name = "mixed"
    version = "1.0.0"
    max_retries = 5
    enabled = True
    dependencies = ["dep1"]
"""
        tree = ast.parse(code)
        class_node = tree.body[0]

        metadata = discovery._extract_class_metadata(class_node)

        assert metadata is not None
        assert metadata["name"] == "mixed"
        assert metadata["version"] == "1.0.0"
        # Non-string/non-list attributes should also be extracted
        assert metadata.get("max_retries") == 5
        assert metadata.get("enabled") is True

    def test_discover_multiple_search_paths(self, tmp_path):
        """Test discovery across multiple search paths."""
        path1 = tmp_path / "path1"
        path2 = tmp_path / "path2"
        path1.mkdir()
        path2.mkdir()

        # Create plugin in each path
        (path1 / "plugin1.py").write_text("""
class Plugin1:
    name = "plugin1"
""")

        (path2 / "plugin2.py").write_text("""
class Plugin2:
    name = "plugin2"
""")

        discovery = PluginDiscovery([str(path1), str(path2)])
        discovered = discovery.discover()

        assert len(discovered) == 2
        names = [p["name"] for p in discovered]
        assert "plugin1" in names
        assert "plugin2" in names

    def test_discover_nested_directories(self, tmp_path):
        """Test that nested directories are not searched."""
        # Create nested structure
        nested = tmp_path / "nested"
        nested.mkdir()

        # Plugin in root
        (tmp_path / "root.py").write_text("""
class RootPlugin:
    name = "root"
""")

        # Plugin in nested dir
        (nested / "nested.py").write_text("""
class NestedPlugin:
    name = "nested"
""")

        discovery = PluginDiscovery([str(tmp_path)])
        discovered = discovery.discover()

        # Should only find root plugin (glob only searches immediate directory)
        assert len(discovered) == 1
        assert discovered[0]["name"] == "root"

    def test_discover_with_encoding_issues(self, discovery, tmp_path):
        """Test discovery with different file encodings."""
        # Create file with UTF-8 content
        utf8_file = tmp_path / "utf8.py"
        utf8_file.write_text("""
class UTF8Plugin:
    name = "utf8"
    description = "Plugin with UTF-8: 你好, мир, 🚀"
""", encoding='utf-8')

        discovered = discovery.discover()

        assert len(discovered) == 1
        assert discovered[0]["name"] == "utf8"

    def test_discover_read_permission_error(self, discovery, tmp_path):
        """Test discovery when file cannot be read."""
        restricted = tmp_path / "restricted.py"
        restricted.write_text("""
class RestrictedPlugin:
    name = "restricted"
""")

        # Make file unreadable (Unix only)
        import os
        import stat

        try:
            os.chmod(restricted, 0o000)
            discovered = discovery.discover()
            # Should skip unreadable files
            assert len(discovered) == 0
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted, stat.S_IRUSR | stat.S_IWUSR)


class TestPluginDiscoveryEdgeCases:
    """Test edge cases in plugin discovery."""

    def test_extract_metadata_python37_compatibility(self, tmp_path):
        """Test metadata extraction with Python 3.7 AST nodes."""
        discovery = PluginDiscovery([str(tmp_path)])

        # Python 3.7 uses ast.Str instead of ast.Constant
        code = """
class OldStylePlugin:
    name = "oldstyle"
"""
        tree = ast.parse(code)
        class_node = tree.body[0]

        metadata = discovery._extract_class_metadata(class_node)
        assert metadata is not None

    def test_discover_concurrent_access(self, tmp_path):
        """Test concurrent discovery operations."""
        import concurrent.futures

        # Create multiple plugins
        for i in range(5):
            (tmp_path / f"plugin_{i}.py").write_text(f"""
class Plugin{i}:
    name = "plugin_{i}"
""")

        discovery = PluginDiscovery([str(tmp_path)])

        # Run multiple concurrent discoveries
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(discovery.discover) for _ in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(len(r) == 5 for r in results)

    def test_discover_with_broken_symlinks(self, tmp_path):
        """Test discovery with broken symlinks."""
        # Create a broken symlink
        broken_link = tmp_path / "broken.py"

        try:
            broken_link.symlink_to(tmp_path / "nonexistent.py")

            discovery = PluginDiscovery([str(tmp_path)])
            discovered = discovery.discover()

            # Should handle broken symlinks gracefully
            assert discovered == []
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

    def test_extract_metadata_large_file(self, tmp_path):
        """Test metadata extraction from large file."""
        large_file = tmp_path / "large.py"

        # Create a large file with metadata
        content = """
class LargePlugin:
    name = "large"
    version = "1.0.0"

"""
        # Add lots of methods
        for i in range(1000):
            content += f"    def method_{i}(self): pass\n"

        large_file.write_text(content)

        discovery = PluginDiscovery([str(tmp_path)])
        metadata = discovery._extract_metadata(large_file)

        assert metadata is not None
        assert metadata["name"] == "large"
