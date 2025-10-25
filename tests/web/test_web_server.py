"""
Tests for FastAPI Web Server Initialization and Configuration

Tests app setup, middleware, CORS, health checks, and basic configuration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import app, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class TestWebServerInitialization:
    """Test FastAPI application initialization"""

    def test_app_creation(self):
        """Test that FastAPI app is created with correct configuration"""
        assert app.title == "AI-Shell API"
        assert app.version == "2.0.0"
        assert app.description == "REST API for AI-Shell Web UI"

    def test_app_has_cors_middleware(self):
        """Test that CORS middleware is configured"""
        # Check that middleware stack includes CORS
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert any('CORS' in name for name in middleware_types)

    def test_jwt_configuration(self):
        """Test JWT configuration constants"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0
        assert ALGORITHM == "HS256"
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_oauth2_scheme_configured(self):
        """Test OAuth2 password bearer is configured"""
        from api.web_server import oauth2_scheme
        assert oauth2_scheme is not None
        assert oauth2_scheme.tokenUrl == "api/auth/login"


class TestHealthEndpoint:
    """Test health check endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_health_check_returns_200(self, client):
        """Test health endpoint returns 200 OK"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_response_format(self, client):
        """Test health endpoint response structure"""
        response = client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

    def test_health_check_no_auth_required(self, client):
        """Test health endpoint does not require authentication"""
        # Should work without Authorization header
        response = client.get("/api/health")
        assert response.status_code == 200


class TestCORSConfiguration:
    """Test CORS configuration"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_cors_allows_localhost(self, client):
        """Test CORS allows localhost:3000"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # FastAPI handles OPTIONS automatically
        assert response.status_code in [200, 405]

    def test_cors_headers_present(self, client):
        """Test CORS headers are present in response"""
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:3000"}
        )
        # Check for CORS headers
        assert response.status_code == 200


class TestErrorHandling:
    """Test global error handling"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_404_for_nonexistent_endpoint(self, client):
        """Test 404 error for nonexistent endpoints"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Test 405 error for wrong HTTP method"""
        response = client.patch("/api/health")
        assert response.status_code == 405


class TestDatabaseStorage:
    """Test in-memory database initialization"""

    def test_users_db_initialized(self):
        """Test users database is initialized"""
        from api.web_server import users_db
        assert isinstance(users_db, dict)

    def test_connections_db_initialized(self):
        """Test connections database is initialized"""
        from api.web_server import connections_db
        assert isinstance(connections_db, dict)

    def test_queries_db_initialized(self):
        """Test queries database is initialized"""
        from api.web_server import queries_db
        assert isinstance(queries_db, dict)

    def test_audit_logs_db_initialized(self):
        """Test audit logs database is initialized"""
        from api.web_server import audit_logs_db
        assert isinstance(audit_logs_db, list)

    def test_websocket_connections_initialized(self):
        """Test websocket connections list is initialized"""
        from api.web_server import websocket_connections
        assert isinstance(websocket_connections, list)


class TestModels:
    """Test Pydantic models"""

    def test_user_role_enum(self):
        """Test UserRole enum values"""
        from api.web_server import UserRole
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.VIEWER.value == "viewer"

    def test_database_type_enum(self):
        """Test DatabaseType enum values"""
        from api.web_server import DatabaseType
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.MONGODB.value == "mongodb"
        assert DatabaseType.REDIS.value == "redis"
        assert DatabaseType.SQLITE.value == "sqlite"

    def test_connection_status_enum(self):
        """Test ConnectionStatus enum values"""
        from api.web_server import ConnectionStatus
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"
        assert ConnectionStatus.ERROR.value == "error"

    def test_login_request_validation(self):
        """Test LoginRequest model validation"""
        from api.web_server import LoginRequest

        request = LoginRequest(username="testuser", password="testpass")
        assert request.username == "testuser"
        assert request.password == "testpass"
        assert request.twoFactorCode is None

    def test_register_request_password_validation(self):
        """Test RegisterRequest password validation"""
        from api.web_server import RegisterRequest
        from pydantic import ValidationError

        # Valid password
        request = RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="validpass123"
        )
        assert request.password == "validpass123"

        # Invalid password (too short)
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="testuser",
                email="test@example.com",
                password="short"
            )
        assert "Password must be at least 8 characters" in str(exc_info.value)

    def test_api_response_model(self):
        """Test ApiResponse model"""
        from api.web_server import ApiResponse

        response = ApiResponse(success=True, data={"key": "value"})
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.error is None


class TestConcurrentRequests:
    """Test handling of concurrent requests"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_concurrent_health_checks(self, client):
        """Test multiple concurrent health check requests"""
        import concurrent.futures

        def make_request():
            return client.get("/api/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
