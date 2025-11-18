# Oracle Database Support in AI-Shell

Comprehensive guide to Oracle database integration using python-oracledb thin mode (no Oracle Instant Client required).

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Connection Methods](#connection-methods)
- [Query Execution](#query-execution)
- [DDL Operations](#ddl-operations)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

AI-Shell provides native Oracle database support through the `OracleClient` MCP (Model Context Protocol) client. The implementation uses **python-oracledb** in **thin mode**, eliminating the need for Oracle Instant Client installation.

### Key Features

✅ **Thin Mode Connection** - No Oracle Client installation required
✅ **Async Operations** - Full async/await support
✅ **CDB & PDB Support** - Connect to Container and Pluggable databases
✅ **Connection Pooling** - Efficient connection management
✅ **Comprehensive Error Handling** - Oracle-specific error codes
✅ **Metadata Queries** - Table info, schema introspection
✅ **Health Monitoring** - Built-in connection health checks

## Installation

### 1. Install AI-Shell with Oracle Support

```bash
# Install from PyPI with Oracle extras
pip install ai-shell-py[oracle]

# Or install all database drivers
pip install ai-shell-py[all-databases]
```

### 2. Verify Installation

```bash
python -c "import oracledb; print(f'oracledb version: {oracledb.__version__}')"
```

Expected output:
```
oracledb version: 2.0.0
```

### 3. No Oracle Client Required

The thin mode driver **does not require** Oracle Instant Client:
- ✅ Works on any platform (Linux, macOS, Windows)
- ✅ No additional downloads or configuration
- ✅ Pure Python implementation

## Connection Methods

### Method 1: Direct Connection (CDB)

Connect to Oracle Container Database (CDB$ROOT):

```python
import asyncio
from ai_shell_py.mcp_clients import OracleClient, ConnectionConfig

async def connect_to_cdb():
    client = OracleClient()

    config = ConnectionConfig(
        host='localhost',
        port=1521,
        database='free',  # Service name
        username='SYS',
        password='MyOraclePass123',
        extra_params={'mode': 'SYSDBA'}  # For SYS connections
    )

    await client.connect(config)
    print(f"Connected! State: {client.state}")

    # Execute query
    result = await client.execute_query("SELECT 1 FROM DUAL")
    print(f"Result: {result['rows'][0][0]}")

    await client.disconnect()

asyncio.run(connect_to_cdb())
```

### Method 2: PDB Connection

Connect to Oracle Pluggable Database:

```python
config = ConnectionConfig(
    host='localhost',
    port=1521,
    database='freepdb1',  # PDB service name
    username='SYS',
    password='MyOraclePass123',
    extra_params={'mode': 'SYSDBA'}
)
```

### Method 3: Regular User Connection

Connect as a regular (non-SYS) user:

```python
config = ConnectionConfig(
    host='localhost',
    port=1521,
    database='freepdb1',
    username='myuser',
    password='mypassword',
    extra_params={}  # No SYSDBA mode
)
```

### Method 4: Connection String (DSN)

The client automatically builds DSN in format: `host:port/service_name`

```python
# Internal DSN format: localhost:1521/freepdb1
```

## Query Execution

### SELECT Queries

```python
# Basic SELECT
result = await client.execute_query("SELECT * FROM employees")

print(f"Columns: {result['columns']}")
print(f"Rows: {len(result['rows'])}")
print(f"Row count: {result['rowcount']}")

# Access data
for row in result['rows']:
    emp_id, name, email = row
    print(f"{emp_id}: {name} - {email}")
```

### Parameterized Queries

Use Oracle named parameters (`:param_name`):

```python
# Named parameters
result = await client.execute_query(
    "SELECT * FROM employees WHERE department_id = :dept_id",
    {'dept_id': 10}
)

# Multiple parameters
result = await client.execute_query(
    """
    SELECT * FROM employees
    WHERE department_id = :dept
    AND salary > :min_salary
    """,
    {'dept': 10, 'min_salary': 50000}
)
```

### INSERT, UPDATE, DELETE

```python
# INSERT with parameters
result = await client.execute_query(
    """
    INSERT INTO employees (id, name, email, hire_date)
    VALUES (:id, :name, :email, SYSDATE)
    """,
    {'id': 1001, 'name': 'John Doe', 'email': 'john@example.com'}
)
print(f"Rows inserted: {result['rowcount']}")

# UPDATE
result = await client.execute_query(
    "UPDATE employees SET salary = :salary WHERE id = :id",
    {'salary': 75000, 'id': 1001}
)

# DELETE
result = await client.execute_query(
    "DELETE FROM employees WHERE id = :id",
    {'id': 1001}
)
```

## DDL Operations

### Creating Tables

```python
await client.execute_ddl("""
    CREATE TABLE customers (
        id NUMBER PRIMARY KEY,
        name VARCHAR2(100) NOT NULL,
        email VARCHAR2(255),
        created_at DATE DEFAULT SYSDATE,
        status VARCHAR2(20) DEFAULT 'active'
    )
""")
```

### Altering Tables

```python
# Add columns
await client.execute_ddl("""
    ALTER TABLE customers ADD (
        phone VARCHAR2(20),
        address VARCHAR2(500)
    )
""")

# Modify columns
await client.execute_ddl(
    "ALTER TABLE customers MODIFY name VARCHAR2(200)"
)
```

### Creating Indexes

```python
await client.execute_ddl(
    "CREATE INDEX idx_customers_email ON customers(email)"
)

# Unique index
await client.execute_ddl(
    "CREATE UNIQUE INDEX idx_customers_phone ON customers(phone)"
)
```

### Dropping Objects

```python
await client.execute_ddl("DROP TABLE customers")
await client.execute_ddl("DROP INDEX idx_customers_email")
```

## Advanced Features

### Table Metadata

Get comprehensive table information:

```python
table_info = await client.get_table_info('employees')

print(f"Table: {table_info['table_name']}")
for col in table_info['columns']:
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    print(f"  {col['name']}: {col['type']}({col['length']}) {nullable}")
```

Output:
```
Table: employees
  ID: NUMBER(22) NOT NULL
  NAME: VARCHAR2(100) NOT NULL
  EMAIL: VARCHAR2(255) NULL
  HIRE_DATE: DATE(7) NULL
```

### List All Tables

```python
tables = await client.get_table_list()
print(f"Found {len(tables)} tables:")
for table in tables:
    print(f"  - {table}")
```

### Health Checks

```python
health = await client.health_check()

print(f"State: {health['state']}")
print(f"Connected: {health['connected']}")
print(f"Ping successful: {health['ping_successful']}")
print(f"Connection time: {health['connection_time']}")
```

### Concurrent Queries

Execute multiple queries in parallel:

```python
tasks = [
    client.execute_query("SELECT COUNT(*) FROM employees"),
    client.execute_query("SELECT COUNT(*) FROM departments"),
    client.execute_query("SELECT COUNT(*) FROM locations")
]

results = await asyncio.gather(*tasks)

for i, result in enumerate(results):
    count = result['rows'][0][0]
    print(f"Query {i+1}: {count} rows")
```

## Best Practices

### 1. Connection Management

```python
# ✅ GOOD: Use context manager pattern
async def query_database():
    client = OracleClient()
    try:
        await client.connect(config)
        result = await client.execute_query("SELECT * FROM users")
        return result
    finally:
        await client.disconnect()

# ✅ GOOD: Check connection state
if client.is_connected:
    result = await client.execute_query("SELECT 1 FROM DUAL")
```

### 2. Error Handling

```python
from ai_shell_py.mcp_clients import MCPClientError

try:
    await client.execute_query("SELECT * FROM nonexistent_table")
except MCPClientError as e:
    print(f"Error code: {e.error_code}")
    print(f"Message: {e.message}")

    # Handle specific Oracle errors
    if "ORA-00942" in str(e):
        print("Table or view does not exist")
    elif "ORA-01017" in str(e):
        print("Invalid username/password")
```

### 3. Parameterized Queries

```python
# ✅ GOOD: Use parameters to prevent SQL injection
user_input = "'; DROP TABLE users; --"
result = await client.execute_query(
    "SELECT * FROM users WHERE username = :username",
    {'username': user_input}  # Safe - Oracle handles escaping
)

# ❌ BAD: String concatenation
query = f"SELECT * FROM users WHERE username = '{user_input}'"  # SQL injection risk!
```

### 4. Transaction Management

```python
# For DML operations, changes are auto-committed
# To control transactions, use SAVEPOINT and ROLLBACK:

await client.execute_query("SAVEPOINT before_update")
try:
    await client.execute_query("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    await client.execute_query("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
except Exception as e:
    await client.execute_query("ROLLBACK TO before_update")
    raise
```

### 5. Performance Optimization

```python
# Use connection pooling for multiple operations
from ai_shell_py.mcp_clients import ConnectionManager

manager = ConnectionManager(max_connections=10)

# Create pooled connection
await manager.create_connection('oracle_pool', 'oracle', config)

# Reuse connection
result1 = await manager.execute_query('oracle_pool', "SELECT * FROM users")
result2 = await manager.execute_query('oracle_pool', "SELECT * FROM orders")
```

## Troubleshooting

### Connection Errors

#### ORA-12170: TNS:Connect timeout occurred

```python
# Increase connection timeout
config.extra_params = {
    'mode': 'SYSDBA',
    'timeout': 60  # seconds
}
```

#### ORA-01017: invalid username/password

```python
# Verify credentials and case sensitivity
# Oracle usernames/passwords are case-sensitive when quoted
config.username = 'SYS'  # Not 'sys' for SYS user
config.extra_params = {'mode': 'SYSDBA'}  # Required for SYS
```

#### ORA-12514: TNS:listener does not currently know of service

```python
# Verify service name (not SID)
# Check with: SELECT name FROM v$database;
config.database = 'freepdb1'  # Use correct service name
```

### Query Errors

#### ORA-00942: table or view does not exist

```python
# Check table name case and schema
# Oracle stores unquoted identifiers in UPPERCASE
table_info = await client.get_table_info('EMPLOYEES')  # Not 'employees'

# Or use quoted identifiers in SQL
await client.execute_query('SELECT * FROM "employees"')  # Case-sensitive
```

#### ORA-01722: invalid number

```python
# Ensure parameter types match column types
result = await client.execute_query(
    "SELECT * FROM users WHERE id = :id",
    {'id': 123}  # Use int, not '123'
)
```

### Performance Issues

```python
# Enable query result streaming for large datasets
# Monitor execution time
import time

start = time.time()
result = await client.execute_query("SELECT * FROM large_table")
elapsed = time.time() - start

print(f"Query executed in {elapsed:.2f}s")
print(f"Returned {result['rowcount']} rows")
```

## Example: Complete CRUD Application

```python
import asyncio
from ai_shell_py.mcp_clients import OracleClient, ConnectionConfig, MCPClientError

class EmployeeManager:
    def __init__(self, config: ConnectionConfig):
        self.client = OracleClient()
        self.config = config

    async def connect(self):
        await self.client.connect(self.config)

    async def disconnect(self):
        await self.client.disconnect()

    async def create_table(self):
        """Create employees table"""
        await self.client.execute_ddl("""
            CREATE TABLE employees (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100) NOT NULL,
                email VARCHAR2(255),
                department VARCHAR2(50),
                salary NUMBER(10,2),
                hire_date DATE DEFAULT SYSDATE
            )
        """)

    async def add_employee(self, emp_id, name, email, department, salary):
        """Add new employee"""
        result = await self.client.execute_query(
            """
            INSERT INTO employees (id, name, email, department, salary)
            VALUES (:id, :name, :email, :dept, :salary)
            """,
            {
                'id': emp_id,
                'name': name,
                'email': email,
                'dept': department,
                'salary': salary
            }
        )
        return result['rowcount'] > 0

    async def get_employee(self, emp_id):
        """Get employee by ID"""
        result = await self.client.execute_query(
            "SELECT * FROM employees WHERE id = :id",
            {'id': emp_id}
        )
        if result['rows']:
            return dict(zip(result['columns'], result['rows'][0]))
        return None

    async def update_salary(self, emp_id, new_salary):
        """Update employee salary"""
        result = await self.client.execute_query(
            "UPDATE employees SET salary = :salary WHERE id = :id",
            {'salary': new_salary, 'id': emp_id}
        )
        return result['rowcount'] > 0

    async def delete_employee(self, emp_id):
        """Delete employee"""
        result = await self.client.execute_query(
            "DELETE FROM employees WHERE id = :id",
            {'id': emp_id}
        )
        return result['rowcount'] > 0

    async def list_employees(self):
        """List all employees"""
        result = await self.client.execute_query(
            "SELECT * FROM employees ORDER BY name"
        )
        return [dict(zip(result['columns'], row)) for row in result['rows']]

# Usage
async def main():
    config = ConnectionConfig(
        host='localhost',
        port=1521,
        database='freepdb1',
        username='myuser',
        password='mypassword'
    )

    manager = EmployeeManager(config)

    try:
        await manager.connect()

        # Create table
        await manager.create_table()

        # Add employees
        await manager.add_employee(1, 'Alice Johnson', 'alice@example.com', 'Engineering', 85000)
        await manager.add_employee(2, 'Bob Smith', 'bob@example.com', 'Sales', 65000)

        # Get employee
        emp = await manager.get_employee(1)
        print(f"Employee: {emp}")

        # Update salary
        await manager.update_salary(1, 90000)

        # List all
        employees = await manager.list_employees()
        for emp in employees:
            print(f"{emp['NAME']}: ${emp['SALARY']}")

        # Delete employee
        await manager.delete_employee(2)

    except MCPClientError as e:
        print(f"Database error: {e.message}")
    finally:
        await manager.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
```

## Additional Resources

- [Oracle python-oracledb Documentation](https://python-oracledb.readthedocs.io/)
- [AI-Shell MCP Client API](../developer/MCP_CLIENT_API.md)
- [Database Operations Guide](../guides/DATABASE_OPERATIONS.md)
- [Oracle Integration Tests](../../tests/integration/test_oracle_integration.py)

## Version Information

- **AI-Shell**: 2.0.0+
- **python-oracledb**: 2.0.0
- **Oracle Database**: 11g, 12c, 18c, 19c, 21c, 23c (Free)
- **Thin Mode**: No Oracle Client required
