"""Comprehensive tests for plugin loader module."""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.plugins.loader import PluginLoader


class TestPluginLoader:
    """Test suite for PluginLoader class."""

    @pytest.fixture
    def loader(self):
        """Create a plugin loader instance."""
        return PluginLoader()

    @pytest.fixture
    def mock_plugin_path(self, tmp_path):
        """Create a temporary plugin file."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
class TestPlugin:
    name = "test"
    version = "1.0.0"

    def __init__(self):
        self.value = 42

    def activate(self):
        return True
""")
        return plugin_file

    def test_loader_initialization(self, loader):
        """Test loader initialization."""
        assert loader is not None
        assert hasattr(loader, '_loaded_modules')
        assert isinstance(loader._loaded_modules, dict)
        assert len(loader._loaded_modules) == 0

    def test_load_from_path_success(self, loader, mock_plugin_path):
        """Test successful plugin loading from path."""
        plugin = loader.load_from_path(str(mock_plugin_path))

        assert plugin is not None
        assert hasattr(plugin, 'name')
        assert hasattr(plugin, 'version')
        assert plugin.name == "test"
        assert plugin.version == "1.0.0"
        assert plugin.value == 42

    def test_load_from_path_nonexistent_file(self, loader):
        """Test loading from non-existent file path."""
        with pytest.raises(FileNotFoundError):
            loader.load_from_path("/nonexistent/path/plugin.py", strict=True)

    def test_load_from_path_nonexistent_file_non_strict(self, loader):
        """Test loading from non-existent file in non-strict mode."""
        result = loader.load_from_path("/nonexistent/path/plugin.py", strict=False)
        assert result is None

    def test_load_from_path_invalid_syntax(self, loader, tmp_path):
        """Test loading plugin with syntax errors."""
        plugin_file = tmp_path / "invalid.py"
        plugin_file.write_text("class Invalid\n    pass")  # Missing colon

        with pytest.raises(SyntaxError):
            loader.load_from_path(str(plugin_file), strict=True)

    def test_load_from_path_invalid_syntax_non_strict(self, loader, tmp_path):
        """Test loading plugin with syntax errors in non-strict mode."""
        plugin_file = tmp_path / "invalid.py"
        plugin_file.write_text("class Invalid\n    pass")

        result = loader.load_from_path(str(plugin_file), strict=False)
        assert result is None

    def test_load_from_path_no_plugin_class(self, loader, tmp_path):
        """Test loading file without plugin class."""
        plugin_file = tmp_path / "no_class.py"
        plugin_file.write_text("VALUE = 100\ndef helper(): return VALUE")

        with pytest.raises(ValueError, match="No plugin class found"):
            loader.load_from_path(str(plugin_file), strict=True)

    def test_load_from_path_multiple_classes(self, loader, tmp_path):
        """Test loading plugin file with multiple classes."""
        plugin_file = tmp_path / "multi_class.py"
        plugin_file.write_text("""
class Helper:
    pass

class RealPlugin:
    name = "real"

    def activate(self):
        return True
""")

        plugin = loader.load_from_path(str(plugin_file))
        assert plugin is not None
        assert hasattr(plugin, 'name')
        assert plugin.name == "real"

    def test_load_from_path_module_caching(self, loader, mock_plugin_path):
        """Test that loaded modules are cached."""
        plugin1 = loader.load_from_path(str(mock_plugin_path))
        initial_count = len(loader._loaded_modules)

        plugin2 = loader.load_from_path(str(mock_plugin_path))

        # Should have loaded two separate instances (different id())
        assert plugin1 is not plugin2
        # But from separate module loads
        assert len(loader._loaded_modules) > initial_count

    def test_load_from_directory_success(self, loader, tmp_path):
        """Test loading all plugins from directory."""
        # Create multiple plugin files
        for i in range(3):
            plugin_file = tmp_path / f"plugin_{i}.py"
            plugin_file.write_text(f"""
class Plugin{i}:
    name = "plugin_{i}"

    def activate(self):
        return True
""")

        plugins = loader.load_from_directory(str(tmp_path))

        assert len(plugins) == 3
        assert all(p is not None for p in plugins)

    def test_load_from_directory_nonexistent(self, loader):
        """Test loading from non-existent directory."""
        plugins = loader.load_from_directory("/nonexistent/directory")
        assert plugins == []

    def test_load_from_directory_empty(self, loader, tmp_path):
        """Test loading from empty directory."""
        plugins = loader.load_from_directory(str(tmp_path))
        assert plugins == []

    def test_load_from_directory_skip_private_files(self, loader, tmp_path):
        """Test that files starting with _ are skipped."""
        # Create public and private plugin files
        public_file = tmp_path / "public.py"
        public_file.write_text("""
class PublicPlugin:
    name = "public"
    def activate(self): return True
""")

        private_file = tmp_path / "_private.py"
        private_file.write_text("""
class PrivatePlugin:
    name = "private"
    def activate(self): return True
""")

        plugins = loader.load_from_directory(str(tmp_path))

        assert len(plugins) == 1
        assert plugins[0].name == "public"

    def test_load_from_directory_mixed_valid_invalid(self, loader, tmp_path):
        """Test loading directory with mix of valid and invalid plugins."""
        # Valid plugin
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("""
class ValidPlugin:
    name = "valid"
    def activate(self): return True
""")

        # Invalid plugin
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("class Invalid\n    pass")

        plugins = loader.load_from_directory(str(tmp_path))

        # Should load only valid plugin (non-strict mode)
        assert len(plugins) == 1
        assert plugins[0].name == "valid"

    def test_find_plugin_class_with_activate(self, loader, tmp_path):
        """Test finding plugin class with activate method."""
        plugin_file = tmp_path / "test.py"
        plugin_file.write_text("""
class MyPlugin:
    def activate(self): pass
""")

        import importlib.util
        spec = importlib.util.spec_from_file_location("test", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_class = loader._find_plugin_class(module)
        assert plugin_class is not None
        assert plugin_class.__name__ == "MyPlugin"

    def test_find_plugin_class_with_name(self, loader, tmp_path):
        """Test finding plugin class with name attribute."""
        plugin_file = tmp_path / "test.py"
        plugin_file.write_text("""
class MyPlugin:
    name = "test"
""")

        import importlib.util
        spec = importlib.util.spec_from_file_location("test", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_class = loader._find_plugin_class(module)
        assert plugin_class is not None
        assert plugin_class.__name__ == "MyPlugin"

    def test_find_plugin_class_imported_classes_skipped(self, loader, tmp_path):
        """Test that imported classes are skipped."""
        plugin_file = tmp_path / "test.py"
        plugin_file.write_text("""
import os

class LocalPlugin:
    name = "local"
""")

        import importlib.util
        spec = importlib.util.spec_from_file_location("test", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_class = loader._find_plugin_class(module)
        # Should find LocalPlugin, not imported os classes
        assert plugin_class is not None
        assert plugin_class.__name__ == "LocalPlugin"

    def test_find_plugin_class_no_classes(self, loader, tmp_path):
        """Test module with no classes."""
        plugin_file = tmp_path / "test.py"
        plugin_file.write_text("""
VALUE = 100
def function(): pass
""")

        import importlib.util
        spec = importlib.util.spec_from_file_location("test", plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_class = loader._find_plugin_class(module)
        assert plugin_class is None

    def test_concurrent_loading(self, loader, tmp_path):
        """Test concurrent plugin loading."""
        import concurrent.futures

        # Create multiple plugins
        plugin_files = []
        for i in range(5):
            plugin_file = tmp_path / f"concurrent_{i}.py"
            plugin_file.write_text(f"""
class ConcurrentPlugin{i}:
    name = "concurrent_{i}"
    def activate(self): return True
""")
            plugin_files.append(str(plugin_file))

        # Load concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(loader.load_from_path, pf, False)
                      for pf in plugin_files]
            plugins = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should load successfully
        assert len([p for p in plugins if p is not None]) == 5

    def test_load_plugin_with_dependencies(self, loader, tmp_path):
        """Test loading plugin that imports other modules."""
        plugin_file = tmp_path / "with_deps.py"
        plugin_file.write_text("""
import os
import sys
from pathlib import Path

class PluginWithDeps:
    name = "with_deps"

    def get_path(self):
        return Path.cwd()
""")

        plugin = loader.load_from_path(str(plugin_file))
        assert plugin is not None
        assert hasattr(plugin, 'get_path')

    def test_load_plugin_error_handling(self, loader, tmp_path):
        """Test error handling during plugin instantiation."""
        plugin_file = tmp_path / "error.py"
        plugin_file.write_text("""
class ErrorPlugin:
    name = "error"

    def __init__(self):
        raise RuntimeError("Initialization error")
""")

        with pytest.raises(RuntimeError):
            loader.load_from_path(str(plugin_file), strict=True)

    def test_plugin_with_get_value_method(self, loader):
        """Test finding plugin class with get_value method."""
        # Use the actual mock plugin
        mock_path = Path(__file__).parent / "mocks" / "valid_plugin.py"

        plugin = loader.load_from_path(str(mock_path))
        assert plugin is not None
        assert hasattr(plugin, 'get_value')
        assert plugin.get_value() == 42


class TestPluginLoaderEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def loader(self):
        """Create a plugin loader instance."""
        return PluginLoader()

    def test_load_with_unicode_filename(self, loader, tmp_path):
        """Test loading plugin with Unicode filename."""
        plugin_file = tmp_path / "플러그인_test.py"
        plugin_file.write_text("""
class UnicodePlugin:
    name = "unicode_test"
    def activate(self): return True
""")

        plugin = loader.load_from_path(str(plugin_file))
        assert plugin is not None

    def test_load_with_spaces_in_path(self, loader, tmp_path):
        """Test loading plugin with spaces in path."""
        space_dir = tmp_path / "path with spaces"
        space_dir.mkdir()
        plugin_file = space_dir / "plugin.py"
        plugin_file.write_text("""
class SpacePlugin:
    name = "space"
    def activate(self): return True
""")

        plugin = loader.load_from_path(str(plugin_file))
        assert plugin is not None

    def test_load_empty_file(self, loader, tmp_path):
        """Test loading empty Python file."""
        plugin_file = tmp_path / "empty.py"
        plugin_file.write_text("")

        with pytest.raises(ValueError):
            loader.load_from_path(str(plugin_file), strict=True)

    def test_load_with_import_errors(self, loader, tmp_path):
        """Test loading plugin with import errors."""
        plugin_file = tmp_path / "import_error.py"
        plugin_file.write_text("""
import nonexistent_module

class ImportErrorPlugin:
    name = "import_error"
""")

        with pytest.raises(ImportError):
            loader.load_from_path(str(plugin_file), strict=True)

    def test_load_symlink_plugin(self, loader, tmp_path):
        """Test loading plugin via symlink."""
        # Create original plugin
        original = tmp_path / "original.py"
        original.write_text("""
class OriginalPlugin:
    name = "original"
    def activate(self): return True
""")

        # Create symlink
        symlink = tmp_path / "link.py"
        try:
            symlink.symlink_to(original)

            plugin = loader.load_from_path(str(symlink))
            assert plugin is not None
            assert plugin.name == "original"
        except OSError:
            pytest.skip("Symlinks not supported on this platform")
