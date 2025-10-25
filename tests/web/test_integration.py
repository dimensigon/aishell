"""
Integration Tests for Web Interface

End-to-end workflow tests covering complete user journeys and system interactions.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import (
    app, users_db, connections_db, queries_db, audit_logs_db,
    websocket_connections
)


class TestCompleteUserJourney:
    """Test complete user registration and workflow"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup clean environment"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()
        audit_logs_db.clear()
        websocket_connections.clear()

        yield

        users_db.clear()
        connections_db.clear()
        queries_db.clear()
        audit_logs_db.clear()
        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_complete_user_workflow(self, client):
        """Test complete workflow: register -> login -> create connection -> execute query"""

        # Step 1: Register new user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert register_response.status_code == 200
        assert register_response.json()["success"] is True

        # Step 2: Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["accessToken"]
        user_info = login_response.json()["data"]["user"]
        assert token is not None
        assert user_info["username"] == "testuser"

        # Step 3: Create database connection
        connection_response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "My PostgreSQL",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "mydb",
                "username": "dbuser",
                "password": "dbpass",
                "ssl": False
            }
        )
        assert connection_response.status_code == 200
        connection_id = connection_response.json()["data"]["id"]

        # Step 4: Test connection
        test_response = client.post(
            f"/api/connections/{connection_id}/test",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert test_response.status_code == 200
        assert test_response.json()["data"]["status"] == "connected"

        # Step 5: Execute query
        query_response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "connectionId": connection_id,
                "query": "SELECT * FROM users"
            }
        )
        assert query_response.status_code == 200
        result = query_response.json()["data"]
        assert "rows" in result
        assert "columns" in result

        # Step 6: Get query history
        history_response = client.get(
            "/api/queries/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert history_response.status_code == 200
        assert history_response.json()["data"]["total"] >= 1

        # Step 7: Get audit logs
        audit_response = client.get(
            "/api/audit",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert audit_response.status_code == 200
        # Should have logs for register, login, create connection, execute query
        assert audit_response.json()["data"]["total"] >= 4

        # Step 8: Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_response.status_code == 200


class TestConnectionManagementWorkflow:
    """Test complete connection management workflow"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user"""
        users_db.clear()
        connections_db.clear()
        audit_logs_db.clear()

        # Create user
        from api.web_server import hash_password, create_access_token
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

    def test_crud_connection_workflow(self, client):
        """Test Create, Read, Update, Delete connection workflow"""

        # Create connection
        create_response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test DB",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "username": "testuser",
                "password": "testpass",
                "ssl": False
            }
        )
        assert create_response.status_code == 200
        connection_id = create_response.json()["data"]["id"]

        # Read (list) connections
        list_response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert list_response.status_code == 200
        connections = list_response.json()["data"]
        assert len(connections) == 1
        assert connections[0]["id"] == connection_id

        # Update connection
        update_response = client.put(
            f"/api/connections/{connection_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Updated DB",
                "type": "mysql",
                "host": "newhost",
                "port": 3306,
                "database": "newdb",
                "username": "newuser",
                "password": "newpass",
                "ssl": True
            }
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["name"] == "Updated DB"
        assert update_response.json()["data"]["type"] == "mysql"

        # Verify update
        list_response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        updated_conn = list_response.json()["data"][0]
        assert updated_conn["name"] == "Updated DB"

        # Delete connection
        delete_response = client.delete(
            f"/api/connections/{connection_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert delete_response.status_code == 200

        # Verify deletion
        list_response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert len(list_response.json()["data"]) == 0


class TestMultiUserInteraction:
    """Test multiple users interacting with the system"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup multiple users"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()
        audit_logs_db.clear()

        yield

        users_db.clear()
        connections_db.clear()
        queries_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_multiple_users_workflow(self, client):
        """Test multiple users working independently"""

        # User 1: Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "password123"
            }
        )
        user1_login = client.post(
            "/api/auth/login",
            json={"username": "user1", "password": "password123"}
        )
        user1_token = user1_login.json()["data"]["accessToken"]

        # User 2: Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "password456"
            }
        )
        user2_login = client.post(
            "/api/auth/login",
            json={"username": "user2", "password": "password456"}
        )
        user2_token = user2_login.json()["data"]["accessToken"]

        # User 1 creates connection
        user1_conn = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "name": "User1 DB",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "db1",
                "username": "user1",
                "password": "pass1"
            }
        )

        # User 2 creates connection
        user2_conn = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {user2_token}"},
            json={
                "name": "User2 DB",
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database": "db2",
                "username": "user2",
                "password": "pass2"
            }
        )

        # Both should see all connections (in this simple implementation)
        connections = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert len(connections.json()["data"]) == 2


class TestErrorRecoveryWorkflow:
    """Test error handling and recovery workflows"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user"""
        users_db.clear()
        connections_db.clear()

        from api.web_server import hash_password, create_access_token
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

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_invalid_token_recovery(self, client):
        """Test handling of invalid token and recovery"""

        # Attempt with invalid token
        response = client.get(
            "/api/connections",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

        # Login to get valid token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        new_token = login_response.json()["data"]["accessToken"]

        # Retry with valid token
        response = client.get(
            "/api/connections",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert response.status_code == 200

    def test_nonexistent_resource_workflow(self, client):
        """Test handling of nonexistent resources"""

        # Try to update nonexistent connection
        response = client.put(
            "/api/connections/nonexistent",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test",
                "username": "test",
                "password": "test"
            }
        )
        assert response.status_code == 404

        # Create the connection
        create_response = client.post(
            "/api/connections",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "test",
                "username": "test",
                "password": "test"
            }
        )
        assert create_response.status_code == 200


class TestAuthenticationFlow:
    """Test complete authentication workflows"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup clean environment"""
        users_db.clear()
        audit_logs_db.clear()

        yield

        users_db.clear()
        audit_logs_db.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_full_authentication_lifecycle(self, client):
        """Test register -> login -> access -> logout -> login again"""

        # Register
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "lifecycleuser",
                "email": "lifecycle@example.com",
                "password": "password123"
            }
        )
        assert register_response.status_code == 200

        # First login
        login1_response = client.post(
            "/api/auth/login",
            json={"username": "lifecycleuser", "password": "password123"}
        )
        token1 = login1_response.json()["data"]["accessToken"]

        # Access protected resource
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response.status_code == 200

        # Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert logout_response.status_code == 200

        # Login again
        login2_response = client.post(
            "/api/auth/login",
            json={"username": "lifecycleuser", "password": "password123"}
        )
        token2 = login2_response.json()["data"]["accessToken"]
        assert token2 is not None

        # Access with new token
        me_response2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response2.status_code == 200


class TestConcurrentOperations:
    """Test concurrent operations and race conditions"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated user"""
        users_db.clear()
        connections_db.clear()
        queries_db.clear()

        from api.web_server import hash_password, create_access_token
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

        # Create a connection
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
            futures = [executor.submit(execute_query, i) for i in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert len(queries_db) == 10

    def test_concurrent_connection_operations(self, client):
        """Test concurrent connection operations"""
        import concurrent.futures

        def create_connection(i):
            return client.post(
                "/api/connections",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": f"Connection {i}",
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": f"db{i}",
                    "username": "user",
                    "password": "pass"
                }
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_connection, i) for i in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)


class TestWebSocketIntegration:
    """Test WebSocket integration with REST API"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup clean environment"""
        users_db.clear()
        websocket_connections.clear()

        yield

        users_db.clear()
        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_websocket_and_rest_integration(self, client):
        """Test WebSocket works alongside REST API"""

        # Register via REST
        client.post(
            "/api/auth/register",
            json={
                "username": "wsuser",
                "email": "ws@example.com",
                "password": "password123"
            }
        )

        # Health check via REST
        health = client.get("/api/health")
        assert health.status_code == 200

        # Connect WebSocket
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("test message")
            response = websocket.receive_text()
            assert "test message" in response

        # REST still works after WebSocket
        health = client.get("/api/health")
        assert health.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
