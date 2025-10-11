"""
Comprehensive tests for Security & Vault System

Tests cover:
- Encryption/decryption
- Credential types (standard, database, API, custom)
- Auto-redaction patterns
- Vault operations (CRUD)
- Keyring integration
- Pattern detection
- Search functionality
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.security import SecureVault, CredentialType, RedactionEngine, RedactionPattern


class TestRedactionEngine:
    """Test auto-redaction functionality"""

    def test_password_redaction(self):
        """Test password pattern redaction"""
        engine = RedactionEngine()
        text = "password: secret123"
        redacted = engine.redact(text)
        assert "secret123" not in redacted
        assert "[REDACTED_PASSWORD]" in redacted

    def test_api_key_redaction(self):
        """Test API key pattern redaction"""
        engine = RedactionEngine()
        text = "api_key=sk_test_1234567890abcdef"
        redacted = engine.redact(text)
        assert "sk_test_1234567890abcdef" not in redacted
        assert "[REDACTED_API_KEY]" in redacted

    def test_token_redaction(self):
        """Test token pattern redaction"""
        engine = RedactionEngine()
        text = "Bearer token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = engine.redact(text)
        # Either TOKEN or JWT pattern should redact it
        assert "[REDACTED" in redacted

    def test_database_url_redaction(self):
        """Test database URL pattern redaction"""
        engine = RedactionEngine()
        text = "mongodb://user:pass@localhost:27017/db"
        redacted = engine.redact(text)
        assert "user:pass" not in redacted
        assert "[REDACTED_DATABASE_URL]" in redacted

    def test_multiple_patterns(self):
        """Test multiple patterns in same text"""
        engine = RedactionEngine()
        text = "password: secret123, api_key: abc123, token: xyz789"
        redacted = engine.redact(text)
        assert "secret123" not in redacted
        assert "abc123" not in redacted
        assert "xyz789" not in redacted

    def test_custom_pattern(self):
        """Test adding custom redaction pattern"""
        engine = RedactionEngine()
        engine.add_pattern(
            name='CUSTOM_ID',
            pattern=r'ID-\d{6}',
            replacement='[CUSTOM_ID]'
        )
        text = "User ID-123456 logged in"
        redacted = engine.redact(text)
        assert "ID-123456" not in redacted
        assert "[CUSTOM_ID]" in redacted

    def test_pattern_detection(self):
        """Test detecting which patterns match"""
        engine = RedactionEngine()
        text = "password: secret, api_key: key123"
        detections = engine.detect_patterns(text)
        assert 'PASSWORD' in detections
        assert 'API_KEY' in detections

    def test_is_sensitive(self):
        """Test checking if text contains sensitive data"""
        engine = RedactionEngine()
        assert engine.is_sensitive("password: secret")
        assert not engine.is_sensitive("hello world")

    def test_dict_redaction(self):
        """Test redacting dictionary values"""
        engine = RedactionEngine()
        data = {
            'username': 'user123',
            'password': 'secret',
            'api_key': 'key123',
            'public_info': 'visible'
        }
        redacted = engine.redact_dict(data)
        assert redacted['password'] == '[REDACTED]'
        assert redacted['api_key'] == '[REDACTED]'
        assert redacted['username'] == 'user123'
        assert redacted['public_info'] == 'visible'

    def test_preserve_length_redaction(self):
        """Test length-preserving redaction"""
        engine = RedactionEngine()
        engine.add_pattern(
            name='PRESERVE_TEST',
            pattern=r'SECRET_\w+',
            preserve_length=True,
            preserve_prefix=7,
            preserve_suffix=2
        )
        text = "SECRET_12345678AB"
        redacted = engine.redact(text)
        assert redacted.startswith("SECRET_")
        assert redacted.endswith("AB")
        assert '*' in redacted


class TestSecureVault:
    """Test secure vault functionality"""

    @pytest.fixture
    def temp_vault(self, vault_factory):
        """Create temporary vault"""
        return vault_factory()

    def test_vault_initialization(self, temp_vault):
        """Test vault initialization"""
        assert temp_vault._fernet is not None
        assert temp_vault.auto_redact is True
        assert temp_vault.redaction_engine is not None

    def test_store_standard_credential(self, temp_vault):
        """Test storing standard credential"""
        cred_id = temp_vault.store_credential(
            name='test_user',
            credential_type=CredentialType.STANDARD,
            data={'username': 'user123', 'password': 'secret123'}
        )
        assert cred_id in temp_vault.credentials
        assert temp_vault.credentials[cred_id].type == CredentialType.STANDARD

    def test_store_database_credential(self, temp_vault):
        """Test storing database credential"""
        cred_id = temp_vault.store_credential(
            name='production_db',
            credential_type=CredentialType.DATABASE,
            data={
                'host': 'db.example.com',
                'port': 5432,
                'username': 'dbuser',
                'password': 'dbpass123',
                'database': 'production'
            }
        )
        cred = temp_vault.credentials[cred_id]
        assert cred.type == CredentialType.DATABASE
        assert cred.data['host'] == 'db.example.com'

    def test_store_api_credential(self, temp_vault):
        """Test storing API credential"""
        cred_id = temp_vault.store_credential(
            name='openai_api',
            credential_type=CredentialType.API,
            data={
                'api_key': 'sk-1234567890abcdef',
                'endpoint': 'https://api.openai.com'
            }
        )
        assert temp_vault.credentials[cred_id].type == CredentialType.API

    def test_auto_redaction_on_retrieval(self, temp_vault):
        """Test auto-redaction when retrieving credentials"""
        cred_id = temp_vault.store_credential(
            name='secret_cred',
            credential_type=CredentialType.STANDARD,
            data={'password': 'secret123', 'token': 'token456'}
        )

        # Retrieve with auto-redaction (default)
        redacted_cred = temp_vault.get_credential(cred_id)
        assert redacted_cred.data['password'] == '[REDACTED]'
        assert redacted_cred.data['token'] == '[REDACTED]'

        # Retrieve without redaction
        unredacted_cred = temp_vault.get_credential(cred_id, redact=False)
        assert unredacted_cred.data['password'] == 'secret123'
        assert unredacted_cred.data['token'] == 'token456'

    def test_encryption_decryption(self, temp_vault):
        """Test encryption and decryption"""
        test_data = "sensitive data 123"
        encrypted = temp_vault._encrypt(test_data)
        assert encrypted != test_data.encode()

        decrypted = temp_vault._decrypt(encrypted)
        assert decrypted == test_data

    def test_vault_persistence(self, vault_factory):
        """Test vault data persistence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / 'persist_vault.enc'

            # Create and populate vault
            vault1 = vault_factory(
                vault_path=str(vault_path),
                master_password='test123',
                auto_redact=False
            )
            cred_id = vault1.store_credential(
                name='persist_test',
                credential_type=CredentialType.STANDARD,
                data={'username': 'user', 'password': 'pass'}
            )

            # Load vault in new instance
            vault2 = vault_factory(
                vault_path=str(vault_path),
                master_password='test123',
                auto_redact=False
            )

            loaded_cred = vault2.get_credential(cred_id, redact=False)
            assert loaded_cred is not None
            assert loaded_cred.data['username'] == 'user'
            assert loaded_cred.data['password'] == 'pass'

    def test_get_credential_by_name(self, temp_vault):
        """Test retrieving credential by name"""
        temp_vault.store_credential(
            name='named_cred',
            credential_type=CredentialType.STANDARD,
            data={'key': 'value'}
        )

        cred = temp_vault.get_credential_by_name('named_cred', redact=False)
        assert cred is not None
        assert cred.name == 'named_cred'

    def test_list_credentials(self, temp_vault):
        """Test listing credentials"""
        temp_vault.store_credential(
            name='cred1',
            credential_type=CredentialType.STANDARD,
            data={'key': 'value'}
        )
        temp_vault.store_credential(
            name='cred2',
            credential_type=CredentialType.DATABASE,
            data={'host': 'localhost'}
        )

        all_creds = temp_vault.list_credentials()
        assert len(all_creds) == 2

        db_creds = temp_vault.list_credentials(CredentialType.DATABASE)
        assert len(db_creds) == 1

    def test_update_credential(self, temp_vault):
        """Test updating credential"""
        cred_id = temp_vault.store_credential(
            name='update_test',
            credential_type=CredentialType.STANDARD,
            data={'value': 'old'}
        )

        success = temp_vault.update_credential(
            cred_id,
            data={'value': 'new'}
        )
        assert success

        updated_cred = temp_vault.get_credential(cred_id, redact=False)
        assert updated_cred.data['value'] == 'new'

    def test_delete_credential(self, temp_vault):
        """Test deleting credential"""
        cred_id = temp_vault.store_credential(
            name='delete_test',
            credential_type=CredentialType.STANDARD,
            data={'key': 'value'}
        )

        success = temp_vault.delete_credential(cred_id)
        assert success
        assert cred_id not in temp_vault.credentials

    def test_search_credentials(self, temp_vault):
        """Test searching credentials"""
        temp_vault.store_credential(
            name='production_db',
            credential_type=CredentialType.DATABASE,
            data={'host': 'prod.example.com'},
            metadata={'env': 'production'}
        )
        temp_vault.store_credential(
            name='staging_db',
            credential_type=CredentialType.DATABASE,
            data={'host': 'staging.example.com'},
            metadata={'env': 'staging'}
        )

        results = temp_vault.search_credentials('production')
        assert len(results) >= 1
        assert any(r.name == 'production_db' for r in results)

    def test_vault_stats(self, temp_vault):
        """Test vault statistics"""
        temp_vault.store_credential(
            name='cred1',
            credential_type=CredentialType.STANDARD,
            data={'key': 'value'}
        )
        temp_vault.store_credential(
            name='cred2',
            credential_type=CredentialType.DATABASE,
            data={'host': 'localhost'}
        )

        stats = temp_vault.get_vault_stats()
        assert stats['total_credentials'] == 2
        assert 'standard' in stats['by_type']
        assert 'database' in stats['by_type']

    def test_export_credential(self, temp_vault):
        """Test exporting credential"""
        cred_id = temp_vault.store_credential(
            name='export_test',
            credential_type=CredentialType.API,
            data={'api_key': 'secret123'}
        )

        # Export with redaction
        export_redacted = temp_vault.export_credential(cred_id, include_sensitive=False)
        assert export_redacted['data']['api_key'] == '[REDACTED]'

        # Export without redaction
        export_full = temp_vault.export_credential(cred_id, include_sensitive=True)
        assert export_full['data']['api_key'] == 'secret123'

    def test_keyring_integration(self, temp_vault):
        """Test keyring integration with mock"""
        temp_vault.use_keyring = True

        cred_id = temp_vault.store_credential(
            name='keyring_test',
            credential_type=CredentialType.STANDARD,
            data={'username': 'user', 'password': 'pass123'}
        )

        # Check mock keyring
        stored_password = temp_vault.keyring.get_password(
            temp_vault.SERVICE_NAME,
            'keyring_test'
        )
        assert stored_password == 'pass123'


class TestCredentialTypes:
    """Test different credential types"""

    def test_oauth_credential(self, vault_factory):
        """Test OAuth credential type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = vault_factory(
                vault_path=str(Path(tmpdir) / 'oauth_vault.enc'),
                master_password='test123'
            )

            cred_id = vault.store_credential(
                name='google_oauth',
                credential_type=CredentialType.OAUTH,
                data={
                    'client_id': 'client123',
                    'client_secret': 'secret456',
                    'access_token': 'token789',
                    'refresh_token': 'refresh012'
                }
            )

            cred = vault.get_credential(cred_id, redact=False)
            assert cred.type == CredentialType.OAUTH
            assert 'client_id' in cred.data

    def test_ssh_credential(self, vault_factory):
        """Test SSH credential type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = vault_factory(
                vault_path=str(Path(tmpdir) / 'ssh_vault.enc'),
                master_password='test123'
            )

            cred_id = vault.store_credential(
                name='server_ssh',
                credential_type=CredentialType.SSH,
                data={
                    'host': 'server.example.com',
                    'username': 'admin',
                    'private_key': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'
                }
            )

            cred = vault.get_credential(cred_id, redact=False)
            assert cred.type == CredentialType.SSH

    def test_custom_credential(self, vault_factory):
        """Test custom credential type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = vault_factory(
                vault_path=str(Path(tmpdir) / 'custom_vault.enc'),
                master_password='test123'
            )

            cred_id = vault.store_credential(
                name='custom_service',
                credential_type=CredentialType.CUSTOM,
                data={
                    'custom_field_1': 'value1',
                    'custom_field_2': 'value2'
                },
                metadata={
                    'service': 'custom_api',
                    'version': '2.0'
                }
            )

            cred = vault.get_credential(cred_id, redact=False)
            assert cred.type == CredentialType.CUSTOM
            assert cred.metadata['service'] == 'custom_api'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
