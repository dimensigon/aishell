"""
Advanced Security Module - v2.0.0 Features

This module provides enterprise-grade security features including:
- Two-factor authentication (TOTP)
- SSO integration (SAML, OAuth2)
- Certificate-based authentication
- Database activity monitoring
- Anomaly detection for unusual query patterns
- Security scanning and vulnerability assessment
"""

from src.security.advanced.advanced_auth import (
    TwoFactorAuth,
    SSOManager,
    CertificateAuth,
    AuthenticationMethod
)
from src.security.advanced.activity_monitor import (
    ActivityMonitor,
    SecurityEvent,
    AnomalyDetector,
    ThreatLevel
)

__all__ = [
    'TwoFactorAuth',
    'SSOManager',
    'CertificateAuth',
    'AuthenticationMethod',
    'ActivityMonitor',
    'SecurityEvent',
    'AnomalyDetector',
    'ThreatLevel'
]

__version__ = '2.0.0'
