"""Comprehensive tests for plugin sandbox module."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.plugins.sandbox import PluginSandbox, ResourceLimiter


class TestPluginSandbox:
    """Test suite for PluginSandbox class."""

    @pytest.fixture
    def sandbox(self):
        """Create a sandbox instance."""
        return PluginSandbox()

    def test_sandbox_initialization(self, sandbox):
        """Test sandbox initialization."""
        assert sandbox is not None
        assert hasattr(sandbox, '_allowed_paths')
        assert hasattr(sandbox, '_denied_paths')

        # Should have default denied paths
        assert len(sandbox._denied_paths) > 0

    def test_default_denied_paths(self, sandbox):
        """Test that system paths are denied by default."""
        denied_paths = sandbox._denied_paths

        # Check for system directories
        assert any("/etc" in str(p) for p in denied_paths)
        assert any("/sys" in str(p) for p in denied_paths)
        assert any("/proc" in str(p) for p in denied_paths)

    def test_allow_path(self, sandbox, tmp_path):
        """Test allowing a path."""
        test_path = str(tmp_path / "allowed")

        sandbox.allow_path(test_path)

        assert any(test_path in str(p) for p in sandbox._allowed_paths)

    def test_deny_path(self, sandbox, tmp_path):
        """Test denying a path."""
        test_path = str(tmp_path / "denied")

        sandbox.deny_path(test_path)

        assert any(test_path in str(p) for p in sandbox._denied_paths)

    def test_can_access_allowed_path(self, sandbox, tmp_path):
        """Test accessing allowed path."""
        test_path = tmp_path / "allowed"
        test_path.mkdir()

        sandbox.allow_path(str(tmp_path))

        assert sandbox.can_access(str(test_path)) is True

    def test_can_access_denied_path(self, sandbox):
        """Test accessing denied path."""
        result = sandbox.can_access("/etc/passwd")

        assert result is False

    def test_can_access_subdirectory_of_allowed(self, sandbox, tmp_path):
        """Test accessing subdirectory of allowed path."""
        parent = tmp_path / "parent"
        child = parent / "child"
        child.mkdir(parents=True)

        sandbox.allow_path(str(parent))

        # Child should also be accessible
        assert sandbox.can_access(str(child)) is True

    def test_can_access_subdirectory_of_denied(self, sandbox):
        """Test that subdirectories of denied paths are also denied."""
        result = sandbox.can_access("/etc/ssh/sshd_config")

        assert result is False

    def test_can_access_not_explicitly_allowed(self, sandbox, tmp_path):
        """Test accessing path that's not explicitly allowed."""
        test_path = tmp_path / "not_allowed"
        test_path.mkdir()

        # Not in allowed list, should be denied by default
        result = sandbox.can_access(str(test_path))

        assert result is False

    def test_can_access_with_symlink(self, sandbox, tmp_path):
        """Test accessing symlinked paths."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()

        link_dir = tmp_path / "link"

        try:
            link_dir.symlink_to(real_dir)

            sandbox.allow_path(str(real_dir))

            # Symlink should resolve to real path
            assert sandbox.can_access(str(link_dir)) is True
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

    def test_can_access_relative_path(self, sandbox, tmp_path):
        """Test accessing with relative paths."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        sandbox.allow_path(str(test_dir))

        # Change to tmp_path and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = sandbox.can_access("test")
            # Will resolve to absolute path
            assert result is True
        finally:
            os.chdir(original_cwd)

    def test_can_access_nonexistent_path(self, sandbox):
        """Test accessing non-existent path."""
        result = sandbox.can_access("/nonexistent/path/that/does/not/exist")

        # Should default to denied
        assert result is False

    def test_clear_allowed_paths(self, sandbox, tmp_path):
        """Test clearing all allowed paths."""
        sandbox.allow_path(str(tmp_path / "path1"))
        sandbox.allow_path(str(tmp_path / "path2"))

        assert len(sandbox._allowed_paths) > 0

        sandbox.clear_allowed_paths()

        assert len(sandbox._allowed_paths) == 0

    def test_get_allowed_paths(self, sandbox, tmp_path):
        """Test getting allowed paths."""
        path1 = tmp_path / "path1"
        path2 = tmp_path / "path2"

        sandbox.allow_path(str(path1))
        sandbox.allow_path(str(path2))

        allowed = sandbox.get_allowed_paths()

        assert len(allowed) == 2
        # Returns copy, not original
        allowed.clear()
        assert len(sandbox._allowed_paths) == 2

    def test_allow_multiple_paths(self, sandbox, tmp_path):
        """Test allowing multiple paths."""
        paths = [tmp_path / f"path{i}" for i in range(5)]

        for path in paths:
            path.mkdir()
            sandbox.allow_path(str(path))

        for path in paths:
            assert sandbox.can_access(str(path)) is True

    def test_deny_overrides_allow(self, sandbox, tmp_path):
        """Test that denied path overrides allowed."""
        test_path = tmp_path / "test"
        test_path.mkdir()

        sandbox.allow_path(str(test_path))
        sandbox.deny_path(str(test_path))

        # Denied should take precedence
        assert sandbox.can_access(str(test_path)) is False


class TestResourceLimiter:
    """Test suite for ResourceLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create a resource limiter instance."""
        return ResourceLimiter(max_memory_mb=100, max_cpu_percent=50)

    def test_limiter_initialization(self, limiter):
        """Test limiter initialization."""
        assert limiter.max_memory_mb == 100
        assert limiter.max_cpu_percent == 50
        assert len(limiter._usage) == 0

    def test_limiter_default_values(self):
        """Test limiter with default values."""
        limiter = ResourceLimiter()

        assert limiter.max_memory_mb == 100
        assert limiter.max_cpu_percent == 50

    def test_track_usage(self, limiter):
        """Test tracking resource usage."""
        limiter.track_usage("plugin1", memory_mb=50, cpu_percent=25)

        usage = limiter.get_usage("plugin1")

        assert usage is not None
        assert usage["memory_mb"] == 50
        assert usage["cpu_percent"] == 25

    def test_track_usage_multiple_plugins(self, limiter):
        """Test tracking usage for multiple plugins."""
        limiter.track_usage("plugin1", memory_mb=30, cpu_percent=20)
        limiter.track_usage("plugin2", memory_mb=60, cpu_percent=40)

        usage1 = limiter.get_usage("plugin1")
        usage2 = limiter.get_usage("plugin2")

        assert usage1["memory_mb"] == 30
        assert usage2["memory_mb"] == 60

    def test_within_limits_below(self, limiter):
        """Test plugin within resource limits."""
        limiter.track_usage("plugin1", memory_mb=50, cpu_percent=25)

        assert limiter.within_limits("plugin1") is True

    def test_within_limits_at_limit(self, limiter):
        """Test plugin at resource limits."""
        limiter.track_usage("plugin1", memory_mb=100, cpu_percent=50)

        assert limiter.within_limits("plugin1") is True

    def test_within_limits_memory_exceeded(self, limiter):
        """Test plugin exceeding memory limit."""
        limiter.track_usage("plugin1", memory_mb=150, cpu_percent=25)

        assert limiter.within_limits("plugin1") is False

    def test_within_limits_cpu_exceeded(self, limiter):
        """Test plugin exceeding CPU limit."""
        limiter.track_usage("plugin1", memory_mb=50, cpu_percent=75)

        assert limiter.within_limits("plugin1") is False

    def test_within_limits_both_exceeded(self, limiter):
        """Test plugin exceeding both limits."""
        limiter.track_usage("plugin1", memory_mb=150, cpu_percent=75)

        assert limiter.within_limits("plugin1") is False

    def test_within_limits_no_tracking(self, limiter):
        """Test checking limits for untracked plugin."""
        # Should return True if no usage tracked
        assert limiter.within_limits("unknown_plugin") is True

    def test_get_usage_not_tracked(self, limiter):
        """Test getting usage for untracked plugin."""
        usage = limiter.get_usage("unknown_plugin")

        assert usage is None

    def test_clear_usage(self, limiter):
        """Test clearing usage for a plugin."""
        limiter.track_usage("plugin1", memory_mb=50, cpu_percent=25)

        limiter.clear_usage("plugin1")

        assert limiter.get_usage("plugin1") is None

    def test_clear_usage_not_tracked(self, limiter):
        """Test clearing usage for untracked plugin."""
        # Should not raise error
        limiter.clear_usage("unknown_plugin")

    def test_update_usage(self, limiter):
        """Test updating usage for same plugin."""
        limiter.track_usage("plugin1", memory_mb=50, cpu_percent=25)
        limiter.track_usage("plugin1", memory_mb=75, cpu_percent=30)

        usage = limiter.get_usage("plugin1")

        # Should update to new values
        assert usage["memory_mb"] == 75
        assert usage["cpu_percent"] == 30

    def test_zero_usage(self, limiter):
        """Test tracking zero usage."""
        limiter.track_usage("plugin1", memory_mb=0, cpu_percent=0)

        assert limiter.within_limits("plugin1") is True

    def test_custom_limits(self):
        """Test limiter with custom limits."""
        limiter = ResourceLimiter(max_memory_mb=200, max_cpu_percent=75)

        limiter.track_usage("plugin1", memory_mb=150, cpu_percent=60)

        assert limiter.within_limits("plugin1") is True

        limiter.track_usage("plugin1", memory_mb=250, cpu_percent=60)

        assert limiter.within_limits("plugin1") is False


class TestSandboxEdgeCases:
    """Test edge cases in sandbox functionality."""

    @pytest.fixture
    def sandbox(self):
        """Create sandbox instance."""
        return PluginSandbox()

    def test_can_access_with_dots(self, sandbox, tmp_path):
        """Test path with .. components."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        sandbox.allow_path(str(allowed))

        # Try to access parent via ..
        test_path = str(allowed / ".." / "allowed")

        # Should resolve and allow
        result = sandbox.can_access(test_path)
        assert result is True

    def test_can_access_empty_string(self, sandbox):
        """Test accessing empty path."""
        result = sandbox.can_access("")

        assert result is False

    def test_concurrent_path_operations(self, sandbox, tmp_path):
        """Test concurrent path allow/deny operations."""
        import concurrent.futures

        paths = [tmp_path / f"path{i}" for i in range(10)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(sandbox.allow_path, str(p))
                      for p in paths]
            [f.result() for f in concurrent.futures.as_completed(futures)]

        # All paths should be allowed
        assert len(sandbox._allowed_paths) == 10

    def test_concurrent_access_checks(self, sandbox, tmp_path):
        """Test concurrent access checks."""
        import concurrent.futures

        test_path = tmp_path / "test"
        test_path.mkdir()
        sandbox.allow_path(str(test_path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(sandbox.can_access, str(test_path))
                      for _ in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should return True
        assert all(results)


class TestResourceLimiterEdgeCases:
    """Test edge cases in resource limiting."""

    @pytest.fixture
    def limiter(self):
        """Create limiter instance."""
        return ResourceLimiter()

    def test_concurrent_usage_tracking(self, limiter):
        """Test concurrent usage tracking."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(limiter.track_usage, f"plugin{i}", i*10, i*5)
                for i in range(10)
            ]
            [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should be tracked
        for i in range(10):
            assert limiter.get_usage(f"plugin{i}") is not None

    def test_negative_values(self, limiter):
        """Test tracking negative values."""
        # Should still track but fail validation
        limiter.track_usage("plugin1", memory_mb=-10, cpu_percent=-5)

        usage = limiter.get_usage("plugin1")

        assert usage["memory_mb"] == -10
        assert usage["cpu_percent"] == -5

    def test_very_large_limits(self):
        """Test limiter with very large limits."""
        limiter = ResourceLimiter(max_memory_mb=1000000, max_cpu_percent=100)

        limiter.track_usage("plugin1", memory_mb=500000, cpu_percent=90)

        assert limiter.within_limits("plugin1") is True

    def test_float_values(self, limiter):
        """Test tracking float values."""
        limiter.track_usage("plugin1", memory_mb=50.5, cpu_percent=25.7)

        usage = limiter.get_usage("plugin1")

        assert usage["memory_mb"] == 50.5
        assert usage["cpu_percent"] == 25.7


class TestIntegration:
    """Integration tests for sandbox and resource limiter."""

    def test_sandbox_and_limiter_together(self, tmp_path):
        """Test using sandbox and limiter together."""
        sandbox = PluginSandbox()
        limiter = ResourceLimiter()

        # Set up sandbox
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        sandbox.allow_path(str(plugin_dir))

        # Track resources
        limiter.track_usage("test_plugin", memory_mb=50, cpu_percent=25)

        # Verify both work
        assert sandbox.can_access(str(plugin_dir)) is True
        assert limiter.within_limits("test_plugin") is True

    def test_multiple_plugins_isolated(self, tmp_path):
        """Test that multiple plugins are properly isolated."""
        sandbox = PluginSandbox()
        limiter = ResourceLimiter()

        # Create separate directories for each plugin
        plugin1_dir = tmp_path / "plugin1"
        plugin2_dir = tmp_path / "plugin2"
        plugin1_dir.mkdir()
        plugin2_dir.mkdir()

        # Allow only plugin1 directory
        sandbox.allow_path(str(plugin1_dir))

        # Track resources for both
        limiter.track_usage("plugin1", memory_mb=30, cpu_percent=20)
        limiter.track_usage("plugin2", memory_mb=40, cpu_percent=30)

        # plugin1 can access its directory
        assert sandbox.can_access(str(plugin1_dir)) is True

        # plugin2 cannot access plugin1's directory
        assert sandbox.can_access(str(plugin2_dir)) is False

        # Both within limits
        assert limiter.within_limits("plugin1") is True
        assert limiter.within_limits("plugin2") is True
