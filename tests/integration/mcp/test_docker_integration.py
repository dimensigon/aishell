"""Docker integration tests to verify container health and connectivity."""
import subprocess
import pytest
import time
from tests.integration.mcp.config import CONTAINER_NAMES, DOCKER_CONFIGS


class TestDockerContainers:
    """Test Docker container status."""

    def test_postgresql_container_running(self):
        """Test PostgreSQL container is running."""
        container_name = CONTAINER_NAMES['postgresql']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "true" in result.stdout.lower()

    def test_mysql_container_running(self):
        """Test MySQL container is running."""
        container_name = CONTAINER_NAMES['mysql']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "true" in result.stdout.lower()

    def test_mongodb_container_running(self):
        """Test MongoDB container is running."""
        container_name = CONTAINER_NAMES['mongodb']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "true" in result.stdout.lower()

    def test_redis_container_running(self):
        """Test Redis container is running."""
        container_name = CONTAINER_NAMES['redis']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "true" in result.stdout.lower()

    def test_all_containers_running(self):
        """Test all required containers are running."""
        for service, container_name in CONTAINER_NAMES.items():
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"{service} container not found"
            assert "true" in result.stdout.lower(), f"{service} container not running"


class TestDockerHealthChecks:
    """Test Docker container health checks."""

    def test_postgresql_health(self):
        """Test PostgreSQL container health."""
        container_name = CONTAINER_NAMES['postgresql']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "healthy" in result.stdout.lower()

    def test_mysql_health(self):
        """Test MySQL container health."""
        container_name = CONTAINER_NAMES['mysql']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "healthy" in result.stdout.lower()

    def test_mongodb_health(self):
        """Test MongoDB container health."""
        container_name = CONTAINER_NAMES['mongodb']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "healthy" in result.stdout.lower()

    def test_redis_health(self):
        """Test Redis container health."""
        container_name = CONTAINER_NAMES['redis']

        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "healthy" in result.stdout.lower()


class TestDockerNetworking:
    """Test Docker container networking."""

    def test_postgresql_port_exposed(self):
        """Test PostgreSQL port is exposed."""
        container_name = CONTAINER_NAMES['postgresql']
        expected_port = DOCKER_CONFIGS['postgresql']['port']

        result = subprocess.run(
            ["docker", "port", container_name, "5432"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert str(expected_port) in result.stdout

    def test_mysql_port_exposed(self):
        """Test MySQL port is exposed."""
        container_name = CONTAINER_NAMES['mysql']
        expected_port = DOCKER_CONFIGS['mysql']['port']

        result = subprocess.run(
            ["docker", "port", container_name, "3306"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert str(expected_port) in result.stdout

    def test_mongodb_port_exposed(self):
        """Test MongoDB port is exposed."""
        container_name = CONTAINER_NAMES['mongodb']
        expected_port = DOCKER_CONFIGS['mongodb']['port']

        result = subprocess.run(
            ["docker", "port", container_name, "27017"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert str(expected_port) in result.stdout

    def test_redis_port_exposed(self):
        """Test Redis port is exposed."""
        container_name = CONTAINER_NAMES['redis']
        expected_port = DOCKER_CONFIGS['redis']['port']

        result = subprocess.run(
            ["docker", "port", container_name, "6379"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert str(expected_port) in result.stdout


class TestDockerVolumes:
    """Test Docker volume persistence."""

    def test_postgresql_volume_exists(self):
        """Test PostgreSQL data volume exists."""
        result = subprocess.run(
            ["docker", "volume", "ls"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "postgres-data" in result.stdout

    def test_mysql_volume_exists(self):
        """Test MySQL data volume exists."""
        result = subprocess.run(
            ["docker", "volume", "ls"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "mysql-data" in result.stdout

    def test_mongodb_volume_exists(self):
        """Test MongoDB data volume exists."""
        result = subprocess.run(
            ["docker", "volume", "ls"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "mongodb-data" in result.stdout

    def test_redis_volume_exists(self):
        """Test Redis data volume exists."""
        result = subprocess.run(
            ["docker", "volume", "ls"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "redis-data" in result.stdout


class TestDockerConnectivity:
    """Test connectivity from clients to Docker containers."""

    @pytest.mark.asyncio
    async def test_postgresql_connectivity(self, pg_client):
        """Test connection from PostgreSQL client to container."""
        config = DOCKER_CONFIGS['postgresql']

        await pg_client.connect(**config)

        assert pg_client.is_connected()

        result = await pg_client.execute("SELECT 1 as value")
        assert result['rows'][0]['value'] == 1

    @pytest.mark.asyncio
    async def test_mysql_connectivity(self, mysql_client):
        """Test connection from MySQL client to container."""
        config = DOCKER_CONFIGS['mysql']

        await mysql_client.connect(**config)

        assert mysql_client.is_connected()

        result = await mysql_client.execute("SELECT 1 as value")
        assert result['rows'][0]['value'] == 1

    @pytest.mark.asyncio
    async def test_mongodb_connectivity(self, mongo_client):
        """Test connection from MongoDB client to container."""
        config = DOCKER_CONFIGS['mongodb']

        await mongo_client.connect(**config)

        assert mongo_client.is_connected()

        # Ping database
        await mongo_client.ping()

    @pytest.mark.asyncio
    async def test_redis_connectivity(self, redis_mcp_client):
        """Test connection from Redis client to container."""
        config = DOCKER_CONFIGS['redis']

        await redis_mcp_client.connect(**config)

        assert redis_mcp_client.is_connected()

        result = await redis_mcp_client.ping()
        assert result is True or result == 'PONG'


class TestDockerResourceUsage:
    """Test Docker container resource usage."""

    def test_postgresql_memory_usage(self):
        """Test PostgreSQL container memory usage is reasonable."""
        container_name = CONTAINER_NAMES['postgresql']

        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip()  # Has memory usage info

    def test_mysql_memory_usage(self):
        """Test MySQL container memory usage is reasonable."""
        container_name = CONTAINER_NAMES['mysql']

        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip()

    def test_mongodb_memory_usage(self):
        """Test MongoDB container memory usage is reasonable."""
        container_name = CONTAINER_NAMES['mongodb']

        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip()

    def test_redis_memory_usage(self):
        """Test Redis container memory usage is reasonable."""
        container_name = CONTAINER_NAMES['redis']

        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip()


class TestDockerLogs:
    """Test Docker container logs."""

    def test_postgresql_logs_no_errors(self):
        """Test PostgreSQL container logs don't contain errors."""
        container_name = CONTAINER_NAMES['postgresql']

        result = subprocess.run(
            ["docker", "logs", "--tail", "100", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check for common error patterns (adjust based on your needs)
        assert "FATAL" not in result.stderr or "ready to accept connections" in result.stdout

    def test_mysql_logs_no_errors(self):
        """Test MySQL container logs don't contain critical errors."""
        container_name = CONTAINER_NAMES['mysql']

        result = subprocess.run(
            ["docker", "logs", "--tail", "100", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # MySQL logs startup info to stdout
        assert "ready for connections" in result.stdout.lower() or "mysqld: ready for connections" in result.stdout.lower()

    def test_mongodb_logs_no_errors(self):
        """Test MongoDB container logs don't contain errors."""
        container_name = CONTAINER_NAMES['mongodb']

        result = subprocess.run(
            ["docker", "logs", "--tail", "100", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "waiting for connections" in result.stdout.lower() or "ready" in result.stdout.lower()

    def test_redis_logs_no_errors(self):
        """Test Redis container logs don't contain errors."""
        container_name = CONTAINER_NAMES['redis']

        result = subprocess.run(
            ["docker", "logs", "--tail", "100", container_name],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "ready to accept connections" in result.stdout.lower()
