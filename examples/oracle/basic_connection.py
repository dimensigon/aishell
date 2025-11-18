#!/usr/bin/env python3
"""
Oracle Database Connection Example

Demonstrates basic Oracle database connectivity using AI-Shell's OracleClient
with python-oracledb thin mode (no Oracle Instant Client required).
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from mcp_clients import OracleClient, ConnectionConfig, MCPClientError


async def main():
    """Demonstrate Oracle database connection and basic queries"""

    print("=" * 60)
    print("AI-Shell Oracle Database Example")
    print("=" * 60)
    print()

    # Connection configuration
    config = ConnectionConfig(
        host='localhost',
        port=1521,
        database='freepdb1',  # Oracle service name
        username='SYS',
        password='MyOraclePass123',
        extra_params={'mode': 'SYSDBA'}  # Required for SYS user
    )

    # Create Oracle client
    client = OracleClient()

    try:
        # 1. Connect to Oracle database
        print("1. Connecting to Oracle database...")
        await client.connect(config)
        print(f"   ✓ Connected! State: {client.state}")
        print()

        # 2. Health check
        print("2. Performing health check...")
        health = await client.health_check()
        print(f"   ✓ Health: {health['state']}")
        print(f"   ✓ Ping successful: {health['ping_successful']}")
        print()

        # 3. Get database version
        print("3. Getting database version...")
        result = await client.execute_query(
            "SELECT banner FROM v$version WHERE ROWNUM = 1"
        )
        version = result['rows'][0][0]
        print(f"   ✓ Database: {version}")
        print()

        # 4. Get current user and database
        print("4. Getting current context...")
        result = await client.execute_query(
            "SELECT USER, SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM DUAL"
        )
        user, schema = result['rows'][0]
        print(f"   ✓ User: {user}")
        print(f"   ✓ Schema: {schema}")
        print()

        # 5. List tables in schema
        print("5. Listing tables...")
        tables = await client.get_table_list()
        print(f"   ✓ Found {len(tables)} tables")
        if tables:
            print("   Tables:")
            for table in tables[:5]:  # Show first 5
                print(f"     - {table}")
            if len(tables) > 5:
                print(f"     ... and {len(tables) - 5} more")
        print()

        # 6. Create a test table
        print("6. Creating test table...")
        await client.execute_ddl("""
            CREATE TABLE ai_shell_demo (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100) NOT NULL,
                description VARCHAR2(500),
                created_at DATE DEFAULT SYSDATE
            )
        """)
        print("   ✓ Table 'ai_shell_demo' created")
        print()

        # 7. Get table information
        print("7. Getting table metadata...")
        table_info = await client.get_table_info('ai_shell_demo')
        print(f"   ✓ Table: {table_info['table_name']}")
        print("   Columns:")
        for col in table_info['columns']:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"     - {col['name']}: {col['type']}({col['length']}) {nullable}")
        print()

        # 8. Insert test data
        print("8. Inserting test data...")
        for i in range(1, 4):
            await client.execute_query(
                """
                INSERT INTO ai_shell_demo (id, name, description)
                VALUES (:id, :name, :desc)
                """,
                {
                    'id': i,
                    'name': f'Test Record {i}',
                    'desc': f'This is a test record created by AI-Shell example #{i}'
                }
            )
        print("   ✓ Inserted 3 records")
        print()

        # 9. Query the data
        print("9. Querying test data...")
        result = await client.execute_query(
            "SELECT * FROM ai_shell_demo ORDER BY id"
        )
        print(f"   ✓ Found {result['rowcount']} rows")
        print("   Data:")
        for row in result['rows']:
            row_id, name, description, created_at = row
            print(f"     [{row_id}] {name}")
            print(f"         {description}")
            print(f"         Created: {created_at}")
        print()

        # 10. Update a record
        print("10. Updating a record...")
        result = await client.execute_query(
            """
            UPDATE ai_shell_demo
            SET description = :new_desc
            WHERE id = :id
            """,
            {
                'id': 2,
                'new_desc': 'Updated description via AI-Shell!'
            }
        )
        print(f"   ✓ Updated {result['rowcount']} row(s)")
        print()

        # 11. Delete a record
        print("11. Deleting a record...")
        result = await client.execute_query(
            "DELETE FROM ai_shell_demo WHERE id = :id",
            {'id': 3}
        )
        print(f"   ✓ Deleted {result['rowcount']} row(s)")
        print()

        # 12. Final count
        print("12. Final record count...")
        result = await client.execute_query(
            "SELECT COUNT(*) FROM ai_shell_demo"
        )
        count = result['rows'][0][0]
        print(f"   ✓ Remaining records: {count}")
        print()

        # 13. Cleanup - Drop test table
        print("13. Cleaning up...")
        await client.execute_ddl("DROP TABLE ai_shell_demo")
        print("   ✓ Test table dropped")
        print()

        # 14. Disconnect
        print("14. Disconnecting...")
        await client.disconnect()
        print(f"   ✓ Disconnected! State: {client.state}")
        print()

        print("=" * 60)
        print("✓ All operations completed successfully!")
        print("=" * 60)

    except MCPClientError as e:
        print(f"\n❌ Database error occurred:")
        print(f"   Error code: {e.error_code}")
        print(f"   Message: {e.message}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

    finally:
        # Ensure cleanup
        if client.is_connected:
            await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
