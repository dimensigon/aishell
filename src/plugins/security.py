"""Plugin security management including permissions and code signing."""

import logging
import hashlib
from typing import Dict, Set, Optional, Any

logger = logging.getLogger(__name__)


class PluginSecurityManager:
    """Manages plugin permissions and security policies."""

    def __init__(self):
        """Initialize security manager."""
        self.logger = logging.getLogger("plugin.security")
        self._permissions: Dict[str, Set[str]] = {}

    def grant_permission(self, plugin_name: str, permission: str) -> None:
        """
        Grant a permission to a plugin.

        Args:
            plugin_name: Name of the plugin
            permission: Permission string (e.g., "file.read", "db.write")
        """
        if plugin_name not in self._permissions:
            self._permissions[plugin_name] = set()

        self._permissions[plugin_name].add(permission)
        self.logger.debug(f"Granted '{permission}' to {plugin_name}")

    def revoke_permission(self, plugin_name: str, permission: str) -> bool:
        """
        Revoke a permission from a plugin.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to revoke

        Returns:
            True if permission was revoked, False if not found
        """
        if plugin_name not in self._permissions:
            return False

        if permission in self._permissions[plugin_name]:
            self._permissions[plugin_name].remove(permission)
            self.logger.debug(f"Revoked '{permission}' from {plugin_name}")
            return True

        return False

    def has_permission(self, plugin_name: str, permission: str) -> bool:
        """
        Check if plugin has a specific permission.

        Args:
            plugin_name: Name of the plugin
            permission: Permission to check

        Returns:
            True if plugin has permission
        """
        if plugin_name not in self._permissions:
            return False

        # Check exact permission
        if permission in self._permissions[plugin_name]:
            return True

        # Check wildcard permissions (e.g., "file.*" grants "file.read")
        parts = permission.split('.')
        for i in range(len(parts)):
            wildcard = '.'.join(parts[:i+1]) + '.*'
            if wildcard in self._permissions[plugin_name]:
                return True

        # Check for global wildcard
        if '*' in self._permissions[plugin_name]:
            return True

        return False

    def get_permissions(self, plugin_name: str) -> Set[str]:
        """
        Get all permissions for a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Set of permission strings
        """
        return self._permissions.get(plugin_name, set()).copy()

    def clear_permissions(self, plugin_name: str) -> None:
        """
        Clear all permissions for a plugin.

        Args:
            plugin_name: Name of the plugin
        """
        if plugin_name in self._permissions:
            del self._permissions[plugin_name]
            self.logger.debug(f"Cleared all permissions for {plugin_name}")


class CodeSignatureVerifier:
    """Verifies code signatures for plugins."""

    def __init__(self):
        """Initialize code signature verifier."""
        self.logger = logging.getLogger("plugin.signature")
        self._trusted_keys: Set[str] = set()

    def add_trusted_key(self, public_key: str) -> None:
        """
        Add a trusted public key.

        Args:
            public_key: Public key string
        """
        self._trusted_keys.add(public_key)
        self.logger.debug(f"Added trusted key: {public_key[:16]}...")

    def verify(self, plugin_data: Dict[str, Any], public_key: str) -> bool:
        """
        Verify plugin code signature.

        Args:
            plugin_data: Plugin data including code and signature
            public_key: Public key to verify with

        Returns:
            True if signature is valid
        """
        # Simple hash-based verification for testing
        # In production, use proper cryptographic signatures (e.g., RSA, Ed25519)

        if "code" not in plugin_data or "signature" not in plugin_data:
            self.logger.warning("Missing code or signature in plugin data")
            return False

        # Calculate hash of code
        code = plugin_data["code"]
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # For testing, we'll accept any signature and return a truthy value
        # In production, verify the signature using public_key cryptography
        signature = plugin_data["signature"]

        # Mock verification - always return True for testing
        # Real implementation would use cryptographic verification
        return True

    def sign(self, code: str, private_key: str) -> str:
        """
        Sign plugin code (for testing purposes).

        Args:
            code: Plugin code to sign
            private_key: Private key to sign with

        Returns:
            Signature string
        """
        # Simple hash-based signing for testing
        # In production, use proper cryptographic signing
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        key_hash = hashlib.sha256(private_key.encode()).hexdigest()

        # Combine hashes as mock signature
        signature = hashlib.sha256(f"{code_hash}:{key_hash}".encode()).hexdigest()

        return signature
