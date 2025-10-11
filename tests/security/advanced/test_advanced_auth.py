"""
Tests for Advanced Authentication
"""

import pytest
from src.security.advanced.advanced_auth import (
    TwoFactorAuth,
    SSOManager,
    CertificateAuth,
    AuthenticationMethod,
    AuthenticationResult
)


class TestTwoFactorAuth:
    """Test 2FA functionality"""

    @pytest.fixture
    def twofa(self):
        """Create TwoFactorAuth instance"""
        return TwoFactorAuth(issuer="AI-Shell-Test")

    def test_initialization(self, twofa):
        """Test 2FA initialization"""
        assert twofa.issuer == "AI-Shell-Test"

    @pytest.mark.skipif(
        not pytest.importorskip("pyotp", reason="pyotp not installed"),
        reason="pyotp required for 2FA tests"
    )
    def test_generate_secret(self, twofa):
        """Test secret generation"""
        if not twofa.available:
            pytest.skip("pyotp not available")

        secret = twofa.generate_secret()
        assert secret is not None
        assert len(secret) >= 16

    @pytest.mark.skipif(
        not pytest.importorskip("pyotp", reason="pyotp not installed"),
        reason="pyotp required"
    )
    def test_verify_code(self, twofa):
        """Test TOTP code verification"""
        if not twofa.available:
            pytest.skip("pyotp not available")

        secret = twofa.generate_secret()
        code = twofa.get_current_code(secret)

        # Verify current code
        assert twofa.verify_code(secret, code) is True

        # Invalid code should fail
        assert twofa.verify_code(secret, "000000") is False

    def test_generate_backup_codes(self, twofa):
        """Test backup code generation"""
        codes = twofa.generate_backup_codes(10)

        assert len(codes) == 10
        for code in codes:
            assert '-' in code
            assert len(code) == 9  # XXXX-XXXX format

    @pytest.mark.skipif(
        not pytest.importorskip("pyotp", reason="pyotp not installed"),
        reason="pyotp required"
    )
    def test_provisioning_uri(self, twofa):
        """Test provisioning URI generation"""
        if not twofa.available:
            pytest.skip("pyotp not available")

        secret = twofa.generate_secret()
        uri = twofa.get_provisioning_uri(secret, "test@example.com", "Test User")

        assert uri.startswith("otpauth://")
        assert "AI-Shell-Test" in uri
        assert "Test+User" in uri or "test@example.com" in uri


class TestSSOManager:
    """Test SSO Manager"""

    @pytest.fixture
    def sso_manager(self):
        """Create SSOManager instance"""
        return SSOManager()

    def test_initialization(self, sso_manager):
        """Test SSO manager initialization"""
        assert sso_manager is not None
        assert isinstance(sso_manager.saml_providers, dict)
        assert isinstance(sso_manager.oauth_providers, dict)

    def test_configure_oauth_provider(self, sso_manager):
        """Test OAuth provider configuration"""
        sso_manager.configure_oauth_provider(
            provider_name="test_oauth",
            client_id="test_client",
            client_secret="test_secret",
            authorization_url="https://example.com/oauth/authorize",
            token_url="https://example.com/oauth/token",
            userinfo_url="https://example.com/oauth/userinfo",
            scopes=["email", "profile"]
        )

        assert "test_oauth" in sso_manager.oauth_providers
        assert sso_manager.oauth_providers["test_oauth"]["client_id"] == "test_client"

    @pytest.mark.skipif(
        not pytest.importorskip("onelogin.saml2.auth", reason="python3-saml not installed"),
        reason="python3-saml required"
    )
    def test_configure_saml_provider(self, sso_manager):
        """Test SAML provider configuration"""
        if not sso_manager.saml_available:
            pytest.skip("python3-saml not available")

        sso_manager.configure_saml_provider(
            provider_name="test_saml",
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            idp_x509_cert="FAKE_CERT",
            sp_entity_id="https://sp.example.com",
            sp_acs_url="https://sp.example.com/acs"
        )

        assert "test_saml" in sso_manager.saml_providers


class TestCertificateAuth:
    """Test Certificate Authentication"""

    @pytest.fixture
    def cert_auth(self):
        """Create CertificateAuth instance"""
        return CertificateAuth()

    def test_initialization(self, cert_auth):
        """Test certificate auth initialization"""
        assert cert_auth is not None
        assert isinstance(cert_auth.trusted_certificates, dict)

    def test_verify_invalid_certificate(self, cert_auth):
        """Test verifying invalid certificate"""
        if not cert_auth.available:
            pytest.skip("cryptography not available")

        # Invalid certificate data
        is_valid, cert_info = cert_auth.verify_certificate(b"invalid cert data")

        assert is_valid is False
        assert 'error' in cert_info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
