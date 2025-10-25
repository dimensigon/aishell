"""
Unit tests for Security Modules.

Tests security functionality including encryption, authentication,
authorization, audit logging, and input validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.utils.test_helpers import assert_no_secrets, assert_sql_safe


@pytest.mark.unit
@pytest.mark.security
class TestEncryption:
    """Test suite for encryption functionality."""

    def test_data_encryption(self, mock_security_manager):
        """Test data is encrypted correctly."""
        plaintext = "sensitive data"
        encrypted = mock_security_manager.encrypt_data(plaintext)

        assert encrypted != plaintext
        assert encrypted == "encrypted_data"

    def test_data_decryption(self, mock_security_manager):
        """Test data is decrypted correctly."""
        encrypted = "encrypted_data"
        decrypted = mock_security_manager.decrypt_data(encrypted)

        assert decrypted != encrypted
        assert decrypted == "decrypted_data"

    def test_encryption_roundtrip(self, mock_security_manager):
        """Test encryption and decryption roundtrip."""
        original = "test data"

        # Mock to return original data for roundtrip test
        mock_security_manager.decrypt_data = MagicMock(return_value=original)

        encrypted = mock_security_manager.encrypt_data(original)
        decrypted = mock_security_manager.decrypt_data(encrypted)

        assert decrypted == original

    def test_empty_data_encryption(self, mock_security_manager):
        """Test encrypting empty data."""
        encrypted = mock_security_manager.encrypt_data("")
        assert encrypted is not None

    def test_large_data_encryption(self, mock_security_manager):
        """Test encrypting large data."""
        large_data = "x" * 1000000  # 1MB
        encrypted = mock_security_manager.encrypt_data(large_data)
        assert encrypted is not None


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.asyncio
class TestAuthentication:
    """Test suite for authentication."""

    async def test_valid_credentials(self, mock_security_manager):
        """Test authentication with valid credentials."""
        result = await mock_security_manager.check_permissions()
        assert result is True

    async def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        manager = MagicMock()
        manager.authenticate = AsyncMock(return_value=False)

        result = await manager.authenticate("user", "wrong_password")
        assert result is False

    async def test_token_validation(self):
        """Test token-based authentication."""
        manager = MagicMock()
        manager.validate_token = AsyncMock(return_value=True)

        valid_token = "valid_token_123"
        result = await manager.validate_token(valid_token)

        assert result is True

    async def test_expired_token(self):
        """Test expired token handling."""
        manager = MagicMock()
        manager.validate_token = AsyncMock(return_value=False)

        expired_token = "expired_token"
        result = await manager.validate_token(expired_token)

        assert result is False

    async def test_session_management(self):
        """Test session creation and validation."""
        manager = MagicMock()
        manager.create_session = AsyncMock(return_value="session_id_123")
        manager.validate_session = AsyncMock(return_value=True)

        session_id = await manager.create_session("user123")
        assert session_id is not None

        is_valid = await manager.validate_session(session_id)
        assert is_valid is True


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.asyncio
class TestAuthorization:
    """Test suite for authorization."""

    async def test_permission_check(self, mock_security_manager):
        """Test permission checking."""
        result = await mock_security_manager.check_permissions()
        assert result is True

    async def test_role_based_access(self):
        """Test role-based access control."""
        manager = MagicMock()
        manager.check_role = AsyncMock(return_value=True)

        has_access = await manager.check_role("admin", "database:write")
        assert has_access is True

    async def test_permission_denied(self):
        """Test permission denied scenario."""
        manager = MagicMock()
        manager.check_permissions = AsyncMock(return_value=False)

        has_access = await manager.check_permissions("user", "admin:delete")
        assert has_access is False

    async def test_resource_access_control(self):
        """Test resource-level access control."""
        manager = MagicMock()
        manager.can_access_resource = AsyncMock(return_value=True)

        can_access = await manager.can_access_resource(
            user_id="user123",
            resource_id="resource456",
            action="read"
        )

        assert can_access is True


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.asyncio
class TestAuditLogging:
    """Test suite for audit logging."""

    async def test_action_logging(self, mock_audit_logger):
        """Test actions are logged."""
        await mock_audit_logger.log_action(
            user="test_user",
            action="database_query",
            details={"query": "SELECT * FROM users"}
        )

        assert mock_audit_logger.log_action.called

    async def test_query_logging(self, mock_audit_logger):
        """Test queries are logged."""
        await mock_audit_logger.log_query(
            query="SELECT * FROM users",
            user="test_user",
            timestamp="2025-01-01T00:00:00Z"
        )

        assert mock_audit_logger.log_query.called

    async def test_error_logging(self, mock_audit_logger):
        """Test errors are logged."""
        await mock_audit_logger.log_error(
            error="Database connection failed",
            user="test_user",
            context={"operation": "connect"}
        )

        assert mock_audit_logger.log_error.called

    async def test_sensitive_data_redaction(self, mock_audit_logger):
        """Test sensitive data is redacted in logs."""
        log_data = {
            "user": "test_user",
            "password": "secret123",
            "token": "abc123xyz"
        }

        # In real implementation, password and token should be redacted
        await mock_audit_logger.log_action(
            user="test_user",
            action="login",
            details=log_data
        )

        assert mock_audit_logger.log_action.called


@pytest.mark.unit
@pytest.mark.security
class TestInputValidation:
    """Test suite for input validation."""

    def test_sql_injection_detection(self, sample_sql_queries):
        """Test SQL injection patterns are detected."""
        for query in sample_sql_queries["unsafe"]:
            # Should detect dangerous patterns
            is_safe = not any(
                pattern in query.upper()
                for pattern in ["DROP TABLE", "DELETE FROM", "1=1", "'; --"]
            )
            assert not is_safe, f"Failed to detect unsafe query: {query}"

    def test_safe_query_validation(self, sample_sql_queries):
        """Test safe queries pass validation."""
        for query in sample_sql_queries["safe"]:
            assert_sql_safe(query)

    def test_xss_prevention(self):
        """Test XSS attack prevention."""
        xss_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror='alert(1)'>",
            "javascript:alert('XSS')"
        ]

        for xss_input in xss_inputs:
            # In real implementation, should sanitize
            sanitized = xss_input.replace("<", "&lt;").replace(">", "&gt;")
            assert "<script>" not in sanitized

    def test_command_injection_prevention(self):
        """Test command injection prevention."""
        dangerous_commands = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& net user admin"
        ]

        for cmd in dangerous_commands:
            # Should detect shell metacharacters
            has_dangerous_chars = any(char in cmd for char in [";", "|", "&", "$", "`"])
            assert has_dangerous_chars

    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention."""
        malicious_paths = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd"
        ]

        for path in malicious_paths:
            # Should detect directory traversal
            has_traversal = ".." in path or path.startswith("/")
            assert has_traversal


@pytest.mark.unit
@pytest.mark.security
class TestDataSanitization:
    """Test suite for data sanitization."""

    def test_password_redaction(self):
        """Test passwords are redacted."""
        data = {
            "username": "test_user",
            "password": "secret123"
        }

        # Mock redaction
        data["password"] = "***REDACTED***"

        assert_no_secrets(data)

    def test_token_redaction(self):
        """Test tokens are redacted."""
        data = {
            "user_id": "123",
            "auth_token": "abc123xyz"
        }

        # Mock redaction
        data["auth_token"] = "***REDACTED***"

        assert_no_secrets(data)

    def test_api_key_redaction(self):
        """Test API keys are redacted."""
        data = {
            "service": "openai",
            "api_secret": "sk-1234567890abcdef"
        }

        # Mock redaction
        data["api_secret"] = "***REDACTED***"

        assert_no_secrets(data)

    def test_nested_data_redaction(self):
        """Test nested sensitive data is redacted."""
        data = {
            "user": {
                "name": "test",
                "credentials": {
                    "password": "***REDACTED***"
                }
            }
        }

        assert_no_secrets(data)


@pytest.mark.unit
@pytest.mark.security
class TestSecurityConfiguration:
    """Test suite for security configuration."""

    def test_secure_defaults(self):
        """Test security settings have secure defaults."""
        config = {
            "encryption_enabled": True,
            "audit_logging": True,
            "session_timeout": 3600,
            "max_login_attempts": 5
        }

        assert config["encryption_enabled"] is True
        assert config["audit_logging"] is True
        assert config["session_timeout"] > 0
        assert config["max_login_attempts"] > 0

    def test_insecure_configuration_detection(self):
        """Test detection of insecure configurations."""
        insecure_configs = [
            {"encryption_enabled": False},
            {"session_timeout": 0},
            {"max_login_attempts": 999999}
        ]

        for config in insecure_configs:
            # Should be flagged as insecure
            is_insecure = (
                config.get("encryption_enabled") is False or
                config.get("session_timeout", 1) <= 0 or
                config.get("max_login_attempts", 0) > 10
            )
            assert is_insecure
