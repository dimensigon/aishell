"""
Tests for Query Execution Endpoints

Tests query execution, query history, pagination, and query result formatting.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import (
    app, users_db, connections_db, queries_db, audit_logs_db,
    hash_password, create_access_token
)


class TestExecuteQuery:
    """Test POST /api/queries/execute endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()
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

        # Create test connection
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

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        queries_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_execute_query_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.post("/api/queries/execute", json={})
        assert response.status_code == 401

    def test_execute_query_success(self, client):
        """Test successful query execution"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_execute_query_returns_result_structure(self, client):
        """Test query result has correct structure"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT id, name FROM users"
            }
        )

        result = response.json()["data"]
        assert "id" in result
        assert "query" in result
        assert "columns" in result
        assert "rows" in result
        assert "rowCount" in result
        assert "executionTime" in result
        assert "timestamp" in result

    def test_execute_query_stores_in_db(self, client):
        """Test query result is stored in database"""
        assert len(queries_db) == 0

        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        query_id = response.json()["data"]["id"]
        assert len(queries_db) == 1
        assert query_id in queries_db

    def test_execute_query_updates_connection_last_used(self, client):
        """Test connection lastUsed is updated"""
        assert connections_db["conn1"]["lastUsed"] is None

        client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        assert connections_db["conn1"]["lastUsed"] is not None

    def test_execute_query_creates_audit_log(self, client):
        """Test audit log is created"""
        client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        assert len(audit_logs_db) > 0
        log = audit_logs_db[0]
        assert log["action"] == "execute"
        assert log["resource"] == "query"

    def test_execute_query_nonexistent_connection(self, client):
        """Test query with nonexistent connection returns 404"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "nonexistent",
                "query": "SELECT * FROM users"
            }
        )

        assert response.status_code == 404
        assert "Connection not found" in response.json()["detail"]

    def test_execute_query_with_parameters(self, client):
        """Test query execution with parameters"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users WHERE id = :id",
                "parameters": {"id": 1}
            }
        )

        assert response.status_code == 200

    def test_execute_query_missing_connection_id(self, client):
        """Test query without connectionId returns 422"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "query": "SELECT * FROM users"
            }
        )

        assert response.status_code == 422

    def test_execute_query_missing_query(self, client):
        """Test execution without query returns 422"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1"
            }
        )

        assert response.status_code == 422


class TestQueryHistory:
    """Test GET /api/queries/history endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()
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

        # Create test queries
        for i in range(5):
            query_id = f"query{i}"
            queries_db[query_id] = {
                "id": query_id,
                "query": f"SELECT * FROM table{i}",
                "columns": ["id", "name"],
                "rows": [{"id": 1, "name": "test"}],
                "rowCount": 1,
                "executionTime": 50 + i,
                "timestamp": datetime.utcnow().isoformat()
            }

        self.token = create_access_token({"sub": user_id})

        yield

        users_db.clear()
        connections_db.clear()
        queries_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_query_history_requires_auth(self, client):
        """Test endpoint requires authentication"""
        response = client.get("/api/queries/history")
        assert response.status_code == 401

    def test_query_history_success(self, client):
        """Test successful retrieval of query history"""
        response = client.get(
            "/api/queries/history",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_query_history_returns_paginated_response(self, client):
        """Test response has pagination structure"""
        response = client.get(
            "/api/queries/history",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pageSize" in data
        assert "totalPages" in data

    def test_query_history_default_pagination(self, client):
        """Test default pagination parameters"""
        response = client.get(
            "/api/queries/history",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert data["page"] == 1
        assert data["pageSize"] == 20
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_query_history_custom_page_size(self, client):
        """Test custom page size"""
        response = client.get(
            "/api/queries/history?pageSize=2",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert data["pageSize"] == 2
        assert len(data["items"]) == 2

    def test_query_history_second_page(self, client):
        """Test retrieval of second page"""
        response = client.get(
            "/api/queries/history?page=2&pageSize=2",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert data["page"] == 2
        assert len(data["items"]) == 2

    def test_query_history_total_pages_calculation(self, client):
        """Test total pages is calculated correctly"""
        response = client.get(
            "/api/queries/history?pageSize=2",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 5
        assert data["totalPages"] == 3  # ceil(5/2) = 3

    def test_query_history_empty_list(self, client):
        """Test empty query history"""
        queries_db.clear()

        response = client.get(
            "/api/queries/history",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        data = response.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_query_history_filter_by_connection(self, client):
        """Test filtering by connection ID (parameter exists)"""
        response = client.get(
            "/api/queries/history?connectionId=conn1",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        assert response.status_code == 200
        # Note: Actual filtering logic not implemented in the endpoint


class TestQueryResultFormat:
    """Test query result data format"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()

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
            "name": "Test DB",
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
        queries_db.clear()

    def test_query_result_has_columns(self, client):
        """Test query result includes column names"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        result = response.json()["data"]
        assert isinstance(result["columns"], list)
        assert len(result["columns"]) > 0
        # Default mock returns these columns
        assert "id" in result["columns"]
        assert "name" in result["columns"]
        assert "email" in result["columns"]

    def test_query_result_has_rows(self, client):
        """Test query result includes row data"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        result = response.json()["data"]
        assert isinstance(result["rows"], list)
        assert len(result["rows"]) > 0

    def test_query_result_row_format(self, client):
        """Test each row is a dictionary"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        result = response.json()["data"]
        for row in result["rows"]:
            assert isinstance(row, dict)

    def test_query_result_row_count(self, client):
        """Test rowCount matches actual rows"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        result = response.json()["data"]
        assert result["rowCount"] == len(result["rows"])

    def test_query_result_has_execution_time(self, client):
        """Test result includes execution time"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        result = response.json()["data"]
        assert isinstance(result["executionTime"], int)
        assert result["executionTime"] > 0

    def test_query_result_has_timestamp(self, client):
        """Test result includes timestamp"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "connectionId": "conn1",
                "query": "SELECT * FROM users"
            }
        )

        result = response.json()["data"]
        assert "timestamp" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["timestamp"])


class TestConcurrentQueries:
    """Test concurrent query execution"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()

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
            "name": "Test DB",
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
        queries_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_concurrent_query_execution(self, client):
        """Test multiple concurrent queries"""
        import concurrent.futures

        def execute_query(i):
            return client.post(
                "/api/queries/execute",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "connectionId": "conn1",
                    "query": f"SELECT * FROM table{i}"
                }
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_query, i) for i in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["success"] for r in responses)

        # All should be stored
        assert len(queries_db) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
