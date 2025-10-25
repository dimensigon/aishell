"""
Tests for User Management Endpoints

Tests user listing, admin access control, and user management operations.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import (
    app, users_db, audit_logs_db,
    hash_password, create_access_token, UserRole
)


class TestGetUsers:
    """Test GET /api/users endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        audit_logs_db.clear()

        # Create admin user
        admin_id = "admin-user"
        users_db[admin_id] = {
            "id": admin_id,
            "username": "adminuser",
            "email": "admin@example.com",
            "password": hash_password("adminpass123"),
            "role": UserRole.ADMIN.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        # Create regular user
        user_id = "regular-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "regularuser",
            "email": "user@example.com",
            "password": hash_password("userpass123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        # Create viewer user
        viewer_id = "viewer-user"
        users_db[viewer_id] = {
            "id": viewer_id,
            "username": "vieweruser",
            "email": "viewer@example.com",
            "password": hash_password("viewerpass123"),
            "role": UserRole.VIEWER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        self.admin_token = create_access_token({"sub": admin_id})
        self.user_token = create_access_token({"sub": user_id})
        self.viewer_token = create_access_token({"sub": viewer_id})

        yield

        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_get_users_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.get("/api/users")
        assert response.status_code == 401

    def test_get_users_requires_admin(self, client):
        """Test endpoint requires admin role"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_get_users_viewer_denied(self, client):
        """Test viewer role is denied access"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.viewer_token}"}
        )

        assert response.status_code == 403

    def test_get_users_admin_success(self, client):
        """Test admin can retrieve users"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_users_returns_paginated_response(self, client):
        """Test response has pagination structure"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pageSize" in data
        assert "totalPages" in data

    def test_get_users_returns_all_users(self, client):
        """Test all users are returned"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_get_users_no_passwords_in_response(self, client):
        """Test passwords are not included in response"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        users = response.json()["data"]["items"]
        for user in users:
            assert "password" not in user

    def test_get_users_includes_all_fields(self, client):
        """Test user objects have all expected fields"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        users = response.json()["data"]["items"]
        user = users[0]

        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "role" in user
        assert "twoFactorEnabled" in user
        assert "createdAt" in user

    def test_get_users_default_pagination(self, client):
        """Test default pagination parameters"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert data["page"] == 1
        assert data["pageSize"] == 20

    def test_get_users_custom_page_size(self, client):
        """Test custom page size"""
        response = client.get(
            "/api/users?pageSize=2",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert data["pageSize"] == 2
        assert len(data["items"]) == 2

    def test_get_users_second_page(self, client):
        """Test retrieval of second page"""
        response = client.get(
            "/api/users?page=2&pageSize=2",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert data["page"] == 2
        assert len(data["items"]) == 1  # 3 total, 2 per page, page 2 has 1

    def test_get_users_total_pages(self, client):
        """Test total pages calculation"""
        response = client.get(
            "/api/users?pageSize=2",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 3
        assert data["totalPages"] == 2  # ceil(3/2) = 2

    def test_get_users_empty_page(self, client):
        """Test requesting page beyond available data"""
        response = client.get(
            "/api/users?page=10",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        data = response.json()["data"]
        assert data["items"] == []


class TestUserRoles:
    """Test user role validation and permissions"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()

        yield

        users_db.clear()

    def test_admin_role_value(self):
        """Test admin role value"""
        assert UserRole.ADMIN.value == "admin"

    def test_user_role_value(self):
        """Test user role value"""
        assert UserRole.USER.value == "user"

    def test_viewer_role_value(self):
        """Test viewer role value"""
        assert UserRole.VIEWER.value == "viewer"

    def test_user_created_with_default_role(self):
        """Test new users get default role"""
        from fastapi.testclient import TestClient
        client = TestClient(app)

        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200

        # Check user has default 'user' role
        user = list(users_db.values())[0]
        assert user["role"] == UserRole.USER.value


class TestUserDataFormat:
    """Test user data format and validation"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()

        admin_id = "admin-user"
        users_db[admin_id] = {
            "id": admin_id,
            "username": "adminuser",
            "email": "admin@example.com",
            "password": hash_password("adminpass123"),
            "role": UserRole.ADMIN.value,
            "twoFactorEnabled": True,
            "createdAt": "2024-01-01T00:00:00",
            "lastLogin": "2024-01-15T12:00:00"
        }

        self.admin_token = create_access_token({"sub": admin_id})

        yield

        users_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_user_id_is_string(self, client):
        """Test user ID is a string"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        user = response.json()["data"]["items"][0]
        assert isinstance(user["id"], str)

    def test_user_username_is_string(self, client):
        """Test username is a string"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        user = response.json()["data"]["items"][0]
        assert isinstance(user["username"], str)

    def test_user_email_is_valid_format(self, client):
        """Test email has valid format"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        user = response.json()["data"]["items"][0]
        assert "@" in user["email"]

    def test_user_role_is_valid_enum(self, client):
        """Test role is valid enum value"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        user = response.json()["data"]["items"][0]
        valid_roles = [UserRole.ADMIN.value, UserRole.USER.value, UserRole.VIEWER.value]
        assert user["role"] in valid_roles

    def test_user_two_factor_is_boolean(self, client):
        """Test twoFactorEnabled is boolean"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        user = response.json()["data"]["items"][0]
        assert isinstance(user["twoFactorEnabled"], bool)

    def test_user_created_at_is_iso_format(self, client):
        """Test createdAt is ISO format timestamp"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        user = response.json()["data"]["items"][0]
        # Should be parseable as datetime
        datetime.fromisoformat(user["createdAt"])

    def test_user_last_login_optional(self, client):
        """Test lastLogin can be null"""
        # Create user without lastLogin
        user_id = "new-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "newuser",
            "email": "new@example.com",
            "password": hash_password("password123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        users = response.json()["data"]["items"]
        new_user = next(u for u in users if u["id"] == user_id)
        assert new_user["lastLogin"] is None


class TestRateLimiting:
    """Test rate limiting for user endpoints (basic tests)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()

        admin_id = "admin-user"
        users_db[admin_id] = {
            "id": admin_id,
            "username": "adminuser",
            "email": "admin@example.com",
            "password": hash_password("adminpass123"),
            "role": UserRole.ADMIN.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        self.admin_token = create_access_token({"sub": admin_id})

        yield

        users_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_multiple_requests_succeed(self, client):
        """Test multiple sequential requests all succeed"""
        # Note: Actual rate limiting not implemented in basic server
        # This test verifies no accidental blocking
        for _ in range(10):
            response = client.get(
                "/api/users",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
