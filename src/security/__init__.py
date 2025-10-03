"""
Security Module - Secure credential storage and auto-redaction

This module provides enterprise-grade security features including:
- Encrypted credential vault with Fernet encryption
- Multiple credential types (standard, database, custom)
- Auto-redaction of sensitive data
- OS keyring integration
"""

from .vault import SecureVault, CredentialType
from .redaction import RedactionEngine, RedactionPattern

__all__ = [
    'SecureVault',
    'CredentialType',
    'RedactionEngine',
    'RedactionPattern',
]

__version__ = '1.0.0'
