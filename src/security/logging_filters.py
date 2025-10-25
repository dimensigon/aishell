"""
Logging Filters for Credential Redaction

This module provides logging filters to automatically redact sensitive information
from log output, preventing credential leakage.

Security: CRITICAL
CVSS: 8.2 (High) - Prevents credential exposure
"""

import logging
import re
from typing import Pattern, List


class CredentialRedactionFilter(logging.Filter):
    """
    Filter to redact sensitive information from logs

    Automatically redacts:
    - Passwords in connection strings
    - API keys and tokens
    - Environment variables containing secrets
    - JWT tokens
    - Credit card numbers
    - SSH keys
    """

    # Patterns to redact
    PATTERNS: List[Pattern] = [
        # Passwords in URLs (keep username, redact password)
        re.compile(r'://([^:]+):([^@]+)@', re.IGNORECASE),

        # API keys and tokens
        re.compile(r'(api[_-]?key|token|secret|bearer)["\s:=]+([^\s"\']+)', re.IGNORECASE),

        # Environment variables
        re.compile(r'(PASSWORD|SECRET|KEY|TOKEN|PRIVATE)["\s:=]+([^\s"\']+)', re.IGNORECASE),

        # Oracle passwords
        re.compile(r'password\s*=\s*["\']?([^"\'\\s]+)', re.IGNORECASE),

        # JWT tokens
        re.compile(r'(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)'),

        # Credit card numbers (PCI DSS)
        re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),

        # SSH private keys
        re.compile(r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----', re.DOTALL),

        # AWS keys
        re.compile(r'(AKIA[0-9A-Z]{16})'),

        # Generic secrets pattern
        re.compile(r'(["\'])((?:secret|password|key|token)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE),
    ]

    REDACTION_TEXT = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Redact sensitive information from log records

        Args:
            record: LogRecord to filter

        Returns:
            True (always - this filter never suppresses records)
        """
        # Redact message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.redact(record.msg)

        # Redact arguments
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) for arg in record.args)
            elif isinstance(record.args, list):
                record.args = [self.redact(str(arg)) for arg in record.args]

        # Redact exception info if present
        if record.exc_info and record.exc_info[1]:
            exc_msg = str(record.exc_info[1])
            if exc_msg:
                # Create a sanitized exception message
                redacted_msg = self.redact(exc_msg)
                # Update the exception info
                record.exc_text = redacted_msg

        return True

    def redact(self, text: str) -> str:
        """
        Apply all redaction patterns to text

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        if not isinstance(text, str):
            return text

        redacted = text

        for pattern in self.PATTERNS:
            # Special handling for URL passwords (keep username)
            if pattern == self.PATTERNS[0]:  # URL pattern
                redacted = pattern.sub(rf'://\1:{self.REDACTION_TEXT}@', redacted)
            # Special handling for key-value pairs (keep key name)
            elif pattern == self.PATTERNS[1] or pattern == self.PATTERNS[2] or pattern == self.PATTERNS[3]:
                redacted = pattern.sub(rf'\1={self.REDACTION_TEXT}', redacted)
            # Generic redaction for everything else
            else:
                redacted = pattern.sub(self.REDACTION_TEXT, redacted)

        return redacted


class PIIRedactionFilter(logging.Filter):
    """
    Filter to redact Personally Identifiable Information (PII) from logs

    Redacts:
    - Email addresses
    - Phone numbers
    - Social Security Numbers
    - IP addresses (optional)
    """

    PII_PATTERNS: List[Pattern] = [
        # Email addresses
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),

        # US Phone numbers
        re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),

        # Social Security Numbers
        re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),

        # IP addresses (optional - enable if needed)
        # re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    ]

    REDACTION_TEXT = "***PII_REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact PII from log records"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.redact_pii(record.msg)

        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact_pii(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact_pii(str(arg)) for arg in record.args)

        return True

    def redact_pii(self, text: str) -> str:
        """Apply PII redaction patterns"""
        if not isinstance(text, str):
            return text

        redacted = text
        for pattern in self.PII_PATTERNS:
            redacted = pattern.sub(self.REDACTION_TEXT, redacted)

        return redacted


def configure_secure_logging():
    """
    Configure all loggers with credential and PII redaction filters

    Call this function during application initialization to apply
    security filters to all logging output.

    Example:
        from src.security.logging_filters import configure_secure_logging

        configure_secure_logging()
        logger = logging.getLogger(__name__)
        logger.info("Connection string: postgresql://user:password@host/db")
        # Output: "Connection string: postgresql://user:***REDACTED***@host/db"
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Create filters
    credential_filter = CredentialRedactionFilter()
    pii_filter = PIIRedactionFilter()

    # Add filters to root logger
    root_logger.addFilter(credential_filter)
    root_logger.addFilter(pii_filter)

    # Apply to all existing handlers
    for handler in root_logger.handlers:
        handler.addFilter(credential_filter)
        handler.addFilter(pii_filter)

    # Log that filtering is active (without revealing config)
    logging.info("Secure logging configured with credential and PII redaction")


# Example usage
if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Enable secure logging
    configure_secure_logging()

    # Test redaction
    logger = logging.getLogger(__name__)

    print("=== Testing Credential Redaction ===\n")

    # Test 1: Database connection string
    logger.info("Connecting to: postgresql://postgres:MySecretPassword123@localhost:5432/db")

    # Test 2: API key
    logger.info("Using API key: api_key=sk-1234567890abcdef")

    # Test 3: JWT token
    logger.info("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature")

    # Test 4: Oracle connection
    logger.info("Oracle connection: password=MyOraclePass123 user=SYS")

    # Test 5: Environment variable
    logger.info("DATABASE_PASSWORD=VerySecretPassword123")

    # Test 6: Email (PII)
    logger.info("User email: user@example.com")

    # Test 7: Phone number (PII)
    logger.info("Contact: 555-123-4567")

    print("\n=== All tests completed ===")
    print("Check that all sensitive data was redacted above")
