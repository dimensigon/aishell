"""Pytest fixtures for MCP integration tests."""
import asyncio
import os
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
import subprocess
import yaml
import pytest
import psycopg
import pymongo
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

from tests.integration.mcp.config import (
    DOCKER_CONFIGS,
    DOCKER_COMPOSE_CONFIG,
    CONTAINER_NAMES,
    TIMEOUT_CONNECT
)


@pytest.fixture(scope="session")
def docker_compose_file(tmp_path_factory) -> Path:
    """Create docker-compose.yml file for test containers."""
    compose_dir = tmp_path_factory.mktemp("docker")
    compose_file = compose_dir / "docker-compose.yml"

    with open(compose_file, 'w') as f:
        yaml.dump(DOCKER_COMPOSE_CONFIG, f)

    return compose_file


@pytest.fixture(scope="session")
def docker_services(docker_compose_file):
    """Start all Docker containers for testing."""
    compose_dir = docker_compose_file.parent

    # Start containers
    subprocess.run(
        ["docker-compose", "-f", str(docker_compose_file), "up", "-d"],
        cwd=compose_dir,
        check=True,
        capture_output=True
    )

    # Wait for all services to be healthy
    _wait_for_services()

    yield

    # Cleanup: Stop and remove containers
    subprocess.run(
        ["docker-compose", "-f", str(docker_compose_file), "down", "-v"],
        cwd=compose_dir,
        check=False,
        capture_output=True
    )


def _wait_for_services(max_wait: int = 60):
    """Wait for all Docker services to be healthy."""
    start_time = time.time()
    services = list(CONTAINER_NAMES.values())

    while services and (time.time() - start_time) < max_wait:
        for service in services[:]:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", service],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and "healthy" in result.stdout:
                services.remove(service)
                print(f"✓ {service} is healthy")

        if services:
            time.sleep(2)

    if services:
        raise TimeoutError(f"Services failed to become healthy: {services}")


@pytest.fixture(scope="session")
async def postgresql_connection(docker_services):
    """Provide PostgreSQL connection for tests."""
    config = DOCKER_CONFIGS['postgresql']
    conn_string = (
        f"postgresql://{config['username']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )

    conn = await psycopg.AsyncConnection.connect(conn_string)

    # Create test schema
    async with conn.cursor() as cur:
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()

    yield conn

    await conn.close()


@pytest.fixture(scope="function")
async def postgresql_clean(postgresql_connection):
    """Clean PostgreSQL tables before each test."""
    async with postgresql_connection.cursor() as cur:
        await cur.execute("TRUNCATE TABLE test_users RESTART IDENTITY CASCADE")
        await postgresql_connection.commit()

    yield

    async with postgresql_connection.cursor() as cur:
        await cur.execute("TRUNCATE TABLE test_users RESTART IDENTITY CASCADE")
        await postgresql_connection.commit()


@pytest.fixture(scope="session")
def mysql_connection(docker_services):
    """Provide MySQL connection for tests."""
    import mysql.connector

    config = DOCKER_CONFIGS['mysql']
    conn = mysql.connector.connect(
        host=config['host'],
        port=config['port'],
        user=config['username'],
        password=config['password'],
        database=config['database']
    )

    # Create test schema
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()

    yield conn

    conn.close()


@pytest.fixture(scope="function")
def mysql_clean(mysql_connection):
    """Clean MySQL tables before each test."""
    cursor = mysql_connection.cursor()
    cursor.execute("TRUNCATE TABLE test_users")
    mysql_connection.commit()
    cursor.close()

    yield

    cursor = mysql_connection.cursor()
    cursor.execute("TRUNCATE TABLE test_users")
    mysql_connection.commit()
    cursor.close()


@pytest.fixture(scope="session")
async def mongodb_client(docker_services) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Provide MongoDB client for tests."""
    config = DOCKER_CONFIGS['mongodb']
    uri = (
        f"mongodb://{config['username']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
        "?authSource=admin"
    )

    client = AsyncIOMotorClient(uri)

    # Verify connection
    await client.admin.command('ping')

    yield client

    client.close()


@pytest.fixture(scope="function")
async def mongodb_clean(mongodb_client):
    """Clean MongoDB collections before each test."""
    db = mongodb_client[DOCKER_CONFIGS['mongodb']['database']]

    # Drop all collections
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].drop()

    yield

    # Cleanup after test
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].drop()


@pytest.fixture(scope="session")
async def redis_client(docker_services) -> AsyncGenerator[redis.Redis, None]:
    """Provide Redis client for tests."""
    config = DOCKER_CONFIGS['redis']

    client = redis.Redis(
        host=config['host'],
        port=config['port'],
        password=config['password'],
        decode_responses=True
    )

    # Verify connection
    await client.ping()

    yield client

    await client.close()


@pytest.fixture(scope="function")
async def redis_clean(redis_client):
    """Clean Redis database before each test."""
    await redis_client.flushdb()

    yield

    await redis_client.flushdb()


@pytest.fixture(scope="session")
def sqlite_path(tmp_path_factory) -> Path:
    """Provide SQLite database path for tests."""
    db_path = tmp_path_factory.mktemp("sqlite") / "test.db"
    return db_path


@pytest.fixture(scope="function")
async def sqlite_connection(sqlite_path):
    """Provide SQLite connection for tests."""
    import aiosqlite

    conn = await aiosqlite.connect(str(sqlite_path))

    # Create test schema
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.commit()

    yield conn

    await conn.close()


@pytest.fixture(scope="function")
async def sqlite_clean(sqlite_connection):
    """Clean SQLite tables before each test."""
    await sqlite_connection.execute("DELETE FROM test_users")
    await sqlite_connection.commit()

    yield

    await sqlite_connection.execute("DELETE FROM test_users")
    await sqlite_connection.commit()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Import MCP clients
@pytest.fixture
async def pg_client():
    """Provide PostgreSQL MCP client."""
    from src.mcp.clients.postgresql import PostgreSQLClient
    client = PostgreSQLClient()
    yield client
    if hasattr(client, '_connection') and client._connection:
        await client.disconnect()


@pytest.fixture
async def mysql_client():
    """Provide MySQL MCP client."""
    from src.mcp.clients.mysql import MySQLClient
    client = MySQLClient()
    yield client
    if hasattr(client, '_connection') and client._connection:
        await client.disconnect()


@pytest.fixture
async def mongo_client():
    """Provide MongoDB MCP client."""
    from src.mcp.clients.mongodb import MongoDBClient
    client = MongoDBClient()
    yield client
    if hasattr(client, '_client') and client._client:
        await client.disconnect()


@pytest.fixture
async def redis_mcp_client():
    """Provide Redis MCP client."""
    from src.mcp.clients.redis import RedisClient
    client = RedisClient()
    yield client
    if hasattr(client, '_client') and client._client:
        await client.disconnect()


@pytest.fixture
async def sqlite_client():
    """Provide SQLite MCP client."""
    from src.mcp.clients.sqlite import SQLiteClient
    client = SQLiteClient()
    yield client
    if hasattr(client, '_connection') and client._connection:
        await client.disconnect()


@pytest.fixture
async def connection_manager():
    """Provide connection manager for tests."""
    from src.mcp.manager import ConnectionManager
    manager = ConnectionManager()
    yield manager
    await manager.close_all()
