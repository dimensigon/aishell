"""
PII (Personally Identifiable Information) detection and masking.

Provides automatic detection and masking of sensitive data.
"""

import re
from typing import List, Dict, Tuple


class PIIDetector:
    """Detects and masks PII in text."""

    # Regex patterns for common PII types
    PATTERNS = {
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }

    def __init__(self):
        """Initialize PII detector."""
        self._compiled_patterns = {
            name: re.compile(pattern)
            for name, pattern in self.PATTERNS.items()
        }

    def detect_pii(self, text: str) -> List[Dict[str, any]]:
        """Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            List of detected PII instances with type and location
        """
        detections = []

        for pii_type, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                detections.append({
                    'type': pii_type,
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })

        return detections

    def mask_pii(self, text: str, mask_char: str = '*') -> str:
        """Mask PII in text.

        Args:
            text: Text containing PII
            mask_char: Character to use for masking

        Returns:
            Text with PII masked
        """
        result = text

        # Process patterns in order of specificity (most specific first)
        for pii_type, pattern in self._compiled_patterns.items():
            if pii_type == 'ssn':
                # Mask SSN: XXX-XX-1234 (keep last 4 digits)
                result = pattern.sub(lambda m: f'***-**-{m.group()[-4:]}', result)
            elif pii_type == 'email':
                # Mask email: j***@example.com
                def mask_email(match):
                    email = match.group()
                    parts = email.split('@')
                    if len(parts) == 2:
                        return f'{parts[0][0]}***@{parts[1]}'
                    return '***'
                result = pattern.sub(mask_email, result)
            elif pii_type == 'phone':
                # Mask phone: XXX-XXX-1234 (keep last 4 digits)
                result = pattern.sub(lambda m: f'***-***-{m.group()[-4:]}', result)
            elif pii_type == 'credit_card':
                # Mask credit card: XXXX-XXXX-XXXX-1234
                result = pattern.sub(lambda m: f'****-****-****-{m.group()[-4:]}', result)
            else:
                # Generic masking
                result = pattern.sub(lambda m: mask_char * len(m.group()), result)

        return result

    def redact_pii(self, text: str, replacement: str = '[REDACTED]') -> str:
        """Completely redact PII from text.

        Args:
            text: Text containing PII
            replacement: Replacement text for redacted PII

        Returns:
            Text with PII redacted
        """
        result = text

        for pattern in self._compiled_patterns.values():
            result = pattern.sub(replacement, result)

        return result

    def anonymize_pii(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Anonymize PII with reversible tokens.

        Args:
            text: Text containing PII

        Returns:
            Tuple of (anonymized text, mapping dictionary)
        """
        result = text
        mapping = {}
        counter = 1

        for pii_type, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(result):
                token = f'<{pii_type.upper()}_{counter}>'
                mapping[token] = match.group()
                result = result.replace(match.group(), token, 1)
                counter += 1

        return result, mapping

    def has_pii(self, text: str) -> bool:
        """Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII is detected
        """
        for pattern in self._compiled_patterns.values():
            if pattern.search(text):
                return True
        return False

    def get_pii_types(self, text: str) -> List[str]:
        """Get types of PII present in text.

        Args:
            text: Text to analyze

        Returns:
            List of PII types found
        """
        found_types = []

        for pii_type, pattern in self._compiled_patterns.items():
            if pattern.search(text):
                found_types.append(pii_type)

        return found_types
