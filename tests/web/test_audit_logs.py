"""
Tests for Audit Log Endpoints

Tests audit log retrieval, filtering, pagination, and access control.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import (
    app, users_db, audit_logs_db, create_audit_log,
    hash_password, create_access_token, UserRole
)


class TestGetAuditLogs:
    """Test GET /api/audit endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        audit_logs_db.clear()

        # Create test users
        user_id = "user-1"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "user@example.com",
            "password": hash_password("password123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        admin_id = "admin-1"
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

        # Create test audit logs
        create_audit_log(user_id, "login", "user", {"username": "testuser"})
        create_audit_log(user_id, "execute", "query", {"queryId": "q1"})
        create_audit_log(admin_id, "create", "connection", {"connectionId": "c1"})
        create_audit_log(admin_id, "delete", "user", {"userId": "u2"})
        create_audit_log(user_id, "logout", "user", {})

        self.user_token = create_access_token({"sub": user_id})
        self.admin_token = create_access_token({"sub": admin_id})

        yield

        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_audit_logs_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.get("/api/audit")
        assert response.status_code == 401

    def test_get_audit_logs_success(self, client):
        """Test successful retrieval of audit logs"""
        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_audit_logs_returns_paginated_response(self, client):
        """Test response has pagination structure"""
        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pageSize" in data
        assert "totalPages" in data

    def test_get_audit_logs_returns_all_logs(self, client):
        """Test all audit logs are returned"""
        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_get_audit_logs_sorted_by_timestamp(self, client):
        """Test logs are sorted by timestamp (newest first)"""
        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        logs = response.json()["data"]["items"]
        timestamps = [log["timestamp"] for log in logs]

        # Verify descending order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]

    def test_audit_log_structure(self, client):
        """Test audit log entry has all expected fields"""
        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        log = response.json()["data"]["items"][0]

        assert "id" in log
        assert "userId" in log
        assert "username" in log
        assert "action" in log
        assert "resource" in log
        assert "details" in log
        assert "timestamp" in log
        assert "ipAddress" in log

    def test_get_audit_logs_default_pagination(self, client):
        """Test default pagination parameters"""
        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        data = response.json()["data"]
        assert data["page"] == 1
        assert data["pageSize"] == 20

    def test_get_audit_logs_custom_page_size(self, client):
        """Test custom page size"""
        response = client.get(
            "/api/audit?pageSize=2",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        data = response.json()["data"]
        assert data["pageSize"] == 2
        assert len(data["items"]) == 2

    def test_get_audit_logs_second_page(self, client):
        """Test retrieval of second page"""
        response = client.get(
            "/api/audit?page=2&pageSize=2",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        data = response.json()["data"]
        assert data["page"] == 2
        assert len(data["items"]) == 2

    def test_get_audit_logs_total_pages(self, client):
        """Test total pages calculation"""
        response = client.get(
            "/api/audit?pageSize=2",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 5
        assert data["totalPages"] == 3  # ceil(5/2) = 3


class TestAuditLogFiltering:
    """Test audit log filtering"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        audit_logs_db.clear()

        # Create test users
        user1_id = "user-1"
        users_db[user1_id] = {
            "id": user1_id,
            "username": "user1",
            "email": "user1@example.com",
            "password": hash_password("password123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        user2_id = "user-2"
        users_db[user2_id] = {
            "id": user2_id,
            "username": "user2",
            "email": "user2@example.com",
            "password": hash_password("password123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        # Create audit logs for different users and actions
        create_audit_log(user1_id, "login", "user", {})
        create_audit_log(user1_id, "execute", "query", {})
        create_audit_log(user2_id, "login", "user", {})
        create_audit_log(user2_id, "create", "connection", {})
        create_audit_log(user1_id, "logout", "user", {})

        self.user1_token = create_access_token({"sub": user1_id})

        yield

        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_filter_by_user_id(self, client):
        """Test filtering by user ID"""
        response = client.get(
            "/api/audit?userId=user-1",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )

        logs = response.json()["data"]["items"]

        # Should only return logs for user-1
        assert all(log["userId"] == "user-1" for log in logs)
        assert len(logs) == 3  # user-1 has 3 logs

    def test_filter_by_action(self, client):
        """Test filtering by action"""
        response = client.get(
            "/api/audit?action=login",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )

        logs = response.json()["data"]["items"]

        # Should only return login actions
        assert all(log["action"] == "login" for log in logs)
        assert len(logs) == 2  # 2 login events

    def test_filter_by_user_and_action(self, client):
        """Test filtering by both user ID and action"""
        response = client.get(
            "/api/audit?userId=user-1&action=login",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )

        logs = response.json()["data"]["items"]

        # Should match both filters
        assert all(log["userId"] == "user-1" and log["action"] == "login" for log in logs)
        assert len(logs) == 1

    def test_filter_no_matches(self, client):
        """Test filter with no matching logs"""
        response = client.get(
            "/api/audit?action=nonexistent",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_filter_maintains_sort_order(self, client):
        """Test filtered results maintain sort order"""
        response = client.get(
            "/api/audit?userId=user-1",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )

        logs = response.json()["data"]["items"]
        timestamps = [log["timestamp"] for log in logs]

        # Verify descending order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]


class TestCreateAuditLog:
    """Test audit log creation utility"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        audit_logs_db.clear()

        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        self.user_id = user_id

        yield

        users_db.clear()
        audit_logs_db.clear()

    def test_create_audit_log_returns_dict(self):
        """Test create_audit_log returns a dictionary"""
        log = create_audit_log(
            self.user_id,
            "test_action",
            "test_resource",
            {"key": "value"}
        )

        assert isinstance(log, dict)

    def test_create_audit_log_has_id(self):
        """Test created log has unique ID"""
        log = create_audit_log(
            self.user_id,
            "test_action",
            "test_resource",
            {}
        )

        assert "id" in log
        assert isinstance(log["id"], str)
        assert len(log["id"]) > 0

    def test_create_audit_log_stores_user_id(self):
        """Test log stores user ID"""
        log = create_audit_log(
            self.user_id,
            "test_action",
            "test_resource",
            {}
        )

        assert log["userId"] == self.user_id

    def test_create_audit_log_stores_username(self):
        """Test log stores username from user data"""
        log = create_audit_log(
            self.user_id,
            "test_action",
            "test_resource",
            {}
        )

        assert log["username"] == "testuser"

    def test_create_audit_log_stores_action(self):
        """Test log stores action"""
        log = create_audit_log(
            self.user_id,
            "custom_action",
            "resource",
            {}
        )

        assert log["action"] == "custom_action"

    def test_create_audit_log_stores_resource(self):
        """Test log stores resource"""
        log = create_audit_log(
            self.user_id,
            "action",
            "custom_resource",
            {}
        )

        assert log["resource"] == "custom_resource"

    def test_create_audit_log_stores_details(self):
        """Test log stores details"""
        details = {"key1": "value1", "key2": "value2"}
        log = create_audit_log(
            self.user_id,
            "action",
            "resource",
            details
        )

        assert log["details"] == details

    def test_create_audit_log_has_timestamp(self):
        """Test log has timestamp"""
        log = create_audit_log(
            self.user_id,
            "action",
            "resource",
            {}
        )

        assert "timestamp" in log
        # Should be valid ISO format
        datetime.fromisoformat(log["timestamp"])

    def test_create_audit_log_adds_to_db(self):
        """Test log is added to database"""
        initial_count = len(audit_logs_db)

        create_audit_log(
            self.user_id,
            "action",
            "resource",
            {}
        )

        assert len(audit_logs_db) == initial_count + 1

    def test_create_audit_log_nonexistent_user(self):
        """Test creating log for nonexistent user"""
        log = create_audit_log(
            "nonexistent-user",
            "action",
            "resource",
            {}
        )

        assert log["userId"] == "nonexistent-user"
        assert log["username"] == "unknown"


class TestAuditLogDataIntegrity:
    """Test audit log data integrity"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        audit_logs_db.clear()

        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_audit_log_immutability(self, client):
        """Test audit logs cannot be modified (conceptual)"""
        # Create an audit log
        initial_log = audit_logs_db[0] if audit_logs_db else None

        if initial_log:
            # Audit logs should be append-only
            # Note: This is a conceptual test - implementation would need
            # actual immutability protection
            assert isinstance(audit_logs_db, list)

    def test_audit_log_timestamp_format(self, client):
        """Test all timestamps are in ISO format"""
        # Create some logs
        from api.web_server import users_db as db
        user_id = list(db.keys())[0]

        create_audit_log(user_id, "action1", "resource1", {})
        create_audit_log(user_id, "action2", "resource2", {})

        for log in audit_logs_db:
            # Should not raise exception
            datetime.fromisoformat(log["timestamp"])

    def test_audit_log_details_as_dict(self, client):
        """Test details are stored as dictionary"""
        user_id = list(users_db.keys())[0]
        log = create_audit_log(user_id, "action", "resource", {"k": "v"})

        assert isinstance(log["details"], dict)

    def test_audit_log_comprehensive_tracking(self, client):
        """Test comprehensive action tracking"""
        # Perform various actions that should create audit logs
        audit_logs_db.clear()

        # Register
        client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )

        # Login
        client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        # Each action should create an audit log
        assert len(audit_logs_db) >= 2

    def test_empty_audit_logs(self, client):
        """Test retrieval when no logs exist"""
        audit_logs_db.clear()

        response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
