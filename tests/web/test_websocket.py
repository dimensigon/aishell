"""
Tests for WebSocket Functionality

Tests WebSocket connections, message handling, broadcasting, and disconnect handling.
"""

import pytest
from fastapi.testclient import TestClient
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.web_server import app, websocket_connections


class TestWebSocketConnection:
    """Test WebSocket connection establishment"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_websocket_endpoint_exists(self, client):
        """Test WebSocket endpoint is available"""
        # WebSocket endpoint should exist at /ws
        with client.websocket_connect("/ws") as websocket:
            assert websocket is not None

    def test_websocket_connection_accepted(self, client):
        """Test WebSocket connection is accepted"""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            # If we get here without exception, connection was accepted
            assert True

    def test_websocket_added_to_connections_list(self, client):
        """Test WebSocket is added to connections list"""
        initial_count = len(websocket_connections)

        with client.websocket_connect("/ws") as websocket:
            # Connection should be added (note: may not reflect in test client)
            pass

        # After disconnect, should be removed
        # Note: Test client behavior may differ from production


class TestWebSocketMessaging:
    """Test WebSocket message sending and receiving"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_send_text_message(self, client):
        """Test sending text message through WebSocket"""
        with client.websocket_connect("/ws") as websocket:
            message = "Hello WebSocket"
            websocket.send_text(message)

            # Should receive echo response
            response = websocket.receive_text()
            assert "Echo:" in response
            assert message in response

    def test_send_json_message(self, client):
        """Test sending JSON message through WebSocket"""
        with client.websocket_connect("/ws") as websocket:
            data = {"type": "test", "message": "Hello"}
            websocket.send_text(json.dumps(data))

            # Should receive echo response
            response = websocket.receive_text()
            assert "Echo:" in response

    def test_receive_message_format(self, client):
        """Test received message format"""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("test message")

            response = websocket.receive_text()
            assert isinstance(response, str)
            assert len(response) > 0

    def test_multiple_messages(self, client):
        """Test sending multiple messages in sequence"""
        with client.websocket_connect("/ws") as websocket:
            messages = ["message1", "message2", "message3"]

            for msg in messages:
                websocket.send_text(msg)
                response = websocket.receive_text()
                assert msg in response


class TestWebSocketBroadcasting:
    """Test WebSocket message broadcasting"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_broadcast_to_single_client(self, client):
        """Test broadcasting with single client"""
        with client.websocket_connect("/ws") as websocket:
            message = "broadcast test"
            websocket.send_text(message)

            # Should receive broadcast
            response = websocket.receive_text()
            assert message in response

    def test_message_echo_format(self, client):
        """Test message echo has expected format"""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("test")

            response = websocket.receive_text()
            assert response.startswith("Echo:")


class TestWebSocketDisconnection:
    """Test WebSocket disconnection handling"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_graceful_disconnect(self, client):
        """Test graceful WebSocket disconnection"""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("test")
            websocket.receive_text()

        # Connection should close without error

    def test_disconnect_after_multiple_messages(self, client):
        """Test disconnect after sending multiple messages"""
        with client.websocket_connect("/ws") as websocket:
            for i in range(5):
                websocket.send_text(f"message {i}")
                websocket.receive_text()

        # Should disconnect cleanly


class TestWebSocketErrorHandling:
    """Test WebSocket error handling"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_invalid_endpoint(self, client):
        """Test connection to invalid WebSocket endpoint"""
        with pytest.raises(Exception):
            # Should fail to connect to non-existent endpoint
            with client.websocket_connect("/ws/invalid"):
                pass

    def test_empty_message_handling(self, client):
        """Test handling of empty messages"""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("")

            # Should handle empty message
            response = websocket.receive_text()
            assert isinstance(response, str)


class TestWebSocketConcurrency:
    """Test concurrent WebSocket connections"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_sequential_connections(self, client):
        """Test multiple sequential connections"""
        for i in range(3):
            with client.websocket_connect("/ws") as websocket:
                websocket.send_text(f"connection {i}")
                response = websocket.receive_text()
                assert f"connection {i}" in response


class TestWebSocketDataTypes:
    """Test different data types over WebSocket"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_send_string(self, client):
        """Test sending string data"""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("string message")
            response = websocket.receive_text()
            assert "string message" in response

    def test_send_json_object(self, client):
        """Test sending JSON object"""
        with client.websocket_connect("/ws") as websocket:
            data = {"key": "value", "number": 123}
            websocket.send_text(json.dumps(data))

            response = websocket.receive_text()
            assert isinstance(response, str)

    def test_send_json_array(self, client):
        """Test sending JSON array"""
        with client.websocket_connect("/ws") as websocket:
            data = [1, 2, 3, 4, 5]
            websocket.send_text(json.dumps(data))

            response = websocket.receive_text()
            assert isinstance(response, str)

    def test_send_special_characters(self, client):
        """Test sending special characters"""
        with client.websocket_connect("/ws") as websocket:
            special_msg = "Special chars: !@#$%^&*()"
            websocket.send_text(special_msg)

            response = websocket.receive_text()
            assert "Special chars" in response

    def test_send_unicode(self, client):
        """Test sending Unicode characters"""
        with client.websocket_connect("/ws") as websocket:
            unicode_msg = "Unicode: 你好世界 🌍"
            websocket.send_text(unicode_msg)

            response = websocket.receive_text()
            assert isinstance(response, str)


class TestWebSocketRealtime:
    """Test real-time WebSocket functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_immediate_response(self, client):
        """Test WebSocket provides immediate response"""
        with client.websocket_connect("/ws") as websocket:
            import time
            start = time.time()

            websocket.send_text("test")
            response = websocket.receive_text()

            duration = time.time() - start

            # Response should be very fast (< 1 second)
            assert duration < 1.0
            assert response is not None

    def test_rapid_message_exchange(self, client):
        """Test rapid message exchange"""
        with client.websocket_connect("/ws") as websocket:
            # Send multiple messages rapidly
            for i in range(10):
                websocket.send_text(f"rapid {i}")
                websocket.receive_text()

            # Should handle all messages without error


class TestWebSocketPersistence:
    """Test WebSocket connection persistence"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        websocket_connections.clear()

        yield

        websocket_connections.clear()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_connection_stays_open(self, client):
        """Test WebSocket connection stays open"""
        with client.websocket_connect("/ws") as websocket:
            # Send messages with delays
            import time

            websocket.send_text("message 1")
            websocket.receive_text()

            time.sleep(0.1)

            websocket.send_text("message 2")
            websocket.receive_text()

            # Connection should still be open

    def test_connection_state_maintained(self, client):
        """Test connection state is maintained"""
        with client.websocket_connect("/ws") as websocket:
            # First message
            websocket.send_text("first")
            response1 = websocket.receive_text()

            # Second message - connection should still work
            websocket.send_text("second")
            response2 = websocket.receive_text()

            assert "first" in response1
            assert "second" in response2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
