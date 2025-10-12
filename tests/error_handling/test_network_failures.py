"""
Network Failure Tests

Tests network error scenarios including connection failures, timeouts,
retries, and graceful degradation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import socket
from requests.exceptions import (
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException
)


class TestNetworkConnectionFailures:
    """Test network connection failure scenarios"""

    def test_connection_refused(self):
        """Test connection refused error"""
        with pytest.raises(ConnectionError):
            import requests
            # Try to connect to closed port
            requests.get("http://localhost:9999", timeout=0.1)

    def test_dns_resolution_failure(self):
        """Test DNS resolution failure"""
        import requests

        with pytest.raises((ConnectionError, requests.exceptions.ConnectionError)):
            requests.get("http://this-domain-definitely-does-not-exist-12345.com", timeout=1)

    def test_network_unreachable(self):
        """Test network unreachable error"""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = OSError("Network unreachable")

            with pytest.raises(OSError, match="Network unreachable"):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(("192.0.2.1", 80))

    def test_connection_timeout(self):
        """Test connection timeout"""
        import requests

        with pytest.raises((Timeout, requests.exceptions.Timeout, requests.exceptions.ConnectTimeout)):
            # Try to connect to non-routable address with short timeout
            requests.get("http://10.255.255.1", timeout=0.001)

    def test_read_timeout(self):
        """Test read timeout after connection"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Timeout("Read timeout")

            import requests
            with pytest.raises(Timeout):
                requests.get("http://example.com", timeout=0.1)


class TestHTTPErrors:
    """Test HTTP error responses"""

    @pytest.mark.parametrize("status_code,error_msg", [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout"),
    ])
    def test_http_error_codes(self, status_code, error_msg):
        """Test various HTTP error status codes"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.raise_for_status.side_effect = HTTPError(error_msg)
            mock_get.return_value = mock_response

            import requests
            with pytest.raises(HTTPError):
                response = requests.get("http://example.com")
                response.raise_for_status()

    def test_rate_limiting_429(self):
        """Test rate limiting (429) response"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_response.raise_for_status.side_effect = HTTPError("Too Many Requests")
            mock_get.return_value = mock_response

            import requests
            with pytest.raises(HTTPError):
                response = requests.get("http://api.example.com")
                response.raise_for_status()


class TestNetworkRetryLogic:
    """Test retry logic for network failures"""

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test retry mechanism on connection errors"""
        attempts = []

        async def flaky_connection():
            attempts.append(len(attempts))
            if len(attempts) < 3:
                raise ConnectionError("Connection failed")
            return "success"

        # Implement retry logic
        max_retries = 5
        for attempt in range(max_retries):
            try:
                result = await flaky_connection()
                break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.1)

        assert len(attempts) == 3
        assert result == "success"

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff on retries"""
        import time

        attempts = []
        times = []

        async def failing_request():
            attempts.append(len(attempts))
            times.append(time.time())
            if len(attempts) < 4:
                raise ConnectionError("Failed")
            return "success"

        # Exponential backoff
        max_retries = 5
        base_delay = 0.1

        for attempt in range(max_retries):
            try:
                result = await failing_request()
                break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        # Check backoff delays increased
        assert len(times) == 4
        for i in range(1, len(times)):
            gap = times[i] - times[i-1]
            expected_min = base_delay * (2 ** (i-1))
            assert gap >= expected_min * 0.9  # Allow some variance

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test failure after max retries"""
        attempts = []

        async def always_failing():
            attempts.append(len(attempts))
            raise ConnectionError("Always fails")

        max_retries = 3

        with pytest.raises(ConnectionError):
            for attempt in range(max_retries):
                try:
                    await always_failing()
                except ConnectionError:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(0.01)

        assert len(attempts) == max_retries

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker on repeated failures"""
        failures = []
        circuit_open = False

        async def protected_call():
            nonlocal circuit_open

            if circuit_open:
                raise Exception("Circuit breaker open")

            failures.append(len(failures))
            if len(failures) >= 3:
                circuit_open = True

            raise ConnectionError("Service down")

        # Make calls until circuit opens
        for i in range(5):
            try:
                await protected_call()
            except Exception:
                pass

        assert circuit_open
        assert len(failures) == 3


class TestNetworkPartitioning:
    """Test network partition scenarios"""

    @pytest.mark.asyncio
    async def test_partial_network_failure(self):
        """Test partial network failure (some nodes reachable)"""
        nodes = {
            "node1": True,  # reachable
            "node2": False,  # unreachable
            "node3": True,   # reachable
        }

        async def call_node(node_name):
            if not nodes[node_name]:
                raise ConnectionError(f"{node_name} unreachable")
            return f"{node_name}_response"

        # Try all nodes
        results = []
        errors = []

        for node in nodes:
            try:
                result = await call_node(node)
                results.append(result)
            except ConnectionError as e:
                errors.append(str(e))

        assert len(results) == 2  # 2 successful
        assert len(errors) == 1   # 1 failed

    @pytest.mark.asyncio
    async def test_split_brain_scenario(self):
        """Test split-brain network partition"""
        partition_a = {"node1", "node2"}
        partition_b = {"node3", "node4"}

        async def can_communicate(node1, node2):
            """Check if two nodes can communicate"""
            in_partition_a = node1 in partition_a and node2 in partition_a
            in_partition_b = node1 in partition_b and node2 in partition_b

            if in_partition_a or in_partition_b:
                return True
            raise ConnectionError(f"Network partition between {node1} and {node2}")

        # Test communication
        assert await can_communicate("node1", "node2")
        assert await can_communicate("node3", "node4")

        with pytest.raises(ConnectionError):
            await can_communicate("node1", "node3")


class TestGracefulDegradation:
    """Test graceful degradation on network failures"""

    @pytest.mark.asyncio
    async def test_fallback_to_cache(self):
        """Test falling back to cache on network failure"""
        cache = {"key1": "cached_value"}

        async def fetch_with_fallback(key):
            try:
                # Simulate network call
                raise ConnectionError("Network down")
            except ConnectionError:
                # Fallback to cache
                if key in cache:
                    return cache[key]
                raise

        result = await fetch_with_fallback("key1")
        assert result == "cached_value"

        with pytest.raises(ConnectionError):
            await fetch_with_fallback("key2")

    @pytest.mark.asyncio
    async def test_degraded_mode_operation(self):
        """Test degraded mode when network fails"""
        from src.core.degraded_mode import DegradedModeManager

        manager = DegradedModeManager(cache_enabled=True, readonly=True)

        result = await manager.execute_in_degraded_mode(
            "SELECT * FROM users",
            enable_cache=True,
            read_only=True
        )

        assert result['mode'] == 'degraded'
        assert result['cache_enabled'] is True
        assert result['readonly'] is True

    @pytest.mark.asyncio
    async def test_timeout_with_partial_results(self):
        """Test returning partial results on timeout"""
        async def fetch_data_from_sources():
            results = []

            sources = [
                ("fast", 0.1, "data1"),
                ("slow", 5.0, "data2"),
                ("medium", 0.3, "data3"),
            ]

            tasks = []
            for name, delay, data in sources:
                async def fetch(d=delay, v=data):
                    await asyncio.sleep(d)
                    return v
                tasks.append(asyncio.create_task(fetch()))

            # Wait with timeout
            done, pending = await asyncio.wait(
                tasks,
                timeout=0.5,
                return_when=asyncio.ALL_COMPLETED
            )

            # Cancel pending
            for task in pending:
                task.cancel()

            # Get completed results
            for task in done:
                try:
                    results.append(await task)
                except Exception:
                    pass

            return results

        results = await fetch_data_from_sources()

        # Should have at least some results
        assert len(results) >= 1
        assert "data1" in results


class TestSocketErrors:
    """Test low-level socket errors"""

    def test_socket_connection_refused(self):
        """Test socket connection refused"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)

        with pytest.raises(ConnectionRefusedError):
            sock.connect(("localhost", 9999))

        sock.close()

    def test_socket_timeout(self):
        """Test socket timeout"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.001)

        with pytest.raises((socket.timeout, OSError)):
            # Try to connect to filtered port
            sock.connect(("192.0.2.1", 80))

        sock.close()

    def test_socket_broken_pipe(self):
        """Test broken pipe error"""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.send.side_effect = BrokenPipeError("Broken pipe")
            mock_socket_class.return_value = mock_socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            with pytest.raises(BrokenPipeError):
                sock.send(b"data")

    def test_connection_reset_by_peer(self):
        """Test connection reset by peer"""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.recv.side_effect = ConnectionResetError("Connection reset")
            mock_socket_class.return_value = mock_socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            with pytest.raises(ConnectionResetError):
                sock.recv(1024)


class TestAsyncNetworkErrors:
    """Test async network error handling"""

    @pytest.mark.asyncio
    async def test_aiohttp_connection_error(self):
        """Test aiohttp connection error handling"""
        try:
            import aiohttp

            with pytest.raises((aiohttp.ClientError, Exception)):
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "http://localhost:99999",
                        timeout=aiohttp.ClientTimeout(total=0.1)
                    ) as response:
                        pass
        except ImportError:
            pytest.skip("aiohttp not installed")

    @pytest.mark.asyncio
    async def test_concurrent_network_failures(self):
        """Test multiple concurrent network failures"""
        async def failing_request(url):
            raise ConnectionError(f"Failed to connect to {url}")

        urls = [f"http://host{i}.example.com" for i in range(10)]
        tasks = [failing_request(url) for url in urls]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should be ConnectionErrors
        assert all(isinstance(r, ConnectionError) for r in results)

    @pytest.mark.asyncio
    async def test_network_failure_during_streaming(self):
        """Test network failure during streaming response"""
        async def streaming_response():
            for i in range(10):
                if i == 5:
                    raise ConnectionError("Connection lost during streaming")
                yield f"chunk_{i}"
                await asyncio.sleep(0.01)

        chunks = []
        with pytest.raises(ConnectionError):
            async for chunk in streaming_response():
                chunks.append(chunk)

        # Should have received some chunks before failure
        assert len(chunks) == 5
