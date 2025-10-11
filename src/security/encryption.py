"""
Data encryption utilities for enterprise security.

Provides encryption at rest and field-level encryption.
"""

from typing import Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json


class DataEncryption:
    """Handles data encryption and decryption."""

    def __init__(self, key: str):
        """Initialize encryption with a key.

        Args:
            key: Encryption key (must be 32 bytes for Fernet)
        """
        # Ensure key is 32 bytes
        if len(key.encode()) < 32:
            key = key.ljust(32, '!')
        elif len(key.encode()) > 32:
            key = key[:32]

        # Derive a proper Fernet key from the provided key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'aishell_salt',  # In production, use unique salt per tenant
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        self._cipher = Fernet(derived_key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext data.

        Args:
            plaintext: Data to encrypt

        Returns:
            Encrypted data as string
        """
        encrypted_bytes = self._cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext data.

        Args:
            ciphertext: Encrypted data

        Returns:
            Decrypted plaintext
        """
        decrypted_bytes = self._cipher.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary to JSON string.

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted JSON string
        """
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, ciphertext: str) -> Dict[str, Any]:
        """Decrypt JSON string to dictionary.

        Args:
            ciphertext: Encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)


class FieldEncryption:
    """Handles field-level encryption for sensitive data."""

    def __init__(self, key: str = "default-field-encryption-key"):
        """Initialize field encryption.

        Args:
            key: Encryption key
        """
        self._encryptor = DataEncryption(key)

    def encrypt_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing data
            fields: List of field names to encrypt

        Returns:
            Dictionary with specified fields encrypted
        """
        result = data.copy()

        for field in fields:
            if field in result:
                # Encrypt the field value
                value = str(result[field])
                encrypted_value = self._encryptor.encrypt(value)
                result[field] = encrypted_value

        return result

    def decrypt_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary with encrypted fields
            fields: List of field names to decrypt

        Returns:
            Dictionary with specified fields decrypted
        """
        result = data.copy()

        for field in fields:
            if field in result:
                # Decrypt the field value
                encrypted_value = result[field]
                try:
                    decrypted_value = self._encryptor.decrypt(encrypted_value)
                    result[field] = decrypted_value
                except Exception:
                    # If decryption fails, leave value as is
                    pass

        return result

    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted.

        Args:
            value: Value to check

        Returns:
            True if value appears encrypted
        """
        try:
            # Fernet tokens start with 'gAAAAA'
            return value.startswith('gAAAAA')
        except (AttributeError, TypeError):
            return False
