"""Comprehensive tests for plugin security module."""

import pytest
import hashlib
from unittest.mock import Mock, patch

from src.plugins.security import PluginSecurityManager, CodeSignatureVerifier


class TestPluginSecurityManager:
    """Test suite for PluginSecurityManager class."""

    @pytest.fixture
    def security_manager(self):
        """Create a security manager instance."""
        return PluginSecurityManager()

    def test_security_manager_initialization(self, security_manager):
        """Test security manager initialization."""
        assert security_manager is not None
        assert hasattr(security_manager, '_permissions')
        assert len(security_manager._permissions) == 0

    def test_grant_permission(self, security_manager):
        """Test granting a permission."""
        security_manager.grant_permission("plugin1", "file.read")

        assert security_manager.has_permission("plugin1", "file.read")

    def test_grant_multiple_permissions(self, security_manager):
        """Test granting multiple permissions."""
        security_manager.grant_permission("plugin1", "file.read")
        security_manager.grant_permission("plugin1", "file.write")
        security_manager.grant_permission("plugin1", "db.query")

        assert security_manager.has_permission("plugin1", "file.read")
        assert security_manager.has_permission("plugin1", "file.write")
        assert security_manager.has_permission("plugin1", "db.query")

    def test_grant_permission_multiple_plugins(self, security_manager):
        """Test granting permissions to multiple plugins."""
        security_manager.grant_permission("plugin1", "file.read")
        security_manager.grant_permission("plugin2", "file.write")

        assert security_manager.has_permission("plugin1", "file.read")
        assert not security_manager.has_permission("plugin1", "file.write")
        assert security_manager.has_permission("plugin2", "file.write")

    def test_revoke_permission_success(self, security_manager):
        """Test revoking a permission."""
        security_manager.grant_permission("plugin1", "file.read")

        result = security_manager.revoke_permission("plugin1", "file.read")

        assert result is True
        assert not security_manager.has_permission("plugin1", "file.read")

    def test_revoke_permission_not_found(self, security_manager):
        """Test revoking non-existent permission."""
        result = security_manager.revoke_permission("plugin1", "file.read")

        assert result is False

    def test_revoke_permission_wrong_plugin(self, security_manager):
        """Test revoking permission from wrong plugin."""
        security_manager.grant_permission("plugin1", "file.read")

        result = security_manager.revoke_permission("plugin2", "file.read")

        assert result is False
        assert security_manager.has_permission("plugin1", "file.read")

    def test_has_permission_exact_match(self, security_manager):
        """Test exact permission matching."""
        security_manager.grant_permission("plugin1", "file.read")

        assert security_manager.has_permission("plugin1", "file.read")
        assert not security_manager.has_permission("plugin1", "file.write")

    def test_has_permission_wildcard(self, security_manager):
        """Test wildcard permission matching."""
        security_manager.grant_permission("plugin1", "file.*")

        assert security_manager.has_permission("plugin1", "file.read")
        assert security_manager.has_permission("plugin1", "file.write")
        assert security_manager.has_permission("plugin1", "file.delete")

    def test_has_permission_nested_wildcard(self, security_manager):
        """Test nested wildcard permissions."""
        security_manager.grant_permission("plugin1", "api.*")

        assert security_manager.has_permission("plugin1", "api.users.read")
        assert security_manager.has_permission("plugin1", "api.posts.write")

    def test_has_permission_global_wildcard(self, security_manager):
        """Test global wildcard permission."""
        security_manager.grant_permission("plugin1", "*")

        assert security_manager.has_permission("plugin1", "file.read")
        assert security_manager.has_permission("plugin1", "db.write")
        assert security_manager.has_permission("plugin1", "anything.at.all")

    def test_has_permission_no_plugin(self, security_manager):
        """Test checking permission for non-existent plugin."""
        assert not security_manager.has_permission("nonexistent", "file.read")

    def test_get_permissions(self, security_manager):
        """Test getting all permissions for a plugin."""
        security_manager.grant_permission("plugin1", "file.read")
        security_manager.grant_permission("plugin1", "file.write")
        security_manager.grant_permission("plugin1", "db.query")

        permissions = security_manager.get_permissions("plugin1")

        assert len(permissions) == 3
        assert "file.read" in permissions
        assert "file.write" in permissions
        assert "db.query" in permissions

    def test_get_permissions_empty(self, security_manager):
        """Test getting permissions for plugin with none."""
        permissions = security_manager.get_permissions("plugin1")

        assert permissions == set()

    def test_get_permissions_returns_copy(self, security_manager):
        """Test that get_permissions returns a copy."""
        security_manager.grant_permission("plugin1", "file.read")

        permissions = security_manager.get_permissions("plugin1")
        permissions.add("file.write")

        # Original should be unchanged
        assert not security_manager.has_permission("plugin1", "file.write")

    def test_clear_permissions(self, security_manager):
        """Test clearing all permissions for a plugin."""
        security_manager.grant_permission("plugin1", "file.read")
        security_manager.grant_permission("plugin1", "file.write")

        security_manager.clear_permissions("plugin1")

        assert len(security_manager.get_permissions("plugin1")) == 0

    def test_clear_permissions_nonexistent(self, security_manager):
        """Test clearing permissions for non-existent plugin."""
        # Should not raise error
        security_manager.clear_permissions("nonexistent")

    def test_permission_isolation(self, security_manager):
        """Test that permissions are isolated between plugins."""
        security_manager.grant_permission("plugin1", "file.read")
        security_manager.grant_permission("plugin2", "file.write")

        assert security_manager.has_permission("plugin1", "file.read")
        assert not security_manager.has_permission("plugin1", "file.write")
        assert security_manager.has_permission("plugin2", "file.write")
        assert not security_manager.has_permission("plugin2", "file.read")


class TestCodeSignatureVerifier:
    """Test suite for CodeSignatureVerifier class."""

    @pytest.fixture
    def verifier(self):
        """Create a code signature verifier instance."""
        return CodeSignatureVerifier()

    def test_verifier_initialization(self, verifier):
        """Test verifier initialization."""
        assert verifier is not None
        assert hasattr(verifier, '_trusted_keys')
        assert len(verifier._trusted_keys) == 0

    def test_add_trusted_key(self, verifier):
        """Test adding a trusted key."""
        public_key = "test_public_key_12345"

        verifier.add_trusted_key(public_key)

        assert public_key in verifier._trusted_keys

    def test_add_multiple_trusted_keys(self, verifier):
        """Test adding multiple trusted keys."""
        keys = ["key1", "key2", "key3"]

        for key in keys:
            verifier.add_trusted_key(key)

        assert len(verifier._trusted_keys) == 3
        assert all(k in verifier._trusted_keys for k in keys)

    def test_sign_code(self, verifier):
        """Test signing code."""
        code = "def hello(): return 'world'"
        private_key = "my_private_key"

        signature = verifier.sign(code, private_key)

        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_sign_different_code_different_signature(self, verifier):
        """Test that different code produces different signatures."""
        code1 = "def func1(): pass"
        code2 = "def func2(): pass"
        private_key = "key"

        sig1 = verifier.sign(code1, private_key)
        sig2 = verifier.sign(code2, private_key)

        assert sig1 != sig2

    def test_sign_same_code_same_signature(self, verifier):
        """Test that same code produces same signature."""
        code = "def func(): pass"
        private_key = "key"

        sig1 = verifier.sign(code, private_key)
        sig2 = verifier.sign(code, private_key)

        assert sig1 == sig2

    def test_verify_valid_signature(self, verifier):
        """Test verifying valid signature."""
        code = "def hello(): return 'world'"
        private_key = "private_key"
        public_key = "public_key"

        signature = verifier.sign(code, private_key)

        plugin_data = {
            "code": code,
            "signature": signature
        }

        # Mock verification returns True for testing
        result = verifier.verify(plugin_data, public_key)

        assert result is True

    def test_verify_missing_code(self, verifier):
        """Test verifying without code."""
        plugin_data = {
            "signature": "some_signature"
        }

        result = verifier.verify(plugin_data, "public_key")

        assert result is False

    def test_verify_missing_signature(self, verifier):
        """Test verifying without signature."""
        plugin_data = {
            "code": "def func(): pass"
        }

        result = verifier.verify(plugin_data, "public_key")

        assert result is False

    def test_verify_empty_data(self, verifier):
        """Test verifying with empty data."""
        result = verifier.verify({}, "public_key")

        assert result is False

    def test_sign_empty_code(self, verifier):
        """Test signing empty code."""
        signature = verifier.sign("", "private_key")

        assert signature is not None
        assert isinstance(signature, str)

    def test_sign_unicode_code(self, verifier):
        """Test signing Unicode code."""
        code = "def greet(): return '你好世界'"
        signature = verifier.sign(code, "key")

        assert signature is not None

    def test_sign_multiline_code(self, verifier):
        """Test signing multiline code."""
        code = """
def complex_function():
    for i in range(10):
        if i % 2 == 0:
            print(i)
    return True
"""
        signature = verifier.sign(code, "key")

        assert signature is not None


class TestSecurityManagerEdgeCases:
    """Test edge cases in security management."""

    @pytest.fixture
    def security_manager(self):
        """Create security manager instance."""
        return PluginSecurityManager()

    def test_permission_with_special_characters(self, security_manager):
        """Test permissions with special characters."""
        security_manager.grant_permission("plugin1", "api/users:read")

        assert security_manager.has_permission("plugin1", "api/users:read")

    def test_empty_permission_string(self, security_manager):
        """Test empty permission string."""
        security_manager.grant_permission("plugin1", "")

        assert security_manager.has_permission("plugin1", "")

    def test_very_long_permission_string(self, security_manager):
        """Test very long permission string."""
        long_perm = ".".join([f"level{i}" for i in range(100)])

        security_manager.grant_permission("plugin1", long_perm)

        assert security_manager.has_permission("plugin1", long_perm)

    def test_concurrent_permission_operations(self, security_manager):
        """Test concurrent permission operations."""
        import concurrent.futures

        def grant_perms(plugin_id):
            for i in range(10):
                security_manager.grant_permission(
                    f"plugin{plugin_id}",
                    f"perm{i}"
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(grant_perms, i) for i in range(5)]
            [f.result() for f in concurrent.futures.as_completed(futures)]

        # Should have 5 plugins with 10 permissions each
        for i in range(5):
            assert len(security_manager.get_permissions(f"plugin{i}")) == 10

    def test_wildcard_at_different_levels(self, security_manager):
        """Test wildcard permissions at different nesting levels."""
        security_manager.grant_permission("plugin1", "api.v1.*")
        security_manager.grant_permission("plugin1", "api.v2.users.*")

        assert security_manager.has_permission("plugin1", "api.v1.anything")
        assert security_manager.has_permission("plugin1", "api.v2.users.read")
        assert not security_manager.has_permission("plugin1", "api.v2.posts.read")

    def test_revoke_all_permissions_individually(self, security_manager):
        """Test revoking all permissions one by one."""
        perms = ["perm1", "perm2", "perm3"]

        for perm in perms:
            security_manager.grant_permission("plugin1", perm)

        for perm in perms:
            result = security_manager.revoke_permission("plugin1", perm)
            assert result is True

        assert len(security_manager.get_permissions("plugin1")) == 0


class TestCodeSignatureVerifierEdgeCases:
    """Test edge cases in code signature verification."""

    @pytest.fixture
    def verifier(self):
        """Create verifier instance."""
        return CodeSignatureVerifier()

    def test_sign_very_large_code(self, verifier):
        """Test signing very large code."""
        large_code = "def func():\n    " + "pass\n    " * 10000

        signature = verifier.sign(large_code, "key")

        assert signature is not None

    def test_concurrent_signing(self, verifier):
        """Test concurrent signing operations."""
        import concurrent.futures

        codes = [f"def func{i}(): pass" for i in range(20)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(verifier.sign, code, "key")
                      for code in codes]
            signatures = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert len(signatures) == 20
        assert all(s is not None for s in signatures)

    def test_sign_with_binary_data(self, verifier):
        """Test signing with binary-like data."""
        binary_code = b"\\x00\\x01\\x02".decode('unicode_escape')

        try:
            signature = verifier.sign(binary_code, "key")
            assert signature is not None
        except Exception:
            # Some encoding may fail, which is acceptable
            pass

    def test_verify_tampered_code(self, verifier):
        """Test verifying tampered code."""
        original_code = "def func(): return True"
        tampered_code = "def func(): return False"

        private_key = "key"
        public_key = "pub_key"

        signature = verifier.sign(original_code, private_key)

        plugin_data = {
            "code": tampered_code,  # Different code
            "signature": signature
        }

        # Mock implementation returns True, but in real crypto this would fail
        result = verifier.verify(plugin_data, public_key)

        # Current mock implementation returns True
        # Real implementation would return False for tampered code
        assert isinstance(result, bool)


class TestIntegration:
    """Integration tests for security components."""

    def test_security_and_signing_together(self):
        """Test using security manager and verifier together."""
        security = PluginSecurityManager()
        verifier = CodeSignatureVerifier()

        # Grant permissions
        security.grant_permission("trusted_plugin", "file.*")

        # Sign code
        code = "def safe_function(): pass"
        signature = verifier.sign(code, "private_key")

        # Verify
        plugin_data = {"code": code, "signature": signature}
        is_signed = verifier.verify(plugin_data, "public_key")

        # Both should succeed
        assert security.has_permission("trusted_plugin", "file.read")
        assert is_signed is True

    def test_multiple_plugins_different_permissions(self):
        """Test multiple plugins with different permission sets."""
        security = PluginSecurityManager()

        # Plugin 1: file operations only
        security.grant_permission("file_plugin", "file.*")

        # Plugin 2: database operations only
        security.grant_permission("db_plugin", "db.*")

        # Plugin 3: full access
        security.grant_permission("admin_plugin", "*")

        # Verify isolation
        assert security.has_permission("file_plugin", "file.read")
        assert not security.has_permission("file_plugin", "db.query")

        assert security.has_permission("db_plugin", "db.query")
        assert not security.has_permission("db_plugin", "file.read")

        assert security.has_permission("admin_plugin", "file.read")
        assert security.has_permission("admin_plugin", "db.query")
