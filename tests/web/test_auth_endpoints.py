"""
Tests for Authentication Endpoints

Tests user registration, login, logout, JWT token validation, 2FA, and session management.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import (
    app, users_db, audit_logs_db, SECRET_KEY, ALGORITHM,
    hash_password, verify_password, create_access_token
)


class TestPasswordUtilities:
    """Test password hashing and verification utilities"""

    def test_hash_password_returns_string(self):
        """Test password hashing returns a string"""
        hashed = hash_password("testpassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_is_deterministic(self):
        """Test same password produces same hash"""
        password = "testpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 == hash2

    def test_different_passwords_produce_different_hashes(self):
        """Test different passwords produce different hashes"""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_user_data(self):
        """Test token contains encoded user data"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"

    def test_token_expiration(self):
        """Test token has expiration time"""
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded

        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        assert exp_time > now

    def test_expired_token_raises_error(self):
        """Test expired token raises exception"""
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


class TestRegistrationEndpoint:
    """Test user registration endpoint"""

    @pytest.fixture(autouse=True)
    def clear_db(self):
        """Clear users database before each test"""
        users_db.clear()
        audit_logs_db.clear()
        yield
        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_register_new_user_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "validpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User registered successfully"

    def test_register_creates_user_in_db(self, client):
        """Test registration creates user in database"""
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )

        assert len(users_db) == 1
        user = list(users_db.values())[0]
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert user["role"] == "user"

    def test_register_creates_audit_log(self, client):
        """Test registration creates audit log entry"""
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )

        assert len(audit_logs_db) == 1
        log = audit_logs_db[0]
        assert log["action"] == "register"
        assert log["resource"] == "user"

    def test_register_duplicate_username_fails(self, client):
        """Test registration fails for duplicate username"""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "user1@example.com",
                "password": "password123"
            }
        )

        # Second registration with same username
        response = client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email_fails(self, client):
        """Test registration fails with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_short_password_fails(self, client):
        """Test registration fails with short password"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_passwords_are_hashed(self, client):
        """Test registered passwords are hashed"""
        password = "mypassword123"
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": password
            }
        )

        user = list(users_db.values())[0]
        # Password should be hashed, not plain text
        assert user["password"] != password
        assert len(user["password"]) > len(password)


class TestLoginEndpoint:
    """Test user login endpoint"""

    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Create a test user before each test"""
        users_db.clear()
        audit_logs_db.clear()

        users_db["test-id"] = {
            "id": "test-id",
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        yield
        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_login_success(self, client):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_login_returns_tokens(self, client):
        """Test login returns access and refresh tokens"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        data = response.json()["data"]
        assert "accessToken" in data
        assert "refreshToken" in data
        assert "expiresIn" in data
        assert isinstance(data["accessToken"], str)
        assert isinstance(data["refreshToken"], str)

    def test_login_returns_user_info(self, client):
        """Test login returns user information"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        user_data = response.json()["data"]["user"]
        assert user_data["username"] == "testuser"
        assert user_data["email"] == "test@example.com"
        assert "password" not in user_data  # Password should not be returned

    def test_login_updates_last_login(self, client):
        """Test login updates user's last login time"""
        assert users_db["test-id"]["lastLogin"] is None

        client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        assert users_db["test-id"]["lastLogin"] is not None

    def test_login_creates_audit_log(self, client):
        """Test login creates audit log entry"""
        client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        assert len(audit_logs_db) > 0
        log = audit_logs_db[0]
        assert log["action"] == "login"

    def test_login_wrong_password(self, client):
        """Test login fails with wrong password"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login fails with nonexistent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_login_2fa_required(self, client):
        """Test login requires 2FA when enabled"""
        # Enable 2FA for user
        users_db["test-id"]["twoFactorEnabled"] = True

        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "2FA code required"
        assert data["data"]["requires2FA"] is True


class TestLogoutEndpoint:
    """Test user logout endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self):
        """Create authenticated user and return token"""
        users_db.clear()
        audit_logs_db.clear()

        user_id = "test-id"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": datetime.utcnow().isoformat()
        }

        token = create_access_token({"sub": user_id})
        yield token

        users_db.clear()
        audit_logs_db.clear()

    def test_logout_requires_authentication(self, client):
        """Test logout requires valid token"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401

    def test_logout_success(self, client, auth_token):
        """Test successful logout"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Logged out successfully"

    def test_logout_creates_audit_log(self, client, auth_token):
        """Test logout creates audit log entry"""
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert len(audit_logs_db) > 0
        log = audit_logs_db[0]
        assert log["action"] == "logout"


class TestGetCurrentUserEndpoint:
    """Test get current user endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self):
        """Create authenticated user and return token"""
        users_db.clear()

        user_id = "test-id"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": datetime.utcnow().isoformat()
        }

        token = create_access_token({"sub": user_id})
        yield token

        users_db.clear()

    def test_get_current_user_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_success(self, client, auth_token):
        """Test successful retrieval of current user"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"

    def test_get_current_user_no_password(self, client, auth_token):
        """Test response does not include password"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        user_data = response.json()["data"]
        assert "password" not in user_data

    def test_get_current_user_invalid_token(self, client):
        """Test invalid token returns 401"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
