"""
Security Module - Comprehensive Security Utilities

This module provides enterprise-grade security features including:
- Encrypted credential vault with Fernet encryption
- Multiple credential types (standard, database, custom)
- Auto-redaction of sensitive data
- OS keyring integration
- Path traversal protection
- Command sanitization
- Rate limiting
- Secure temporary file handling
- Production error handling
"""

from .vault import SecureVault, CredentialType, Credential
from .redaction import RedactionEngine, RedactionPattern

# Import new security modules with error handling
try:
    from .path_validator import safe_path_join, validate_vault_path, validate_config_path, SecurityError
    PATH_SECURITY_AVAILABLE = True
except ImportError:
    PATH_SECURITY_AVAILABLE = False

try:
    from .command_sanitizer import CommandSanitizer
    COMMAND_SANITIZER_AVAILABLE = True
except ImportError:
    COMMAND_SANITIZER_AVAILABLE = False

try:
    from .rate_limiter import RateLimiter, RateLimitConfig, RateLimitExceeded, rate_limited
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

try:
    from .temp_file_handler import SecureTempFile
    TEMP_FILE_HANDLER_AVAILABLE = True
except ImportError:
    TEMP_FILE_HANDLER_AVAILABLE = False

try:
    from .error_handler import SecureErrorHandler, secure_exception_handler, suppress_stack_trace_in_production
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False

__all__ = [
    # Core vault & credentials
    'SecureVault',
    'CredentialType',
    'Credential',
    # Redaction
    'RedactionEngine',
    'RedactionPattern',
]

# Add optional exports if available
if PATH_SECURITY_AVAILABLE:
    __all__.extend([
        'safe_path_join',
        'validate_vault_path',
        'validate_config_path',
        'SecurityError',
    ])

if COMMAND_SANITIZER_AVAILABLE:
    __all__.append('CommandSanitizer')

if RATE_LIMITER_AVAILABLE:
    __all__.extend([
        'RateLimiter',
        'RateLimitConfig',
        'RateLimitExceeded',
        'rate_limited',
    ])

if TEMP_FILE_HANDLER_AVAILABLE:
    __all__.append('SecureTempFile')

if ERROR_HANDLER_AVAILABLE:
    __all__.extend([
        'SecureErrorHandler',
        'secure_exception_handler',
        'suppress_stack_trace_in_production',
    ])

__version__ = '2.0.0'  # Updated for Phase 1B security fixes
