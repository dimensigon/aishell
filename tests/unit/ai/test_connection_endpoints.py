"""
Tests for Database Connection Endpoints

Tests CRUD operations for database connections, connection testing, and status management.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import (
    app, users_db, connections_db, audit_logs_db,
    hash_password, create_access_token, ConnectionStatus, DatabaseType
)


class TestGetConnections:
    """Test GET /api/connections endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

        # Create test user
        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        # Create test connections
        connections_db["conn1"] = {
            "id": "conn1",
            "name": "Test PostgreSQL",
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "ssl": False,
            "status": "connected",
            "createdAt": datetime.utcnow().isoformat(),
            "lastUsed": None
        }

        connections_db["conn2"] = {
            "id": "conn2",
            "name": "Test MySQL",
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database": "testdb",
            "username": "root",
            "ssl": True,
            "status": "disconnected",
            "createdAt": datetime.utcnow().isoformat(),
            "lastUsed": None
        }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_get_connections_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.get("/api/connections")
        assert response.status_code == 401

    def test_get_connections_success(self, client):
        """Test successful retrieval of connections"""
        response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_get_connections_returns_all_fields(self, client):
        """Test response includes all connection fields"""
        response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        connections = response.json()["data"]
        conn = connections[0]

        assert "id" in conn
        assert "name" in conn
        assert "type" in conn
        assert "host" in conn
        assert "port" in conn
        assert "database" in conn
        assert "username" in conn
        assert "ssl" in conn
        assert "status" in conn
        assert "createdAt" in conn

    def test_get_connections_empty_list(self, client):
        """Test returns empty list when no connections"""
        connections_db.clear()

        response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()
        assert data["success"] is True
        assert data["data"] == []


class TestCreateConnection:
    """Test POST /api/connections endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_create_connection_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.post("/api/connections", json={})
        assert response.status_code == 401

    def test_create_connection_success(self, client):
        """Test successful connection creation"""
        response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "New PostgreSQL",
                "type": "postgresql",
                "host": "db.example.com",
                "port": 5432,
                "database": "mydb",
                "username": "dbuser",
                "password": "dbpass",
                "ssl": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New PostgreSQL"
        assert data["data"]["type"] == "postgresql"
        assert data["data"]["status"] == "disconnected"

    def test_create_connection_adds_to_db(self, client):
        """Test connection is added to database"""
        assert len(connections_db) == 0

        client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "New Connection",
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database": "testdb",
                "username": "root",
                "password": "rootpass",
                "ssl": False
            }
        )

        assert len(connections_db) == 1

    def test_create_connection_generates_id(self, client):
        """Test connection ID is generated"""
        response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test Connection",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "testuser",
                "password": "testpass",
                "ssl": False
            }
        )

        connection_id = response.json()["data"]["id"]
        assert isinstance(connection_id, str)
        assert len(connection_id) > 0
        assert connection_id in connections_db

    def test_create_connection_creates_audit_log(self, client):
        """Test audit log is created"""
        client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test Connection",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "testuser",
                "password": "testpass",
                "ssl": False
            }
        )

        assert len(audit_logs_db) > 0
        log = audit_logs_db[0]
        assert log["action"] == "create"
        assert log["resource"] == "connection"

    def test_create_connection_invalid_type(self, client):
        """Test invalid database type returns 422"""
        response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test",
                "type": "invalid_db_type",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "testuser",
                "password": "testpass"
            }
        )

        assert response.status_code == 422

    def test_create_connection_missing_fields(self, client):
        """Test missing required fields returns 422"""
        response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Incomplete Connection"
            }
        )

        assert response.status_code == 422


class TestUpdateConnection:
    """Test PUT /api/connections/{connection_id} endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        connections_db["conn1"] = {
            "id": "conn1",
            "name": "Original Name",
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "ssl": False,
            "status": "connected",
            "createdAt": datetime.utcnow().isoformat(),
            "lastUsed": None
        }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_update_connection_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.put("/api/connections/conn1", json={})
        assert response.status_code == 401

    def test_update_connection_success(self, client):
        """Test successful connection update"""
        response = client.put(
            "/api/connections/conn1",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Updated Name",
                "type": "postgresql",
                "host": "newhost.example.com",
                "port": 5433,
                "database": "newdb",
                "username": "newuser",
                "password": "newpass",
                "ssl": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["host"] == "newhost.example.com"
        assert data["data"]["ssl"] is True

    def test_update_connection_modifies_db(self, client):
        """Test connection is updated in database"""
        client.put(
            "/api/connections/conn1",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Modified Connection",
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database": "testdb",
                "username": "root",
                "password": "rootpass",
                "ssl": False
            }
        )

        assert connections_db["conn1"]["name"] == "Modified Connection"
        assert connections_db["conn1"]["type"] == "mysql"

    def test_update_nonexistent_connection(self, client):
        """Test updating nonexistent connection returns 404"""
        response = client.put(
            "/api/connections/nonexistent",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "testuser",
                "password": "testpass"
            }
        )

        assert response.status_code == 404

    def test_update_connection_creates_audit_log(self, client):
        """Test audit log is created"""
        client.put(
            "/api/connections/conn1",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Updated",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "testuser",
                "password": "testpass"
            }
        )

        assert len(audit_logs_db) > 0
        log = audit_logs_db[0]
        assert log["action"] == "update"
        assert log["resource"] == "connection"


class TestDeleteConnection:
    """Test DELETE /api/connections/{connection_id} endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        connections_db["conn1"] = {
            "id": "conn1",
            "name": "Test Connection",
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "ssl": False,
            "status": "connected",
            "createdAt": datetime.utcnow().isoformat(),
            "lastUsed": None
        }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_delete_connection_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.delete("/api/connections/conn1")
        assert response.status_code == 401

    def test_delete_connection_success(self, client):
        """Test successful connection deletion"""
        response = client.delete(
            "/api/connections/conn1",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Connection deleted"

    def test_delete_connection_removes_from_db(self, client):
        """Test connection is removed from database"""
        assert "conn1" in connections_db

        client.delete(
            "/api/connections/conn1",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert "conn1" not in connections_db

    def test_delete_nonexistent_connection(self, client):
        """Test deleting nonexistent connection returns 404"""
        response = client.delete(
            "/api/connections/nonexistent",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 404

    def test_delete_connection_creates_audit_log(self, client):
        """Test audit log is created"""
        client.delete(
            "/api/connections/conn1",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert len(audit_logs_db) > 0
        log = audit_logs_db[0]
        assert log["action"] == "delete"
        assert log["resource"] == "connection"


class TestConnectionTest:
    """Test POST /api/connections/{connection_id}/test endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

        user_id = "test-user"
        users_db[user_id] = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "password": hash_password("password123"),
            "role": "user",
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }

        connections_db["conn1"] = {
            "id": "conn1",
            "name": "Test Connection",
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "ssl": False,
            "status": "disconnected",
            "createdAt": datetime.utcnow().isoformat(),
            "lastUsed": None
        }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_test_connection_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.post("/api/connections/conn1/test")
        assert response.status_code == 401

    def test_test_connection_success(self, client):
        """Test successful connection test"""
        response = client.post(
            "/api/connections/conn1/test",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "connected"

    def test_test_connection_updates_status(self, client):
        """Test connection status is updated"""
        assert connections_db["conn1"]["status"] == "disconnected"

        client.post(
            "/api/connections/conn1/test",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert connections_db["conn1"]["status"] == "connected"

    def test_test_nonexistent_connection(self, client):
        """Test testing nonexistent connection returns 404"""
        response = client.post(
            "/api/connections/nonexistent/test",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
