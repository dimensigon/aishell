#!/usr/bin/env python3
"""
Oracle Advanced Features Example

Demonstrates advanced Oracle database operations including:
- Concurrent query execution
- Complex data types
- Stored procedures (PL/SQL blocks)
- Transaction management with savepoints
- Performance monitoring
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from mcp_clients import OracleClient, ConnectionConfig, MCPClientError


async def demonstrate_concurrent_queries(client: OracleClient):
    """Execute multiple queries concurrently"""
    print("\n" + "=" * 60)
    print("CONCURRENT QUERY EXECUTION")
    print("=" * 60)

    start_time = time.time()

    # Execute multiple queries in parallel
    tasks = [
        client.execute_query("SELECT COUNT(*) FROM user_tables"),
        client.execute_query("SELECT COUNT(*) FROM user_views"),
        client.execute_query("SELECT COUNT(*) FROM user_indexes"),
        client.execute_query("SELECT COUNT(*) FROM user_sequences"),
        client.execute_query("SELECT COUNT(*) FROM user_constraints"),
    ]

    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    print(f"✓ Executed {len(tasks)} queries in {elapsed:.3f}s")
    print("\nResults:")
    labels = ["Tables", "Views", "Indexes", "Sequences", "Constraints"]
    for label, result in zip(labels, results):
        count = result['rows'][0][0]
        print(f"  {label}: {count}")


async def demonstrate_plsql_blocks(client: OracleClient):
    """Execute PL/SQL anonymous blocks"""
    print("\n" + "=" * 60)
    print("PL/SQL ANONYMOUS BLOCKS")
    print("=" * 60)

    # Create a test table
    await client.execute_ddl("""
        CREATE TABLE plsql_demo (
            id NUMBER PRIMARY KEY,
            message VARCHAR2(200),
            processed_at TIMESTAMP
        )
    """)
    print("✓ Created test table")

    # Execute PL/SQL block for bulk insert
    await client.execute_query("""
        BEGIN
            FOR i IN 1..10 LOOP
                INSERT INTO plsql_demo (id, message, processed_at)
                VALUES (i, 'Message ' || i, SYSTIMESTAMP);
            END LOOP;
            COMMIT;
        END;
    """)
    print("✓ Executed PL/SQL block (inserted 10 rows)")

    # Verify
    result = await client.execute_query("SELECT COUNT(*) FROM plsql_demo")
    count = result['rows'][0][0]
    print(f"✓ Verified: {count} rows in table")

    # Cleanup
    await client.execute_ddl("DROP TABLE plsql_demo")
    print("✓ Cleaned up test table")


async def demonstrate_savepoints(client: OracleClient):
    """Demonstrate transaction control with savepoints"""
    print("\n" + "=" * 60)
    print("TRANSACTION MANAGEMENT WITH SAVEPOINTS")
    print("=" * 60)

    # Create test table
    await client.execute_ddl("""
        CREATE TABLE transaction_demo (
            id NUMBER PRIMARY KEY,
            status VARCHAR2(50)
        )
    """)
    print("✓ Created test table")

    # Insert initial data
    await client.execute_query(
        "INSERT INTO transaction_demo VALUES (1, 'Initial')"
    )
    print("✓ Inserted initial record")

    # Create savepoint
    await client.execute_query("SAVEPOINT before_update")
    print("✓ Created savepoint 'before_update'")

    # Make changes
    await client.execute_query(
        "UPDATE transaction_demo SET status = 'Updated' WHERE id = 1"
    )
    print("✓ Updated record")

    # Check current state
    result = await client.execute_query(
        "SELECT status FROM transaction_demo WHERE id = 1"
    )
    print(f"  Current status: {result['rows'][0][0]}")

    # Rollback to savepoint
    await client.execute_query("ROLLBACK TO before_update")
    print("✓ Rolled back to savepoint")

    # Verify rollback
    result = await client.execute_query(
        "SELECT status FROM transaction_demo WHERE id = 1"
    )
    print(f"  Status after rollback: {result['rows'][0][0]}")

    # Cleanup
    await client.execute_ddl("DROP TABLE transaction_demo")
    print("✓ Cleaned up test table")


async def demonstrate_complex_datatypes(client: OracleClient):
    """Work with complex Oracle data types"""
    print("\n" + "=" * 60)
    print("COMPLEX DATA TYPES")
    print("=" * 60)

    # Create table with various data types
    await client.execute_ddl("""
        CREATE TABLE datatype_demo (
            id NUMBER PRIMARY KEY,
            text_data VARCHAR2(200),
            large_text CLOB,
            numeric_data NUMBER(10,2),
            date_data DATE,
            timestamp_data TIMESTAMP,
            binary_float_data BINARY_FLOAT,
            binary_double_data BINARY_DOUBLE
        )
    """)
    print("✓ Created table with various data types")

    # Insert test data
    await client.execute_query("""
        INSERT INTO datatype_demo (
            id, text_data, large_text, numeric_data,
            date_data, timestamp_data, binary_float_data, binary_double_data
        ) VALUES (
            1,
            'Regular text',
            'This is a CLOB field that can hold large amounts of text data',
            12345.67,
            SYSDATE,
            SYSTIMESTAMP,
            3.14159,
            2.71828182845905
        )
    """)
    print("✓ Inserted record with various data types")

    # Query the data
    result = await client.execute_query("SELECT * FROM datatype_demo WHERE id = 1")

    print("\nColumn types:")
    for col_name, col_type in zip(result['columns'], result['metadata']['column_types']):
        print(f"  {col_name}: {col_type}")

    print("\nSample data:")
    row = result['rows'][0]
    print(f"  ID: {row[0]}")
    print(f"  Text: {row[1]}")
    print(f"  Large Text (first 50 chars): {str(row[2])[:50]}...")
    print(f"  Numeric: {row[3]}")
    print(f"  Date: {row[4]}")
    print(f"  Timestamp: {row[5]}")
    print(f"  Binary Float: {row[6]}")
    print(f"  Binary Double: {row[7]}")

    # Cleanup
    await client.execute_ddl("DROP TABLE datatype_demo")
    print("\n✓ Cleaned up test table")


async def demonstrate_metadata_queries(client: OracleClient):
    """Demonstrate advanced metadata queries"""
    print("\n" + "=" * 60)
    print("ADVANCED METADATA QUERIES")
    print("=" * 60)

    # Get database information
    queries = {
        "Database Name": "SELECT name FROM v$database",
        "Instance Name": "SELECT instance_name FROM v$instance",
        "Startup Time": "SELECT startup_time FROM v$instance",
        "DB Character Set": "SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET'",
        "Total Tablespaces": "SELECT COUNT(*) FROM dba_tablespaces",
    }

    for label, query in queries.items():
        try:
            result = await client.execute_query(query)
            value = result['rows'][0][0]
            print(f"  {label}: {value}")
        except MCPClientError:
            print(f"  {label}: <insufficient privileges>")


async def demonstrate_performance_monitoring(client: OracleClient):
    """Monitor query performance"""
    print("\n" + "=" * 60)
    print("PERFORMANCE MONITORING")
    print("=" * 60)

    # Create a table with more data
    await client.execute_ddl("""
        CREATE TABLE perf_demo (
            id NUMBER PRIMARY KEY,
            data VARCHAR2(1000)
        )
    """)
    print("✓ Created performance test table")

    # Insert test data
    print("  Inserting 1000 rows...")
    start = time.time()

    for i in range(1, 1001):
        await client.execute_query(
            "INSERT INTO perf_demo VALUES (:id, :data)",
            {'id': i, 'data': f'Data row {i}' * 10}
        )

    insert_time = time.time() - start
    print(f"  ✓ Insert time: {insert_time:.2f}s ({1000/insert_time:.0f} rows/sec)")

    # Full table scan
    print("  Performing full table scan...")
    start = time.time()
    result = await client.execute_query("SELECT * FROM perf_demo")
    scan_time = time.time() - start
    print(f"  ✓ Scan time: {scan_time:.3f}s ({result['rowcount']} rows)")

    # Indexed query
    await client.execute_ddl("CREATE INDEX idx_perf_demo_id ON perf_demo(id)")
    print("  ✓ Created index on ID column")

    start = time.time()
    result = await client.execute_query(
        "SELECT * FROM perf_demo WHERE id = :id",
        {'id': 500}
    )
    indexed_time = time.time() - start
    print(f"  ✓ Indexed query time: {indexed_time:.3f}s")

    # Cleanup
    await client.execute_ddl("DROP TABLE perf_demo")
    print("  ✓ Cleaned up test table")


async def main():
    """Run all advanced feature demonstrations"""

    config = ConnectionConfig(
        host='localhost',
        port=1521,
        database='freepdb1',
        username='SYS',
        password='MyOraclePass123',
        extra_params={'mode': 'SYSDBA'}
    )

    client = OracleClient()

    try:
        print("Connecting to Oracle database...")
        await client.connect(config)
        print(f"✓ Connected! ({client.state})")

        # Run demonstrations
        await demonstrate_concurrent_queries(client)
        await demonstrate_plsql_blocks(client)
        await demonstrate_savepoints(client)
        await demonstrate_complex_datatypes(client)
        await demonstrate_metadata_queries(client)
        await demonstrate_performance_monitoring(client)

        print("\n" + "=" * 60)
        print("✓ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except MCPClientError as e:
        print(f"\n❌ Database error: {e.message}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if client.is_connected:
            await client.disconnect()
            print("\n✓ Disconnected from database")


if __name__ == '__main__':
    asyncio.run(main())
