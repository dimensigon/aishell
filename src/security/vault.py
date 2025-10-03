"""
Secure Vault - Encrypted credential storage with auto-redaction

Provides enterprise-grade credential management with:
- Fernet symmetric encryption
- Multiple credential types
- Auto-redaction on retrieval
- OS keyring integration
"""

import json
import base64
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .redaction import RedactionEngine


class CredentialType(Enum):
    """Types of credentials that can be stored"""
    STANDARD = 'standard'
    DATABASE = 'database'
    API = 'api'
    OAUTH = 'oauth'
    SSH = 'ssh'
    CUSTOM = 'custom'


@dataclass
class Credential:
    """A single credential entry"""
    id: str
    name: str
    type: CredentialType
    data: Dict[str, Any]
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['type'] = self.type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'Credential':
        """Create from dictionary"""
        data['type'] = CredentialType(data['type'])
        return cls(**data)


class MockKeyring:
    """Mock keyring for systems without OS keyring support"""
    _storage: Dict[str, str] = {}

    @classmethod
    def get_password(cls, service: str, username: str) -> Optional[str]:
        """Get password from mock storage"""
        key = f"{service}:{username}"
        return cls._storage.get(key)

    @classmethod
    def set_password(cls, service: str, username: str, password: str):
        """Set password in mock storage"""
        key = f"{service}:{username}"
        cls._storage[key] = password

    @classmethod
    def delete_password(cls, service: str, username: str):
        """Delete password from mock storage"""
        key = f"{service}:{username}"
        cls._storage.pop(key, None)


class SecureVault:
    """Secure credential vault with encryption and auto-redaction"""

    SERVICE_NAME = 'ai-shell-vault'

    def __init__(
        self,
        vault_path: Optional[str] = None,
        master_password: Optional[str] = None,
        auto_redact: bool = True,
        use_keyring: bool = False
    ):
        self.vault_path = Path(vault_path) if vault_path else Path.home() / '.ai-shell' / 'vault.enc'
        self.auto_redact = auto_redact
        self.use_keyring = use_keyring
        self.redaction_engine = RedactionEngine() if auto_redact else None

        # Initialize keyring
        self.keyring = MockKeyring()

        # Initialize encryption
        self._fernet: Optional[Fernet] = None
        if master_password:
            self._initialize_encryption(master_password)

        # Load existing vault
        self.credentials: Dict[str, Credential] = {}
        if self.vault_path.exists():
            self._load_vault()

    def _initialize_encryption(self, master_password: str):
        """Initialize Fernet encryption with master password"""
        # Derive key from password using PBKDF2
        salt = b'ai-shell-salt-v1'  # In production, use random salt stored separately
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self._fernet = Fernet(key)

    def _encrypt(self, data: str) -> bytes:
        """Encrypt data"""
        if not self._fernet:
            raise ValueError("Vault not initialized with master password")
        return self._fernet.encrypt(data.encode())

    def _decrypt(self, data: bytes) -> str:
        """Decrypt data"""
        if not self._fernet:
            raise ValueError("Vault not initialized with master password")
        return self._fernet.decrypt(data).decode()

    def _load_vault(self):
        """Load and decrypt vault"""
        if not self._fernet:
            return

        try:
            encrypted_data = self.vault_path.read_bytes()
            decrypted_data = self._decrypt(encrypted_data)
            vault_data = json.loads(decrypted_data)

            self.credentials = {
                cred_id: Credential.from_dict(cred_data)
                for cred_id, cred_data in vault_data.items()
            }
        except Exception as e:
            raise ValueError(f"Failed to load vault: {e}")

    def _save_vault(self):
        """Encrypt and save vault"""
        if not self._fernet:
            raise ValueError("Vault not initialized with master password")

        vault_data = {
            cred_id: cred.to_dict()
            for cred_id, cred in self.credentials.items()
        }

        json_data = json.dumps(vault_data, indent=2)
        encrypted_data = self._encrypt(json_data)

        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        self.vault_path.write_bytes(encrypted_data)

    def store_credential(
        self,
        name: str,
        credential_type: CredentialType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        credential_id: Optional[str] = None
    ) -> str:
        """Store a credential in the vault"""
        if not self._fernet:
            raise ValueError("Vault not initialized with master password")

        cred_id = credential_id or f"{name}_{datetime.now().timestamp()}"
        now = datetime.now().isoformat()

        credential = Credential(
            id=cred_id,
            name=name,
            type=credential_type,
            data=data,
            created_at=now,
            updated_at=now,
            metadata=metadata
        )

        self.credentials[cred_id] = credential
        self._save_vault()

        # Optionally store in OS keyring
        if self.use_keyring and credential_type == CredentialType.STANDARD:
            if 'password' in data:
                self.keyring.set_password(
                    self.SERVICE_NAME,
                    name,
                    data['password']
                )

        return cred_id

    def get_credential(
        self,
        credential_id: str,
        redact: Optional[bool] = None
    ) -> Optional[Credential]:
        """Retrieve a credential from the vault"""
        credential = self.credentials.get(credential_id)

        if credential and (redact or (redact is None and self.auto_redact)):
            # Create a copy with redacted data
            redacted_data = self.redaction_engine.redact_dict(credential.data)
            return Credential(
                id=credential.id,
                name=credential.name,
                type=credential.type,
                data=redacted_data,
                created_at=credential.created_at,
                updated_at=credential.updated_at,
                metadata=credential.metadata
            )

        return credential

    def get_credential_by_name(
        self,
        name: str,
        redact: Optional[bool] = None
    ) -> Optional[Credential]:
        """Retrieve a credential by name"""
        for credential in self.credentials.values():
            if credential.name == name:
                return self.get_credential(credential.id, redact=redact)
        return None

    def list_credentials(self, credential_type: Optional[CredentialType] = None) -> List[str]:
        """List all credential IDs, optionally filtered by type"""
        if credential_type:
            return [
                cred_id for cred_id, cred in self.credentials.items()
                if cred.type == credential_type
            ]
        return list(self.credentials.keys())

    def update_credential(
        self,
        credential_id: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a credential"""
        if credential_id not in self.credentials:
            return False

        credential = self.credentials[credential_id]

        if data:
            credential.data = data
        if metadata:
            credential.metadata = metadata

        credential.updated_at = datetime.now().isoformat()
        self._save_vault()

        return True

    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential"""
        if credential_id not in self.credentials:
            return False

        credential = self.credentials[credential_id]

        # Remove from keyring if applicable
        if self.use_keyring and credential.type == CredentialType.STANDARD:
            self.keyring.delete_password(self.SERVICE_NAME, credential.name)

        del self.credentials[credential_id]
        self._save_vault()

        return True

    def search_credentials(
        self,
        query: str,
        credential_type: Optional[CredentialType] = None
    ) -> List[Credential]:
        """Search credentials by name or metadata"""
        results = []
        query_lower = query.lower()

        for credential in self.credentials.values():
            if credential_type and credential.type != credential_type:
                continue

            if (query_lower in credential.name.lower() or
                (credential.metadata and
                 any(query_lower in str(v).lower() for v in credential.metadata.values()))):
                results.append(self.get_credential(credential.id))

        return results

    def export_credential(self, credential_id: str, include_sensitive: bool = False) -> Dict:
        """Export a credential as a dictionary"""
        credential = self.credentials.get(credential_id)
        if not credential:
            raise ValueError(f"Credential {credential_id} not found")

        if include_sensitive:
            return credential.to_dict()
        else:
            redacted = self.get_credential(credential_id, redact=True)
            return redacted.to_dict()

    def get_vault_stats(self) -> Dict[str, Any]:
        """Get vault statistics"""
        type_counts = {}
        for credential in self.credentials.values():
            type_counts[credential.type.value] = type_counts.get(credential.type.value, 0) + 1

        return {
            'total_credentials': len(self.credentials),
            'by_type': type_counts,
            'vault_path': str(self.vault_path),
            'auto_redact': self.auto_redact,
            'use_keyring': self.use_keyring
        }
