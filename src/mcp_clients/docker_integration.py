"""
Docker Integration Helper for MCP Clients

Provides utilities for working with Docker containers in integration tests,
including health checks and connection string generation.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DockerContainerConfig:
    """Configuration for a Docker container"""
    name: str
    image: str
    host: str = "localhost"
    port: int = 5432
    environment: Optional[Dict[str, str]] = None
    health_check_command: Optional[str] = None
    max_wait_time: int = 60
    check_interval: float = 1.0


class DockerIntegrationHelper:
    """
    Helper class for Docker integration with MCP clients

    Provides methods to wait for containers, check health, and generate
    connection configurations.
    """

    # Default configurations for common databases
    DEFAULT_CONFIGS = {
        'postgresql': DockerContainerConfig(
            name='test_postgres',
            image='postgres:16-alpine',
            host='localhost',
            port=5432,
            environment={
                'POSTGRES_USER': 'postgres',
                'POSTGRES_PASSWORD': 'MyPostgresPass123',
                'POSTGRES_DB': 'postgres'
            },
            health_check_command='pg_isready -U postgres',
            max_wait_time=30
        ),
        'mysql': DockerContainerConfig(
            name='test_mysql',
            image='mysql:8.0',
            host='localhost',
            port=3306,
            environment={
                'MYSQL_ROOT_PASSWORD': 'MyMySQLPass123',
                'MYSQL_DATABASE': 'test_db',
                'MYSQL_USER': 'test_user',
                'MYSQL_PASSWORD': 'MyMySQLPass123'
            },
            health_check_command='mysqladmin ping -h localhost',
            max_wait_time=60
        ),
        'mongodb': DockerContainerConfig(
            name='test_mongodb',
            image='mongo:7.0',
            host='localhost',
            port=27017,
            environment={
                'MONGO_INITDB_ROOT_USERNAME': 'admin',
                'MONGO_INITDB_ROOT_PASSWORD': 'MyMongoPass123',
                'MONGO_INITDB_DATABASE': 'test_integration_db'
            },
            health_check_command='mongosh --eval "db.adminCommand(\'ping\')"',
            max_wait_time=60
        ),
        'redis': DockerContainerConfig(
            name='test_redis',
            image='redis:7-alpine',
            host='localhost',
            port=6379,
            environment={},
            health_check_command='redis-cli ping',
            max_wait_time=30
        ),
    }

    @staticmethod
    async def wait_for_container(
        container_name: str,
        host: str = 'localhost',
        port: int = 5432,
        max_wait_time: int = 60,
        check_interval: float = 1.0
    ) -> bool:
        """
        Wait for a Docker container to be ready

        Args:
            container_name: Name of the Docker container
            host: Host to connect to
            port: Port to check
            max_wait_time: Maximum time to wait in seconds
            check_interval: Time between checks in seconds

        Returns:
            True if container is ready, False if timeout

        Raises:
            TimeoutError: If container doesn't become ready within max_wait_time
        """
        start_time = time.time()
        logger.info(f"Waiting for container {container_name} at {host}:{port}")

        while time.time() - start_time < max_wait_time:
            try:
                # Try to create a connection
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=5.0
                )
                writer.close()
                await writer.wait_closed()

                elapsed = time.time() - start_time
                logger.info(f"Container {container_name} is ready (took {elapsed:.2f}s)")
                return True

            except (ConnectionRefusedError, OSError, asyncio.TimeoutError):
                # Container not ready yet
                await asyncio.sleep(check_interval)
                continue

        raise TimeoutError(
            f"Container {container_name} did not become ready within {max_wait_time} seconds"
        )

    @staticmethod
    async def wait_for_database(
        db_type: str,
        host: str = 'localhost',
        port: Optional[int] = None,
        max_wait_time: Optional[int] = None
    ) -> bool:
        """
        Wait for a database container using default configuration

        Args:
            db_type: Type of database ('postgresql', 'mysql', 'mongodb', 'redis')
            host: Host to connect to (default: localhost)
            port: Port to check (uses default if not specified)
            max_wait_time: Maximum time to wait (uses default if not specified)

        Returns:
            True if database is ready

        Raises:
            ValueError: If db_type is not recognized
            TimeoutError: If database doesn't become ready in time
        """
        if db_type not in DockerIntegrationHelper.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown database type: {db_type}")

        config = DockerIntegrationHelper.DEFAULT_CONFIGS[db_type]

        return await DockerIntegrationHelper.wait_for_container(
            container_name=config.name,
            host=host,
            port=port or config.port,
            max_wait_time=max_wait_time or config.max_wait_time
        )

    @staticmethod
    def get_connection_config(db_type: str, **overrides) -> Dict[str, Any]:
        """
        Get connection configuration for a database type

        Args:
            db_type: Type of database
            **overrides: Override specific configuration values

        Returns:
            Connection configuration dictionary

        Raises:
            ValueError: If db_type is not recognized
        """
        if db_type not in DockerIntegrationHelper.DEFAULT_CONFIGS:
            raise ValueError(f"Unknown database type: {db_type}")

        config = DockerIntegrationHelper.DEFAULT_CONFIGS[db_type]

        # Build base configuration
        conn_config = {
            'host': overrides.get('host', config.host),
            'port': overrides.get('port', config.port),
        }

        # Add database-specific configuration
        if db_type == 'postgresql':
            conn_config.update({
                'database': overrides.get('database', config.environment['POSTGRES_DB']),
                'username': overrides.get('username', config.environment['POSTGRES_USER']),
                'password': overrides.get('password', config.environment['POSTGRES_PASSWORD']),
            })
        elif db_type == 'mysql':
            conn_config.update({
                'database': overrides.get('database', config.environment['MYSQL_DATABASE']),
                'username': overrides.get('username', config.environment.get('MYSQL_USER', 'root')),
                'password': overrides.get('password', config.environment['MYSQL_ROOT_PASSWORD']),
            })
        elif db_type == 'mongodb':
            conn_config.update({
                'database': overrides.get('database', config.environment['MONGO_INITDB_DATABASE']),
                'username': overrides.get('username', config.environment['MONGO_INITDB_ROOT_USERNAME']),
                'password': overrides.get('password', config.environment['MONGO_INITDB_ROOT_PASSWORD']),
            })
        elif db_type == 'redis':
            conn_config.update({
                'database': overrides.get('database', '0'),
                'username': overrides.get('username', ''),
                'password': overrides.get('password', ''),
            })

        return conn_config

    @staticmethod
    def get_connection_string(db_type: str, **overrides) -> str:
        """
        Get connection string/URI for a database type

        Args:
            db_type: Type of database
            **overrides: Override specific configuration values

        Returns:
            Connection string/URI

        Raises:
            ValueError: If db_type is not recognized
        """
        config = DockerIntegrationHelper.get_connection_config(db_type, **overrides)

        if db_type == 'postgresql':
            return (
                f"postgresql://{config['username']}:{config['password']}@"
                f"{config['host']}:{config['port']}/{config['database']}"
            )
        elif db_type == 'mysql':
            return (
                f"mysql://{config['username']}:{config['password']}@"
                f"{config['host']}:{config['port']}/{config['database']}"
            )
        elif db_type == 'mongodb':
            return (
                f"mongodb://{config['username']}:{config['password']}@"
                f"{config['host']}:{config['port']}/{config['database']}"
            )
        elif db_type == 'redis':
            if config['password']:
                return f"redis://:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
            else:
                return f"redis://{config['host']}:{config['port']}/{config['database']}"

        raise ValueError(f"Unknown database type: {db_type}")

    @staticmethod
    async def check_container_health(
        container_name: str,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Check the health of a Docker container

        Args:
            container_name: Name of the container
            timeout: Timeout for the check in seconds

        Returns:
            Dictionary with health status
        """
        try:
            # Use docker CLI to check container status
            import subprocess

            # Get container status
            result = subprocess.run(
                ['docker', 'inspect', '--format={{.State.Health.Status}}', container_name],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                health_status = result.stdout.strip()
                return {
                    'container': container_name,
                    'healthy': health_status == 'healthy',
                    'status': health_status
                }
            else:
                return {
                    'container': container_name,
                    'healthy': False,
                    'status': 'unknown',
                    'error': result.stderr.strip()
                }

        except subprocess.TimeoutExpired:
            return {
                'container': container_name,
                'healthy': False,
                'status': 'timeout',
                'error': 'Health check command timed out'
            }
        except FileNotFoundError:
            return {
                'container': container_name,
                'healthy': False,
                'status': 'error',
                'error': 'Docker CLI not found'
            }
        except Exception as e:
            return {
                'container': container_name,
                'healthy': False,
                'status': 'error',
                'error': str(e)
            }

    @staticmethod
    async def ensure_container_running(
        container_name: str,
        start_command: Optional[str] = None
    ) -> bool:
        """
        Ensure a container is running, starting it if necessary

        Args:
            container_name: Name of the container
            start_command: Optional command to start the container

        Returns:
            True if container is running
        """
        try:
            import subprocess

            # Check if container exists
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=5.0
            )

            if container_name not in result.stdout:
                logger.warning(f"Container {container_name} not found")
                if start_command:
                    logger.info(f"Starting container with: {start_command}")
                    subprocess.run(start_command, shell=True, check=True)
                return False

            # Check if container is running
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=5.0
            )

            if container_name not in result.stdout:
                # Container exists but not running, start it
                logger.info(f"Starting container {container_name}")
                subprocess.run(['docker', 'start', container_name], check=True)
                await asyncio.sleep(2)  # Give it time to start

            return True

        except Exception as e:
            logger.error(f"Error ensuring container is running: {e}")
            return False

    @staticmethod
    def get_docker_compose_path(test_type: str = 'database') -> str:
        """
        Get path to docker-compose file for tests

        Args:
            test_type: Type of tests ('database', 'integration', 'e2e')

        Returns:
            Path to docker-compose.yml
        """
        from pathlib import Path

        base_path = Path(__file__).parent.parent.parent / 'tests' / 'integration' / test_type
        return str(base_path / 'docker-compose.yml')
