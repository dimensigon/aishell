"""Configuration for MCP integration tests."""
import os
from typing import Dict, Any

# Docker container configurations
DOCKER_CONFIGS: Dict[str, Dict[str, Any]] = {
    'postgresql': {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': 'test_integration_db',
        'username': 'postgres',
        'password': 'MyPostgresPass123',
        'image': 'postgres:15-alpine',
        'healthcheck': {
            'test': ['CMD-SHELL', 'pg_isready -U postgres'],
            'interval': '5s',
            'timeout': '3s',
            'retries': 5
        }
    },
    'mysql': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'database': 'test_integration_db',
        'username': 'root',
        'password': 'MyMySQLPass123',
        'image': 'mysql:8.0',
        'healthcheck': {
            'test': ['CMD', 'mysqladmin', 'ping', '-h', 'localhost'],
            'interval': '5s',
            'timeout': '3s',
            'retries': 5
        }
    },
    'mongodb': {
        'host': os.getenv('MONGODB_HOST', 'localhost'),
        'port': int(os.getenv('MONGODB_PORT', 27017)),
        'database': 'test_integration_db',
        'username': 'admin',
        'password': 'MyMongoPass123',
        'image': 'mongo:7.0',
        'healthcheck': {
            'test': ['CMD', 'mongosh', '--eval', 'db.adminCommand("ping")'],
            'interval': '5s',
            'timeout': '3s',
            'retries': 5
        }
    },
    'redis': {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': 'MyRedisPass123',
        'image': 'redis:7-alpine',
        'healthcheck': {
            'test': ['CMD', 'redis-cli', 'ping'],
            'interval': '5s',
            'timeout': '3s',
            'retries': 5
        }
    },
    'sqlite': {
        'path': '/tmp/test_integration.db'
    }
}

# Test timeouts
TIMEOUT_CONNECT = 30
TIMEOUT_QUERY = 10
TIMEOUT_HEALTH = 5

# Performance benchmarks
BENCHMARK_CONFIGS = {
    'query_count': 1000,
    'concurrent_connections': 10,
    'large_result_rows': 10000,
    'bulk_insert_rows': 5000
}

# Container names
CONTAINER_NAMES = {
    'postgresql': 'mcp-test-postgres',
    'mysql': 'mcp-test-mysql',
    'mongodb': 'mcp-test-mongodb',
    'redis': 'mcp-test-redis'
}

# Docker Compose configuration
DOCKER_COMPOSE_CONFIG = {
    'version': '3.8',
    'services': {
        'postgresql': {
            'image': DOCKER_CONFIGS['postgresql']['image'],
            'container_name': CONTAINER_NAMES['postgresql'],
            'environment': {
                'POSTGRES_PASSWORD': DOCKER_CONFIGS['postgresql']['password'],
                'POSTGRES_DB': DOCKER_CONFIGS['postgresql']['database']
            },
            'ports': [f"{DOCKER_CONFIGS['postgresql']['port']}:5432"],
            'healthcheck': DOCKER_CONFIGS['postgresql']['healthcheck'],
            'volumes': ['postgres-data:/var/lib/postgresql/data']
        },
        'mysql': {
            'image': DOCKER_CONFIGS['mysql']['image'],
            'container_name': CONTAINER_NAMES['mysql'],
            'environment': {
                'MYSQL_ROOT_PASSWORD': DOCKER_CONFIGS['mysql']['password'],
                'MYSQL_DATABASE': DOCKER_CONFIGS['mysql']['database']
            },
            'ports': [f"{DOCKER_CONFIGS['mysql']['port']}:3306"],
            'healthcheck': DOCKER_CONFIGS['mysql']['healthcheck'],
            'volumes': ['mysql-data:/var/lib/mysql']
        },
        'mongodb': {
            'image': DOCKER_CONFIGS['mongodb']['image'],
            'container_name': CONTAINER_NAMES['mongodb'],
            'environment': {
                'MONGO_INITDB_ROOT_USERNAME': DOCKER_CONFIGS['mongodb']['username'],
                'MONGO_INITDB_ROOT_PASSWORD': DOCKER_CONFIGS['mongodb']['password'],
                'MONGO_INITDB_DATABASE': DOCKER_CONFIGS['mongodb']['database']
            },
            'ports': [f"{DOCKER_CONFIGS['mongodb']['port']}:27017"],
            'healthcheck': DOCKER_CONFIGS['mongodb']['healthcheck'],
            'volumes': ['mongodb-data:/data/db']
        },
        'redis': {
            'image': DOCKER_CONFIGS['redis']['image'],
            'container_name': CONTAINER_NAMES['redis'],
            'command': f"redis-server --requirepass {DOCKER_CONFIGS['redis']['password']}",
            'ports': [f"{DOCKER_CONFIGS['redis']['port']}:6379"],
            'healthcheck': DOCKER_CONFIGS['redis']['healthcheck'],
            'volumes': ['redis-data:/data']
        }
    },
    'volumes': {
        'postgres-data': {},
        'mysql-data': {},
        'mongodb-data': {},
        'redis-data': {}
    }
}
