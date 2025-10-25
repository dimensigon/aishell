"""
Example database client configurations

This file demonstrates how to configure and use the database clients
with various options and features.
"""

import asyncio
import os
from .base import DatabaseConfig
from .manager import DatabaseClientManager, DatabaseType


# Example configurations for different databases
ORACLE_CDB_CONFIG = DatabaseConfig(
    host=os.getenv('ORACLE_CDB_HOST', 'localhost'),
    port=int(os.getenv('ORACLE_CDB_PORT', '1521')),
    database=os.getenv('ORACLE_CDB_DATABASE', 'free'),
    user=os.getenv('ORACLE_CDB_USER', 'SYS'),
    password=os.getenv('ORACLE_CDB_PASSWORD', 'MyOraclePass123'),

    # Pool configuration
    min_pool_size=5,
    max_pool_size=20,
    pool_timeout=30.0,
    connection_timeout=10.0,

    # Query configuration
    query_timeout=300.0,

    # Retry configuration
    max_retries=3,
    retry_delay=1.0,
    retry_backoff=2.0,
)

ORACLE_PDB_CONFIG = DatabaseConfig(
    host=os.getenv('ORACLE_PDB_HOST', 'localhost'),
    port=int(os.getenv('ORACLE_PDB_PORT', '1521')),
    database=os.getenv('ORACLE_PDB_DATABASE', 'freepdb1'),
    user=os.getenv('ORACLE_PDB_USER', 'SYS'),
    password=os.getenv('ORACLE_PDB_PASSWORD', 'MyOraclePass123'),

    min_pool_size=5,
    max_pool_size=20,
)

POSTGRESQL_CONFIG = DatabaseConfig(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', '5432')),
    database=os.getenv('POSTGRES_DATABASE', 'postgres'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'MyPostgresPass123'),

    min_pool_size=5,
    max_pool_size=20,

    # SSL configuration (optional)
    ssl_enabled=False,
    # ssl_cert='/path/to/cert.pem',
    # ssl_key='/path/to/key.pem',
    # ssl_ca='/path/to/ca.pem',
)

MYSQL_CONFIG = DatabaseConfig(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', '3307')),
    database=os.getenv('MYSQL_DATABASE', 'mysql'),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', 'MyMySQLPass123'),

    min_pool_size=5,
    max_pool_size=20,
)


async def example_basic_usage():
    """Example: Basic database client usage"""
    from .postgresql_client import PostgreSQLClient

    # Create and initialize client
    client = PostgreSQLClient(POSTGRESQL_CONFIG, name="my_postgres")
    await client.initialize()

    try:
        # Execute a simple query
        result = await client.execute("SELECT * FROM users LIMIT 10")

        print(f"Columns: {result['columns']}")
        print(f"Rows: {len(result['rows'])}")
        print(f"Execution time: {result['execution_time']:.3f}s")

        # Execute with parameters
        result = await client.execute(
            "SELECT * FROM users WHERE age > $1",
            params={'age': 18}
        )

    finally:
        await client.close()


async def example_transaction():
    """Example: Transaction management"""
    from .mysql_client import MySQLClient

    client = MySQLClient(MYSQL_CONFIG, name="my_mysql")
    await client.initialize()

    try:
        # Use transaction context manager
        async with client.transaction():
            # All queries in this block are part of the transaction
            await client.execute(
                "INSERT INTO accounts (user_id, balance) VALUES (%s, %s)",
                params={'user_id': 1, 'balance': 1000}
            )

            await client.execute(
                "UPDATE accounts SET balance = balance - 100 WHERE user_id = %s",
                params={'user_id': 1}
            )

            # Transaction is automatically committed on success
            # or rolled back on exception

    except Exception as e:
        print(f"Transaction failed: {e}")

    finally:
        await client.close()


async def example_health_monitoring():
    """Example: Health checks and monitoring"""
    from .oracle_client import OracleClient

    client = OracleClient(ORACLE_CDB_CONFIG, name="my_oracle")
    await client.initialize()

    try:
        # Perform health check
        health = await client.health_check()

        print(f"Health status: {health.status.value}")
        print(f"Response time: {health.response_time:.3f}s")
        print(f"Details: {health.details}")

        # Get client metrics
        metrics = client.metrics
        print(f"\nClient Metrics:")
        print(f"  Total queries: {metrics['query_count']}")
        print(f"  Error count: {metrics['error_count']}")
        print(f"  Error rate: {metrics['error_rate']:.2%}")
        print(f"  Avg execution time: {metrics['avg_execution_time']:.3f}s")
        print(f"  Pool stats: {metrics['pool_stats']}")

    finally:
        await client.close()


async def example_client_manager():
    """Example: Using DatabaseClientManager"""
    manager = DatabaseClientManager()

    try:
        # Register multiple clients
        await manager.register_client(
            'oracle_cdb',
            DatabaseType.ORACLE,
            ORACLE_CDB_CONFIG
        )

        await manager.register_client(
            'postgres',
            DatabaseType.POSTGRESQL,
            POSTGRESQL_CONFIG
        )

        await manager.register_client(
            'mysql',
            DatabaseType.MYSQL,
            MYSQL_CONFIG
        )

        # List all clients
        print(f"Registered clients: {manager.list_clients()}")
        print(f"Client summary: {manager.summary}")

        # Execute query on specific client
        result = await manager.execute_on_client(
            'postgres',
            "SELECT version()"
        )
        print(f"\nPostgreSQL version: {result['rows'][0][0]}")

        # Health check all clients
        health_results = await manager.health_check_all()
        print("\nHealth Check Results:")
        for name, health in health_results.items():
            print(f"  {name}: {health['status']} ({health['response_time']:.3f}s)")

        # Get metrics from all clients
        all_metrics = await manager.get_all_metrics()
        print("\nAll Client Metrics:")
        for name, metrics in all_metrics.items():
            print(f"  {name}: {metrics.get('query_count', 0)} queries")

    finally:
        # Close all clients
        await manager.close_all()


async def example_pdb_operations():
    """Example: Oracle PDB operations"""
    from .oracle_client import OraclePDBClient

    # Create PDB client with CDB config for management
    client = OraclePDBClient(
        ORACLE_PDB_CONFIG,
        name="my_pdb",
        cdb_config=ORACLE_CDB_CONFIG
    )

    await client.initialize()

    try:
        # Get current PDB name
        current_pdb = await client.get_current_pdb()
        print(f"Current PDB: {current_pdb}")

        # List all PDBs
        pdbs = await client.list_pdbs()
        print("\nAvailable PDBs:")
        for pdb in pdbs:
            print(f"  {pdb['pdb_name']}: {pdb['status']} ({pdb['open_mode']})")

        # Switch to different PDB
        # await client.switch_pdb('FREEPDB2')

        # Get PDB info
        pdb_info = await client.get_pdb_info()
        print(f"\nPDB Info: {pdb_info}")

    finally:
        await client.close()


async def example_from_env():
    """Example: Create clients from environment variables"""
    from .manager import create_clients_from_env

    # This automatically creates clients based on environment variables
    # Set these environment variables:
    # - ORACLE_CDB_HOST, ORACLE_CDB_PORT, ORACLE_CDB_DATABASE, etc.
    # - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, etc.
    # - MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, etc.

    manager = await create_clients_from_env()

    try:
        print(f"Created {manager.client_count} clients from environment")
        print(f"Clients: {manager.list_clients()}")

        # Use the clients
        if 'postgresql' in manager.list_clients():
            pg_client = manager.get_client('postgresql')
            version = await pg_client.get_version()
            print(f"PostgreSQL: {version}")

    finally:
        await manager.close_all()


if __name__ == '__main__':
    # Run examples
    print("=== Basic Usage ===")
    asyncio.run(example_basic_usage())

    print("\n=== Transaction Management ===")
    asyncio.run(example_transaction())

    print("\n=== Health Monitoring ===")
    asyncio.run(example_health_monitoring())

    print("\n=== Client Manager ===")
    asyncio.run(example_client_manager())

    print("\n=== PDB Operations ===")
    asyncio.run(example_pdb_operations())

    print("\n=== From Environment ===")
    asyncio.run(example_from_env())
