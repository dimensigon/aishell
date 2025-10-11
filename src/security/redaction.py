"""
Auto-redaction engine for sensitive data protection

Provides pattern-based redaction of credentials, API keys, tokens,
and other sensitive information in logs and outputs.
"""

import re
from typing import List, Dict, Pattern, Optional, Any, Match
from dataclasses import dataclass
from enum import Enum


class RedactionPattern(Enum):
    """Common sensitive data patterns"""
    PASSWORD = r'(?i)(password|passwd|pwd)[\s:=]+[^\s]+'
    API_KEY = r'(?i)(api[_-]?key|apikey)[\s:=]+[^\s]+'
    TOKEN = r'(?i)(token|bearer)[\s:=]+[^\s]+'
    SECRET = r'(?i)(secret|secret[_-]?key)[\s:=]+[^\s]+'
    DATABASE_URL = r'(?i)(mongodb|postgresql|mysql|postgres)://[^\s]+'
    AWS_KEY = r'(?i)(AKIA[0-9A-Z]{16})'
    PRIVATE_KEY = r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC )?PRIVATE KEY-----'
    CREDIT_CARD = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    SSN = r'\b\d{3}-\d{2}-\d{4}\b'
    EMAIL_PASSWORD = r'(?i)(email|mail)[\s:=]+[^\s]+[\s,]+(?:password|pwd)[\s:=]+[^\s]+'
    CONNECTION_STRING = r'(?i)(server|host|data source)=[^;]+;.*(?:password|pwd)=[^;]+'
    JWT = r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'


@dataclass
class RedactionRule:
    """A single redaction rule"""
    name: str
    pattern: Pattern[str]
    replacement: str = '[REDACTED]'
    preserve_length: bool = False
    preserve_prefix: int = 0
    preserve_suffix: int = 0


class RedactionEngine:
    """Engine for auto-redacting sensitive data"""

    def __init__(self) -> None:
        self.rules: List[RedactionRule] = []
        self._load_default_patterns()

    def _load_default_patterns(self) -> None:
        """Load default redaction patterns"""
        for pattern in RedactionPattern:
            self.add_pattern(
                name=pattern.name,
                pattern=pattern.value,
                replacement=f'[REDACTED_{pattern.name}]'
            )

    def add_pattern(
        self,
        name: str,
        pattern: str,
        replacement: str = '[REDACTED]',
        preserve_length: bool = False,
        preserve_prefix: int = 0,
        preserve_suffix: int = 0
    ) -> None:
        """Add a custom redaction pattern"""
        compiled_pattern: Pattern[str] = re.compile(pattern)
        rule = RedactionRule(
            name=name,
            pattern=compiled_pattern,
            replacement=replacement,
            preserve_length=preserve_length,
            preserve_prefix=preserve_prefix,
            preserve_suffix=preserve_suffix
        )
        self.rules.append(rule)

    def remove_pattern(self, name: str) -> bool:
        """Remove a redaction pattern by name"""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < initial_count

    def redact(self, text: str) -> str:
        """Apply all redaction rules to text"""
        result = text
        for rule in self.rules:
            result = self._apply_rule(result, rule)
        return result

    def _apply_rule(self, text: str, rule: RedactionRule) -> str:
        """Apply a single redaction rule"""
        def replace_match(match: Match[str]) -> str:
            matched_text: str = match.group(0)

            if rule.preserve_length:
                # Preserve original length with asterisks
                prefix = matched_text[:rule.preserve_prefix] if rule.preserve_prefix > 0 else ''
                suffix = matched_text[-rule.preserve_suffix:] if rule.preserve_suffix > 0 else ''
                middle_len = len(matched_text) - rule.preserve_prefix - rule.preserve_suffix
                middle = '*' * middle_len
                return prefix + middle + suffix
            elif rule.preserve_prefix > 0 or rule.preserve_suffix > 0:
                # Preserve prefix/suffix with redacted middle
                prefix = matched_text[:rule.preserve_prefix] if rule.preserve_prefix > 0 else ''
                suffix = matched_text[-rule.preserve_suffix:] if rule.preserve_suffix > 0 else ''
                return prefix + rule.replacement + suffix
            else:
                return rule.replacement

        result: str = rule.pattern.sub(replace_match, text)
        return result

    def detect_patterns(self, text: str) -> Dict[str, List[str]]:
        """Detect which patterns match in the text"""
        detections = {}
        for rule in self.rules:
            matches = rule.pattern.findall(text)
            if matches:
                detections[rule.name] = matches
        return detections

    def is_sensitive(self, text: str) -> bool:
        """Check if text contains sensitive data"""
        return bool(self.detect_patterns(text))

    def get_redaction_summary(self, original: str, redacted: str) -> Dict[str, int]:
        """Get summary of what was redacted"""
        summary = {}
        for rule in self.rules:
            original_matches = len(rule.pattern.findall(original))
            redacted_matches = len(rule.pattern.findall(redacted))
            if original_matches > redacted_matches:
                summary[rule.name] = original_matches - redacted_matches
        return summary

    def redact_dict(self, data: Dict[Any, Any], keys_to_redact: Optional[List[str]] = None) -> Dict[Any, Any]:
        """Redact sensitive values in a dictionary"""
        if keys_to_redact is None:
            keys_to_redact = ['password', 'secret', 'token', 'key', 'api_key', 'apikey']

        result: Dict[Any, Any] = {}
        for key, value in data.items():
            if any(k.lower() in str(key).lower() for k in keys_to_redact):
                result[key] = '[REDACTED]'
            elif isinstance(value, str):
                result[key] = self.redact(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, keys_to_redact)
            elif isinstance(value, list):
                result[key] = [
                    self.redact_dict(item, keys_to_redact) if isinstance(item, dict)
                    else self.redact(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


class RedactionService:
    """Service for redacting sensitive data from various sources."""

    def __init__(self):
        self.engine = RedactionEngine()

    def redact_error(self, error_message: str) -> str:
        """
        Redact sensitive data from error messages.

        Args:
            error_message: Error message that may contain sensitive data

        Returns:
            Redacted error message
        """
        # Apply standard redaction
        redacted = self.engine.redact(error_message)

        # Additional patterns for error messages
        # Redact email addresses
        redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', redacted)

        # Redact URLs with credentials
        redacted = re.sub(r'://[^@\s]+:[^@\s]+@', '://[REDACTED]:[REDACTED]@', redacted)

        # Redact key/token-like patterns
        redacted = re.sub(r'\bkey[_-]?[=:]\s*[^\s,;]+', 'key=[REDACTED]', redacted, flags=re.IGNORECASE)
        redacted = re.sub(r'\btoken[_-]?[=:]\s*[^\s,;]+', 'token=[REDACTED]', redacted, flags=re.IGNORECASE)

        return redacted
