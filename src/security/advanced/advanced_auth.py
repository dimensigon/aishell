"""
Advanced Authentication Module

Provides enterprise-grade authentication methods including:
- Two-factor authentication (TOTP)
- SSO integration (SAML, OAuth2)
- Certificate-based authentication
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib
import secrets
import base64
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AuthenticationMethod(Enum):
    """Available authentication methods"""
    PASSWORD = "password"
    TOTP = "totp"
    SSO_SAML = "sso_saml"
    SSO_OAUTH2 = "sso_oauth2"
    CERTIFICATE = "certificate"
    API_KEY = "api_key"


@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    success: bool
    method: AuthenticationMethod
    user_id: Optional[str] = None
    session_token: Optional[str] = None
    requires_2fa: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TwoFactorAuth:
    """
    Two-Factor Authentication (2FA) using TOTP (Time-based One-Time Password)

    Compatible with Google Authenticator, Authy, and other TOTP apps.
    """

    def __init__(self, issuer: str = "AI-Shell"):
        """
        Initialize 2FA manager

        Args:
            issuer: Application name shown in authenticator apps
        """
        self.issuer = issuer
        self.secret_length = 32  # 160 bits

        # Try to import pyotp (optional dependency)
        try:
            import pyotp
            self.pyotp = pyotp
            self.available = True
        except ImportError:
            logger.warning("pyotp not installed. 2FA features disabled. Install with: pip install pyotp")
            self.pyotp = None
            self.available = False

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key

        Returns:
            Base32-encoded secret key
        """
        if not self.available:
            raise RuntimeError("2FA not available: pyotp not installed")

        return self.pyotp.random_base32()

    def get_provisioning_uri(
        self,
        secret: str,
        user_email: str,
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate provisioning URI for QR code

        Args:
            secret: TOTP secret key
            user_email: User's email address
            user_name: Optional user display name

        Returns:
            otpauth:// URI for QR code generation
        """
        if not self.available:
            raise RuntimeError("2FA not available: pyotp not installed")

        totp = self.pyotp.TOTP(secret)
        name = user_name or user_email

        return totp.provisioning_uri(
            name=name,
            issuer_name=self.issuer
        )

    def verify_code(self, secret: str, code: str, window: int = 1) -> bool:
        """
        Verify TOTP code

        Args:
            secret: TOTP secret key
            code: 6-digit code from authenticator app
            window: Number of time windows to check (default 1 = ±30 seconds)

        Returns:
            True if code is valid
        """
        if not self.available:
            return False

        try:
            totp = self.pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
        except Exception as e:
            logger.error(f"2FA verification failed: {e}")
            return False

    def get_current_code(self, secret: str) -> Optional[str]:
        """
        Get current TOTP code (for testing/debugging)

        Args:
            secret: TOTP secret key

        Returns:
            Current 6-digit code
        """
        if not self.available:
            return None

        totp = self.pyotp.TOTP(secret)
        return totp.now()

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            # Format as XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)

        return codes


class SSOManager:
    """
    Single Sign-On (SSO) Manager

    Supports SAML 2.0 and OAuth 2.0 integration.
    """

    def __init__(self):
        """Initialize SSO manager"""
        self.saml_providers: Dict[str, Dict] = {}
        self.oauth_providers: Dict[str, Dict] = {}

        # Check for optional dependencies
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth
            self.saml_available = True
        except ImportError:
            logger.warning("python3-saml not installed. SAML features disabled.")
            self.saml_available = False

        try:
            from requests_oauthlib import OAuth2Session
            self.oauth_available = True
        except ImportError:
            logger.warning("requests-oauthlib not installed. OAuth features disabled.")
            self.oauth_available = False

    def configure_saml_provider(
        self,
        provider_name: str,
        idp_entity_id: str,
        idp_sso_url: str,
        idp_x509_cert: str,
        sp_entity_id: str,
        sp_acs_url: str
    ):
        """
        Configure SAML 2.0 identity provider

        Args:
            provider_name: Provider identifier (e.g., 'okta', 'azure')
            idp_entity_id: Identity Provider entity ID
            idp_sso_url: Identity Provider SSO URL
            idp_x509_cert: Identity Provider X.509 certificate
            sp_entity_id: Service Provider (our app) entity ID
            sp_acs_url: Service Provider Assertion Consumer Service URL
        """
        if not self.saml_available:
            raise RuntimeError("SAML not available: python3-saml not installed")

        self.saml_providers[provider_name] = {
            'strict': True,
            'debug': False,
            'sp': {
                'entityId': sp_entity_id,
                'assertionConsumerService': {
                    'url': sp_acs_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
                }
            },
            'idp': {
                'entityId': idp_entity_id,
                'singleSignOnService': {
                    'url': idp_sso_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                },
                'x509cert': idp_x509_cert
            }
        }

        logger.info(f"Configured SAML provider: {provider_name}")

    def configure_oauth_provider(
        self,
        provider_name: str,
        client_id: str,
        client_secret: str,
        authorization_url: str,
        token_url: str,
        userinfo_url: str,
        scopes: List[str]
    ):
        """
        Configure OAuth 2.0 provider

        Args:
            provider_name: Provider identifier (e.g., 'google', 'github')
            client_id: OAuth client ID
            client_secret: OAuth client secret
            authorization_url: Authorization endpoint
            token_url: Token endpoint
            userinfo_url: User info endpoint
            scopes: List of OAuth scopes
        """
        if not self.oauth_available:
            raise RuntimeError("OAuth not available: requests-oauthlib not installed")

        self.oauth_providers[provider_name] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'authorization_url': authorization_url,
            'token_url': token_url,
            'userinfo_url': userinfo_url,
            'scopes': scopes
        }

        logger.info(f"Configured OAuth provider: {provider_name}")

    def initiate_saml_login(self, provider_name: str) -> Optional[str]:
        """
        Initiate SAML login flow

        Args:
            provider_name: SAML provider name

        Returns:
            Redirect URL for SAML authentication
        """
        if provider_name not in self.saml_providers:
            logger.error(f"SAML provider not configured: {provider_name}")
            return None

        # In a real implementation, this would use OneLogin_Saml2_Auth
        # to generate the SAML request and return the IdP redirect URL
        logger.info(f"Initiating SAML login for: {provider_name}")
        return f"https://sso.example.com/saml/login?provider={provider_name}"

    def initiate_oauth_login(
        self,
        provider_name: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Initiate OAuth 2.0 login flow

        Args:
            provider_name: OAuth provider name
            redirect_uri: Callback URL after authentication
            state: CSRF protection state parameter

        Returns:
            Tuple of (authorization_url, state)
        """
        if provider_name not in self.oauth_providers:
            logger.error(f"OAuth provider not configured: {provider_name}")
            return None

        provider = self.oauth_providers[provider_name]

        if not self.oauth_available:
            return None

        from requests_oauthlib import OAuth2Session

        oauth = OAuth2Session(
            provider['client_id'],
            redirect_uri=redirect_uri,
            scope=provider['scopes'],
            state=state
        )

        authorization_url, state = oauth.authorization_url(
            provider['authorization_url']
        )

        logger.info(f"Initiating OAuth login for: {provider_name}")
        return authorization_url, state

    def complete_oauth_login(
        self,
        provider_name: str,
        authorization_response: str,
        state: str
    ) -> Optional[Dict[str, Any]]:
        """
        Complete OAuth 2.0 login flow

        Args:
            provider_name: OAuth provider name
            authorization_response: Full callback URL with auth code
            state: CSRF protection state parameter

        Returns:
            User information dict if successful
        """
        if provider_name not in self.oauth_providers:
            return None

        provider = self.oauth_providers[provider_name]

        if not self.oauth_available:
            return None

        try:
            from requests_oauthlib import OAuth2Session

            oauth = OAuth2Session(
                provider['client_id'],
                state=state
            )

            # Exchange authorization code for access token
            token = oauth.fetch_token(
                provider['token_url'],
                authorization_response=authorization_response,
                client_secret=provider['client_secret']
            )

            # Get user info
            response = oauth.get(provider['userinfo_url'])
            user_info = response.json()

            logger.info(f"OAuth login successful for: {provider_name}")
            return {
                'user_info': user_info,
                'access_token': token.get('access_token'),
                'provider': provider_name
            }

        except Exception as e:
            logger.error(f"OAuth login failed: {e}")
            return None


class CertificateAuth:
    """
    Certificate-based authentication using X.509 client certificates
    """

    def __init__(self, ca_cert_path: Optional[str] = None):
        """
        Initialize certificate authentication

        Args:
            ca_cert_path: Path to CA certificate for validation
        """
        self.ca_cert_path = ca_cert_path
        self.trusted_certificates: Dict[str, Dict] = {}

        # Check for cryptography library
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            self.x509 = x509
            self.backend = default_backend()
            self.available = True
        except ImportError:
            logger.warning("cryptography library not available")
            self.available = False

    def verify_certificate(
        self,
        cert_data: bytes,
        check_revocation: bool = True
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify client certificate

        Args:
            cert_data: X.509 certificate in PEM or DER format
            check_revocation: Check certificate revocation status

        Returns:
            Tuple of (is_valid, certificate_info)
        """
        if not self.available:
            return False, {'error': 'Certificate validation not available'}

        try:
            # Load certificate
            cert = self.x509.load_pem_x509_certificate(cert_data, self.backend)

            # Extract certificate info
            cert_info = {
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'serial_number': cert.serial_number,
                'not_before': cert.not_valid_before,
                'not_after': cert.not_valid_after,
                'fingerprint': cert.fingerprint(hashlib.sha256()).hex()
            }

            # Check validity period
            now = datetime.utcnow()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                return False, {'error': 'Certificate expired or not yet valid'}

            # Additional checks could be added here:
            # - CA chain validation
            # - CRL/OCSP checking
            # - Certificate pinning

            logger.info(f"Certificate verified for: {cert_info['subject']}")
            return True, cert_info

        except Exception as e:
            logger.error(f"Certificate verification failed: {e}")
            return False, {'error': str(e)}

    def register_trusted_certificate(
        self,
        cert_id: str,
        cert_data: bytes,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a trusted client certificate

        Args:
            cert_id: Certificate identifier
            cert_data: Certificate data
            user_id: Associated user ID
            metadata: Additional metadata

        Returns:
            True if successful
        """
        is_valid, cert_info = self.verify_certificate(cert_data, check_revocation=False)

        if not is_valid:
            logger.error(f"Cannot register invalid certificate: {cert_id}")
            return False

        self.trusted_certificates[cert_id] = {
            'user_id': user_id,
            'cert_info': cert_info,
            'metadata': metadata or {},
            'registered_at': datetime.now()
        }

        logger.info(f"Registered trusted certificate: {cert_id}")
        return True

    def authenticate_with_certificate(
        self,
        cert_data: bytes
    ) -> AuthenticationResult:
        """
        Authenticate user with client certificate

        Args:
            cert_data: X.509 certificate

        Returns:
            AuthenticationResult
        """
        is_valid, cert_info = self.verify_certificate(cert_data)

        if not is_valid:
            return AuthenticationResult(
                success=False,
                method=AuthenticationMethod.CERTIFICATE,
                error_message=cert_info.get('error', 'Invalid certificate')
            )

        # Check if certificate is registered
        fingerprint = cert_info.get('fingerprint')
        for cert_id, trusted_cert in self.trusted_certificates.items():
            if trusted_cert['cert_info'].get('fingerprint') == fingerprint:
                # Generate session token
                session_token = secrets.token_urlsafe(32)

                return AuthenticationResult(
                    success=True,
                    method=AuthenticationMethod.CERTIFICATE,
                    user_id=trusted_cert['user_id'],
                    session_token=session_token,
                    metadata={'cert_id': cert_id}
                )

        return AuthenticationResult(
            success=False,
            method=AuthenticationMethod.CERTIFICATE,
            error_message='Certificate not registered'
        )
