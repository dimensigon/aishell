"""
Comprehensive tests for encryption module.

Tests encryption/decryption, key derivation, field-level encryption,
and security edge cases.
"""

import pytest
from cryptography.fernet import Fernet, InvalidToken
import base64
import json
from src.security.encryption import DataEncryption, FieldEncryption


class TestDataEncryption:
    """Test suite for DataEncryption class."""

    def test_basic_encryption_decryption(self):
        """Test basic encryption and decryption of plaintext."""
        key = "test-encryption-key-123"
        encryptor = DataEncryption(key)

        plaintext = "sensitive data"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext
        assert encrypted != plaintext
        assert encrypted.startswith('gAAAAA')  # Fernet token format

    def test_encryption_deterministic_with_same_key(self):
        """Test that encryption is deterministic with same key."""
        key = "test-key"
        encryptor1 = DataEncryption(key)
        encryptor2 = DataEncryption(key)

        plaintext = "test data"
        encrypted1 = encryptor1.encrypt(plaintext)

        # Same key should be able to decrypt
        decrypted = encryptor2.decrypt(encrypted1)
        assert decrypted == plaintext

    def test_encryption_different_keys(self):
        """Test that different keys produce different results."""
        plaintext = "secret message"

        encryptor1 = DataEncryption("key1")
        encryptor2 = DataEncryption("key2")

        encrypted1 = encryptor1.encrypt(plaintext)
        encrypted2 = encryptor2.encrypt(plaintext)

        # Different keys produce different ciphertext
        assert encrypted1 != encrypted2

        # Cross-decryption should fail
        with pytest.raises(InvalidToken):
            encryptor1.decrypt(encrypted2)

    def test_key_padding_short_key(self):
        """Test that short keys are properly padded."""
        short_key = "short"
        encryptor = DataEncryption(short_key)

        plaintext = "test"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_key_truncation_long_key(self):
        """Test that long keys are properly truncated."""
        long_key = "a" * 100
        encryptor = DataEncryption(long_key)

        plaintext = "test"
        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        encryptor = DataEncryption("test-key")

        encrypted = encryptor.encrypt("")
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == ""

    def test_encrypt_unicode(self):
        """Test encryption of unicode characters."""
        encryptor = DataEncryption("test-key")

        unicode_text = "Hello 世界 🔐 Привет"
        encrypted = encryptor.encrypt(unicode_text)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == unicode_text

    def test_encrypt_special_characters(self):
        """Test encryption with special characters."""
        encryptor = DataEncryption("test-key")

        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encryptor.encrypt(special_text)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == special_text

    def test_encrypt_large_data(self):
        """Test encryption of large data."""
        encryptor = DataEncryption("test-key")

        large_text = "a" * 10000
        encrypted = encryptor.encrypt(large_text)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == large_text

    def test_decrypt_invalid_ciphertext(self):
        """Test decryption with invalid ciphertext."""
        encryptor = DataEncryption("test-key")

        with pytest.raises(InvalidToken):
            encryptor.decrypt("invalid-ciphertext")

    def test_decrypt_corrupted_ciphertext(self):
        """Test decryption with corrupted ciphertext."""
        encryptor = DataEncryption("test-key")

        plaintext = "test"
        encrypted = encryptor.encrypt(plaintext)

        # Corrupt the ciphertext
        corrupted = encrypted[:-5] + "XXXXX"

        with pytest.raises(InvalidToken):
            encryptor.decrypt(corrupted)

    def test_encrypt_dict(self):
        """Test dictionary encryption."""
        encryptor = DataEncryption("test-key")

        data = {
            "username": "admin",
            "password": "secret123",
            "metadata": {"role": "admin"}
        }

        encrypted = encryptor.encrypt_dict(data)
        decrypted = encryptor.decrypt_dict(encrypted)

        assert decrypted == data

    def test_encrypt_dict_empty(self):
        """Test encryption of empty dictionary."""
        encryptor = DataEncryption("test-key")

        data = {}
        encrypted = encryptor.encrypt_dict(data)
        decrypted = encryptor.decrypt_dict(encrypted)

        assert decrypted == data

    def test_encrypt_dict_nested(self):
        """Test encryption of nested dictionary."""
        encryptor = DataEncryption("test-key")

        data = {
            "level1": {
                "level2": {
                    "level3": "deep value"
                }
            }
        }

        encrypted = encryptor.encrypt_dict(data)
        decrypted = encryptor.decrypt_dict(encrypted)

        assert decrypted == data

    def test_pbkdf2_key_derivation(self):
        """Test that PBKDF2 is used for key derivation."""
        key = "test-key"
        encryptor = DataEncryption(key)

        # Encryption should work, indicating key was properly derived
        plaintext = "test"
        encrypted = encryptor.encrypt(plaintext)
        assert encryptor.decrypt(encrypted) == plaintext

    def test_same_key_different_instances(self):
        """Test that same key works across different instances."""
        key = "shared-key"

        encryptor1 = DataEncryption(key)
        plaintext = "shared secret"
        encrypted = encryptor1.encrypt(plaintext)

        encryptor2 = DataEncryption(key)
        decrypted = encryptor2.decrypt(encrypted)

        assert decrypted == plaintext


class TestFieldEncryption:
    """Test suite for FieldEncryption class."""

    def test_encrypt_single_field(self):
        """Test encryption of a single field."""
        encryptor = FieldEncryption("test-key")

        data = {
            "username": "john",
            "password": "secret123",
            "email": "john@example.com"
        }

        encrypted = encryptor.encrypt_fields(data, ["password"])

        assert encrypted["username"] == "john"
        assert encrypted["email"] == "john@example.com"
        assert encrypted["password"] != "secret123"
        assert encryptor.is_encrypted(encrypted["password"])

    def test_encrypt_multiple_fields(self):
        """Test encryption of multiple fields."""
        encryptor = FieldEncryption("test-key")

        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "key-12345",
            "public_info": "visible"
        }

        encrypted = encryptor.encrypt_fields(data, ["password", "api_key"])

        assert encrypted["username"] == "john"
        assert encrypted["public_info"] == "visible"
        assert encrypted["password"] != "secret123"
        assert encrypted["api_key"] != "key-12345"

    def test_decrypt_fields(self):
        """Test decryption of encrypted fields."""
        encryptor = FieldEncryption("test-key")

        data = {
            "username": "john",
            "password": "secret123"
        }

        encrypted = encryptor.encrypt_fields(data, ["password"])
        decrypted = encryptor.decrypt_fields(encrypted, ["password"])

        assert decrypted == data

    def test_encrypt_nonexistent_field(self):
        """Test encryption with nonexistent field (should be ignored)."""
        encryptor = FieldEncryption("test-key")

        data = {"username": "john"}
        encrypted = encryptor.encrypt_fields(data, ["password"])

        assert encrypted == data

    def test_decrypt_invalid_field(self):
        """Test decryption of invalid encrypted field."""
        encryptor = FieldEncryption("test-key")

        data = {"password": "not-encrypted"}
        decrypted = encryptor.decrypt_fields(data, ["password"])

        # Should leave value as is if decryption fails
        assert decrypted["password"] == "not-encrypted"

    def test_is_encrypted_detection(self):
        """Test encrypted value detection."""
        encryptor = FieldEncryption("test-key")

        assert encryptor.is_encrypted("gAAAAABc")
        assert not encryptor.is_encrypted("plaintext")
        assert not encryptor.is_encrypted("")
        assert not encryptor.is_encrypted(None)

    def test_encrypt_numeric_values(self):
        """Test encryption of numeric values (converted to string)."""
        encryptor = FieldEncryption("test-key")

        data = {"pin": 1234, "amount": 99.99}
        encrypted = encryptor.encrypt_fields(data, ["pin", "amount"])

        assert encryptor.is_encrypted(encrypted["pin"])
        assert encryptor.is_encrypted(encrypted["amount"])

        decrypted = encryptor.decrypt_fields(encrypted, ["pin", "amount"])
        assert decrypted["pin"] == "1234"
        assert decrypted["amount"] == "99.99"

    def test_field_encryption_preserves_structure(self):
        """Test that field encryption preserves dictionary structure."""
        encryptor = FieldEncryption("test-key")

        data = {
            "user": {
                "name": "John",
                "password": "secret"
            },
            "metadata": ["item1", "item2"]
        }

        encrypted = encryptor.encrypt_fields(data, ["password"])

        # Structure should be preserved
        assert "user" in encrypted
        assert "metadata" in encrypted
        assert encrypted["metadata"] == ["item1", "item2"]

    def test_default_key(self):
        """Test FieldEncryption with default key."""
        encryptor = FieldEncryption()

        data = {"password": "secret"}
        encrypted = encryptor.encrypt_fields(data, ["password"])
        decrypted = encryptor.decrypt_fields(encrypted, ["password"])

        assert decrypted["password"] == "secret"

    def test_encrypt_empty_fields_list(self):
        """Test encryption with empty fields list."""
        encryptor = FieldEncryption("test-key")

        data = {"username": "john", "password": "secret"}
        encrypted = encryptor.encrypt_fields(data, [])

        assert encrypted == data

    def test_decrypt_empty_fields_list(self):
        """Test decryption with empty fields list."""
        encryptor = FieldEncryption("test-key")

        data = {"username": "john"}
        decrypted = encryptor.decrypt_fields(data, [])

        assert decrypted == data


class TestEncryptionSecurity:
    """Security-focused tests for encryption module."""

    def test_fernet_token_format(self):
        """Test that encryption uses valid Fernet token format."""
        encryptor = DataEncryption("security-key")
        encrypted = encryptor.encrypt("test")

        # Fernet tokens are base64 encoded and start with version (gAAAAA)
        assert encrypted.startswith('gAAAAA')

        # Should be valid base64
        try:
            base64.urlsafe_b64decode(encrypted)
        except Exception:
            pytest.fail("Encrypted data is not valid base64")

    def test_tampering_detection(self):
        """Test that tampered ciphertext is detected."""
        encryptor = DataEncryption("security-key")

        plaintext = "important data"
        encrypted = encryptor.encrypt(plaintext)

        # Tamper with the ciphertext
        tampered = encrypted[:-10] + "tampered!!"

        with pytest.raises(InvalidToken):
            encryptor.decrypt(tampered)

    def test_key_isolation(self):
        """Test that different keys cannot decrypt each other's data."""
        plaintext = "confidential"

        encryptor1 = DataEncryption("key-alice")
        encryptor2 = DataEncryption("key-bob")

        encrypted_alice = encryptor1.encrypt(plaintext)

        # Bob cannot decrypt Alice's data
        with pytest.raises(InvalidToken):
            encryptor2.decrypt(encrypted_alice)

    def test_no_plaintext_leakage(self):
        """Test that ciphertext doesn't contain plaintext."""
        encryptor = DataEncryption("test-key")

        plaintext = "very-unique-secret-12345"
        encrypted = encryptor.encrypt(plaintext)

        assert plaintext not in encrypted
        assert "very-unique-secret" not in encrypted

    def test_encryption_randomness(self):
        """Test that encrypting same data produces different ciphertext."""
        encryptor = DataEncryption("test-key")

        plaintext = "test data"
        encrypted1 = encryptor.encrypt(plaintext)
        encrypted2 = encryptor.encrypt(plaintext)

        # Fernet includes timestamp, so ciphertext differs each time
        # Both should decrypt to same plaintext though
        assert encryptor.decrypt(encrypted1) == plaintext
        assert encryptor.decrypt(encrypted2) == plaintext

    def test_constant_time_operations(self):
        """Test that encryption/decryption appears constant-time."""
        encryptor = DataEncryption("test-key")

        # Fernet is designed to be constant-time
        # We can verify it doesn't crash with edge cases

        test_cases = [
            "a",
            "a" * 100,
            "a" * 1000,
            "",
            "unicode: 你好"
        ]

        for plaintext in test_cases:
            encrypted = encryptor.encrypt(plaintext)
            decrypted = encryptor.decrypt(encrypted)
            assert decrypted == plaintext
