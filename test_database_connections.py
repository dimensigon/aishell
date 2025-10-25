#!/usr/bin/env python3
"""
Database Connection Test Script for AIShell
Tests connections to Oracle, PostgreSQL, and MySQL databases
"""

import asyncio
import sys
from datetime import datetime

# Database connection test results
test_results = {}


async def test_oracle_cdb():
    """Test Oracle CDB$ROOT connection"""
    print("\n" + "="*60)
    print("Testing Oracle CDB$ROOT Connection")
    print("="*60)

    try:
        import oracledb

        connection_params = {
            "user": "SYS",
            "password": "MyOraclePass123",
            "dsn": "localhost:1521/free",
            "mode": oracledb.SYSDBA
        }

        print(f"Connecting to: {connection_params['dsn']}")
        print(f"User: {connection_params['user']} as SYSDBA")

        connection = oracledb.connect(**connection_params)
        cursor = connection.cursor()

        # Test query
        cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
        version = cursor.fetchone()
        print(f"✅ SUCCESS: Connected to Oracle")
        print(f"Version: {version[0]}")

        # Get database name
        cursor.execute("SELECT name FROM v$database")
        db_name = cursor.fetchone()
        print(f"Database Name: {db_name[0]}")

        # Get PDB information
        cursor.execute("SELECT name, open_mode FROM v$pdbs ORDER BY name")
        pdbs = cursor.fetchall()
        print(f"\nPDBs:")
        for pdb in pdbs:
            print(f"  - {pdb[0]}: {pdb[1]}")

        cursor.close()
        connection.close()

        test_results['oracle_cdb'] = {'status': 'PASS', 'version': version[0], 'database': db_name[0]}
        return True

    except ImportError as e:
        print(f"❌ FAIL: Oracle client library not available: {e}")
        test_results['oracle_cdb'] = {'status': 'FAIL', 'error': f'Import error: {e}'}
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        test_results['oracle_cdb'] = {'status': 'FAIL', 'error': str(e)}
        return False


async def test_oracle_pdb():
    """Test Oracle FREEPDB1 connection"""
    print("\n" + "="*60)
    print("Testing Oracle FREEPDB1 Connection")
    print("="*60)

    try:
        import oracledb

        connection_params = {
            "user": "SYS",
            "password": "MyOraclePass123",
            "dsn": "localhost:1521/freepdb1",
            "mode": oracledb.SYSDBA
        }

        print(f"Connecting to: {connection_params['dsn']}")
        print(f"User: {connection_params['user']} as SYSDBA")

        connection = oracledb.connect(**connection_params)
        cursor = connection.cursor()

        # Test query
        cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
        version = cursor.fetchone()
        print(f"✅ SUCCESS: Connected to Oracle PDB")
        print(f"Version: {version[0]}")

        # Get PDB name
        cursor.execute("SELECT sys_context('USERENV', 'CON_NAME') FROM dual")
        pdb_name = cursor.fetchone()
        print(f"PDB Name: {pdb_name[0]}")

        # Get open mode
        cursor.execute("SELECT open_mode FROM v$database")
        open_mode = cursor.fetchone()
        print(f"Open Mode: {open_mode[0]}")

        cursor.close()
        connection.close()

        test_results['oracle_pdb'] = {'status': 'PASS', 'version': version[0], 'pdb': pdb_name[0]}
        return True

    except ImportError as e:
        print(f"❌ FAIL: Oracle client library not available: {e}")
        test_results['oracle_pdb'] = {'status': 'FAIL', 'error': f'Import error: {e}'}
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        test_results['oracle_pdb'] = {'status': 'FAIL', 'error': str(e)}
        return False


async def test_postgresql():
    """Test PostgreSQL connection"""
    print("\n" + "="*60)
    print("Testing PostgreSQL Connection")
    print("="*60)

    try:
        import asyncpg

        connection_string = "postgresql://postgres:MyPostgresPass123@localhost:5432/postgres"

        print(f"Connecting to: localhost:5432/postgres")
        print(f"User: postgres")

        connection = await asyncpg.connect(connection_string)

        # Test query
        version = await connection.fetchval("SELECT version()")
        print(f"✅ SUCCESS: Connected to PostgreSQL")
        print(f"Version: {version}")

        # Get database name
        db_name = await connection.fetchval("SELECT current_database()")
        print(f"Database Name: {db_name}")

        # Get user
        user = await connection.fetchval("SELECT current_user")
        print(f"Current User: {user}")

        # List databases
        databases = await connection.fetch(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
        )
        print(f"\nDatabases:")
        for db in databases:
            print(f"  - {db['datname']}")

        await connection.close()

        test_results['postgresql'] = {'status': 'PASS', 'version': version[:50], 'database': db_name}
        return True

    except ImportError as e:
        print(f"❌ FAIL: PostgreSQL client library not available: {e}")
        test_results['postgresql'] = {'status': 'FAIL', 'error': f'Import error: {e}'}
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        test_results['postgresql'] = {'status': 'FAIL', 'error': str(e)}
        return False


async def test_mysql():
    """Test MySQL connection"""
    print("\n" + "="*60)
    print("Testing MySQL Connection")
    print("="*60)

    try:
        import aiomysql

        connection_params = {
            "host": "localhost",
            "port": 3307,
            "user": "root",
            "password": "MyMySQLPass123",
            "db": "mysql"
        }

        print(f"Connecting to: {connection_params['host']}:{connection_params['port']}")
        print(f"User: {connection_params['user']}")

        connection = await aiomysql.connect(**connection_params)
        cursor = await connection.cursor()

        # Test query
        await cursor.execute("SELECT VERSION()")
        version = await cursor.fetchone()
        print(f"✅ SUCCESS: Connected to MySQL")
        print(f"Version: {version[0]}")

        # Get database name
        await cursor.execute("SELECT DATABASE()")
        db_name = await cursor.fetchone()
        print(f"Database Name: {db_name[0]}")

        # Get user
        await cursor.execute("SELECT USER()")
        user = await cursor.fetchone()
        print(f"Current User: {user[0]}")

        # List databases
        await cursor.execute("SHOW DATABASES")
        databases = await cursor.fetchall()
        print(f"\nDatabases:")
        for db in databases:
            print(f"  - {db[0]}")

        await cursor.close()
        connection.close()

        test_results['mysql'] = {'status': 'PASS', 'version': version[0], 'database': db_name[0]}
        return True

    except ImportError as e:
        print(f"❌ FAIL: MySQL client library not available: {e}")
        test_results['mysql'] = {'status': 'FAIL', 'error': f'Import error: {e}'}
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        test_results['mysql'] = {'status': 'FAIL', 'error': str(e)}
        return False


async def main():
    """Run all database connection tests"""
    print("\n" + "="*60)
    print("AIShell Database Connection Test Suite")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Run all tests
    await test_oracle_cdb()
    await test_oracle_pdb()
    await test_postgresql()
    await test_mysql()

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results.values() if r['status'] == 'PASS')
    failed_tests = total_tests - passed_tests

    for test_name, result in test_results.items():
        status_symbol = "✅" if result['status'] == 'PASS' else "❌"
        print(f"{status_symbol} {test_name}: {result['status']}")
        if result['status'] == 'FAIL':
            print(f"   Error: {result.get('error', 'Unknown error')}")

    print(f"\nTotal: {total_tests} tests")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    # Exit with appropriate code
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
