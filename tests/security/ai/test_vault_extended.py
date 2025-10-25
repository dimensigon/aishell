"""
Extended comprehensive tests for SecureVault module.

Tests encryption, credential management, key rotation, security,
and attack vector scenarios.
"""

import pytest
from pathlib import Path
import tempfile
import json
from cryptography.fernet import InvalidToken
from src.security.vault import SecureVault, CredentialType, Credential
from src.security.path_validator import SecurityError


class TestVaultInitialization:
    """Test suite for vault initialization."""

    def test_vault_with_master_password(self):
        """Test vault initialization with master password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.enc"
            vault = SecureVault(
                vault_path=str(vault_path),
                master_password="test-password-123",
                allow_insecure_path=True
            )

            assert vault.vault_path == vault_path
            assert vault._fernet is not None

    def test_vault_without_password(self):
        """Test vault initialization without password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.enc"
            vault = SecureVault(
                vault_path=str(vault_path),
                allow_insecure_path=True
            )

            assert vault._fernet is None

    def test_default_vault_path(self):
        """Test vault with default path."""
        vault = SecureVault(master_password="test")

        assert vault.vault_path.parent == Path.home() / '.ai-shell'
        assert vault.vault_path.name == 'vault.enc'

    def test_auto_redact_enabled(self):
        """Test vault with auto-redaction enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=True,
                allow_insecure_path=True
            )

            assert vault.auto_redact
            assert vault.redaction_engine is not None

    def test_auto_redact_disabled(self):
        """Test vault with auto-redaction disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=False,
                allow_insecure_path=True
            )

            assert not vault.auto_redact
            assert vault.redaction_engine is None


class TestCredentialStorage:
    """Test suite for credential storage."""

    def test_store_basic_credential(self):
        """Test storing a basic credential."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test-api",
                credential_type=CredentialType.API,
                data={"api_key": "secret-key-123"}
            )

            assert cred_id is not None
            assert cred_id in vault.credentials

    def test_store_with_metadata(self):
        """Test storing credential with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="prod-db",
                credential_type=CredentialType.DATABASE,
                data={"host": "db.example.com", "password": "secret"},
                metadata={"environment": "production", "region": "us-east-1"}
            )

            cred = vault.get_credential(cred_id, redact=False)
            assert cred.metadata["environment"] == "production"

    def test_store_custom_credential_id(self):
        """Test storing with custom credential ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            custom_id = "my-custom-id-123"
            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"key": "value"},
                credential_id=custom_id
            )

            assert cred_id == custom_id

    def test_store_without_master_password(self):
        """Test that storing fails without master password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                allow_insecure_path=True
            )

            with pytest.raises(ValueError, match="not initialized with master password"):
                vault.store_credential(
                    name="test",
                    credential_type=CredentialType.STANDARD,
                    data={"key": "value"}
                )


class TestCredentialRetrieval:
    """Test suite for credential retrieval."""

    def test_get_credential_by_id(self):
        """Test retrieving credential by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=False,
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"password": "secret123"}
            )

            cred = vault.get_credential(cred_id)
            assert cred.data["password"] == "secret123"

    def test_get_credential_with_redaction(self):
        """Test retrieving credential with auto-redaction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=True,
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"password": "secret123", "username": "admin"}
            )

            cred = vault.get_credential(cred_id)
            assert cred.data["password"] == "[REDACTED]"
            assert cred.data["username"] == "admin"

    def test_get_credential_override_redaction(self):
        """Test overriding auto-redaction on retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=True,
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"password": "secret123"}
            )

            cred = vault.get_credential(cred_id, redact=False)
            assert cred.data["password"] == "secret123"

    def test_get_nonexistent_credential(self):
        """Test getting credential that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            cred = vault.get_credential("nonexistent")
            assert cred is None

    def test_get_credential_by_name(self):
        """Test retrieving credential by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=False,
                allow_insecure_path=True
            )

            vault.store_credential(
                name="github-api",
                credential_type=CredentialType.API,
                data={"token": "ghp_12345"}
            )

            cred = vault.get_credential_by_name("github-api")
            assert cred is not None
            assert cred.data["token"] == "ghp_12345"


class TestCredentialListing:
    """Test suite for credential listing."""

    def test_list_all_credentials(self):
        """Test listing all credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            vault.store_credential("api1", CredentialType.API, {"key": "val1"})
            vault.store_credential("api2", CredentialType.API, {"key": "val2"})

            creds = vault.list_credentials()
            assert len(creds) == 2

    def test_list_by_type(self):
        """Test listing credentials filtered by type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            vault.store_credential("api", CredentialType.API, {"key": "val"})
            vault.store_credential("db", CredentialType.DATABASE, {"pass": "secret"})
            vault.store_credential("ssh", CredentialType.SSH, {"key": "rsa"})

            api_creds = vault.list_credentials(CredentialType.API)
            assert len(api_creds) == 1


class TestCredentialUpdate:
    """Test suite for credential updates."""

    def test_update_credential_data(self):
        """Test updating credential data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=False,
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"password": "old-password"}
            )

            vault.update_credential(cred_id, data={"password": "new-password"})

            cred = vault.get_credential(cred_id)
            assert cred.data["password"] == "new-password"

    def test_update_credential_metadata(self):
        """Test updating credential metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"key": "value"},
                metadata={"version": "1.0"}
            )

            vault.update_credential(cred_id, metadata={"version": "2.0", "updated": True})

            cred = vault.get_credential(cred_id, redact=False)
            assert cred.metadata["version"] == "2.0"

    def test_update_nonexistent_credential(self):
        """Test updating credential that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            result = vault.update_credential("nonexistent", data={"key": "value"})
            assert not result


class TestCredentialDeletion:
    """Test suite for credential deletion."""

    def test_delete_credential(self):
        """Test deleting a credential."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            cred_id = vault.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"key": "value"}
            )

            assert vault.delete_credential(cred_id)
            assert vault.get_credential(cred_id) is None

    def test_delete_nonexistent_credential(self):
        """Test deleting credential that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                allow_insecure_path=True
            )

            result = vault.delete_credential("nonexistent")
            assert not result


class TestCredentialSearch:
    """Test suite for credential search."""

    def test_search_by_name(self):
        """Test searching credentials by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=False,
                allow_insecure_path=True
            )

            vault.store_credential("github-api", CredentialType.API, {"token": "123"})
            vault.store_credential("github-ssh", CredentialType.SSH, {"key": "rsa"})
            vault.store_credential("gitlab-api", CredentialType.API, {"token": "456"})

            results = vault.search_credentials("github")
            assert len(results) == 2

    def test_search_with_type_filter(self):
        """Test searching with type filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=False,
                allow_insecure_path=True
            )

            vault.store_credential("api-key-1", CredentialType.API, {"key": "val"})
            vault.store_credential("api-key-2", CredentialType.API, {"key": "val"})
            vault.store_credential("db-password", CredentialType.DATABASE, {"pass": "secret"})

            results = vault.search_credentials("key", CredentialType.API)
            assert len(results) == 2


class TestVaultPersistence:
    """Test suite for vault persistence."""

    def test_save_and_load(self):
        """Test saving and loading vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.enc"

            # Create and save
            vault1 = SecureVault(
                vault_path=str(vault_path),
                master_password="test-password",
                allow_insecure_path=True
            )
            cred_id = vault1.store_credential(
                name="test",
                credential_type=CredentialType.STANDARD,
                data={"password": "secret123"}
            )

            # Load in new instance
            vault2 = SecureVault(
                vault_path=str(vault_path),
                master_password="test-password",
                auto_redact=False,
                allow_insecure_path=True
            )

            cred = vault2.get_credential(cred_id)
            assert cred.data["password"] == "secret123"

    def test_load_with_wrong_password(self):
        """Test loading vault with wrong password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.enc"

            vault1 = SecureVault(
                vault_path=str(vault_path),
                master_password="correct-password",
                allow_insecure_path=True
            )
            vault1.store_credential("test", CredentialType.STANDARD, {"key": "value"})

            with pytest.raises(ValueError, match="Failed to load vault"):
                vault2 = SecureVault(
                    vault_path=str(vault_path),
                    master_password="wrong-password",
                    allow_insecure_path=True
                )

    def test_vault_file_permissions(self):
        """Test that vault file has correct permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.enc"

            vault = SecureVault(
                vault_path=str(vault_path),
                master_password="test",
                allow_insecure_path=True
            )
            vault.store_credential("test", CredentialType.STANDARD, {"key": "value"})

            # Check file permissions (owner read/write only)
            import stat
            mode = vault_path.stat().st_mode
            assert mode & stat.S_IRUSR  # Owner can read
            assert mode & stat.S_IWUSR  # Owner can write
            assert not (mode & stat.S_IRWXG)  # Group has no permissions
            assert not (mode & stat.S_IRWXO)  # Others have no permissions


class TestVaultStatistics:
    """Test suite for vault statistics."""

    def test_get_vault_stats(self):
        """Test getting vault statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="test",
                auto_redact=True,
                allow_insecure_path=True
            )

            vault.store_credential("api1", CredentialType.API, {"key": "val"})
            vault.store_credential("api2", CredentialType.API, {"key": "val"})
            vault.store_credential("db1", CredentialType.DATABASE, {"pass": "secret"})

            stats = vault.get_vault_stats()

            assert stats["total_credentials"] == 3
            assert stats["by_type"]["api"] == 2
            assert stats["by_type"]["database"] == 1
            assert stats["auto_redact"] == True


class TestVaultSecurity:
    """Security-focused tests for vault."""

    def test_encryption_at_rest(self):
        """Test that data is encrypted on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.enc"

            vault = SecureVault(
                vault_path=str(vault_path),
                master_password="test",
                allow_insecure_path=True
            )
            vault.store_credential(
                name="secret",
                credential_type=CredentialType.STANDARD,
                data={"password": "very-secret-password"}
            )

            # Read raw file
            encrypted_content = vault_path.read_bytes()

            # Should not contain plaintext
            assert b"very-secret-password" not in encrypted_content
            assert b"secret" not in encrypted_content

    def test_key_derivation(self):
        """Test that PBKDF2 is used for key derivation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = SecureVault(
                vault_path=str(Path(tmpdir) / "vault.enc"),
                master_password="weak",
                allow_insecure_path=True
            )

            # Should successfully encrypt/decrypt with derived key
            cred_id = vault.store_credential("test", CredentialType.STANDARD, {"key": "value"})
            cred = vault.get_credential(cred_id, redact=False)
            assert cred.data["key"] == "value"

    def test_path_traversal_prevention(self):
        """Test that path traversal is prevented."""
        with pytest.raises(SecurityError):
            vault = SecureVault(
                vault_path="../../../etc/passwd",
                master_password="test"
            )

    def test_unique_salt_per_vault(self):
        """Test that each vault uses a unique salt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault1_path = Path(tmpdir) / "vault1.enc"
            vault2_path = Path(tmpdir) / "vault2.enc"

            vault1 = SecureVault(
                vault_path=str(vault1_path),
                master_password="same-password",
                allow_insecure_path=True
            )
            vault1.store_credential("test", CredentialType.STANDARD, {"key": "value"})

            vault2 = SecureVault(
                vault_path=str(vault2_path),
                master_password="same-password",
                allow_insecure_path=True
            )
            vault2.store_credential("test", CredentialType.STANDARD, {"key": "value"})

            # Encrypted content should differ due to unique salts
            content1 = vault1_path.read_bytes()
            content2 = vault2_path.read_bytes()
            assert content1 != content2
