# Oracle Database Support

AI-Shell provides comprehensive Oracle database support using **python-oracledb** in thin mode - no Oracle Instant Client installation required!

## 📚 Documentation

### Quick Links

- **[Oracle Support Guide](./ORACLE_SUPPORT_GUIDE.md)** - Complete user guide with examples
- **[Implementation Summary](./ORACLE_IMPLEMENTATION_SUMMARY.md)** - Technical details and status
- **[Basic Example](../../examples/oracle/basic_connection.py)** - Working code example
- **[Advanced Example](../../examples/oracle/advanced_features.py)** - Advanced features demo

## 🚀 Quick Start

### Installation

```bash
# Install AI-Shell with Oracle support
pip install ai-shell-py[oracle]

# Or install all database drivers
pip install ai-shell-py[all-databases]
```

### Basic Usage

```python
import asyncio
from ai_shell_py.mcp_clients import OracleClient, ConnectionConfig

async def main():
    client = OracleClient()

    # Connect (no Oracle Client required!)
    await client.connect(ConnectionConfig(
        host='localhost',
        port=1521,
        database='freepdb1',
        username='myuser',
        password='mypass'
    ))

    # Query data
    result = await client.execute_query("SELECT * FROM employees")
    print(f"Found {result['rowcount']} rows")

    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

## ✨ Key Features

- ✅ **Zero Dependencies** - Thin mode, no Oracle Instant Client required
- ✅ **Cross-Platform** - Works on Linux, macOS, Windows
- ✅ **Async/Await** - Full async operation support
- ✅ **CDB & PDB Support** - Connect to Container and Pluggable databases
- ✅ **100% Test Coverage** - Comprehensive unit and integration tests
- ✅ **Production Ready** - Complete error handling and monitoring

## 📖 Features Overview

### Supported Operations

| Operation | Status | Documentation |
|-----------|--------|---------------|
| Connect/Disconnect | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#connection-methods) |
| SELECT Queries | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#select-queries) |
| INSERT/UPDATE/DELETE | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#insert-update-delete) |
| DDL (CREATE/ALTER/DROP) | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#ddl-operations) |
| Parameterized Queries | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#parameterized-queries) |
| Table Metadata | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#table-metadata) |
| Health Checks | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#health-checks) |
| Concurrent Queries | ✅ | [Guide](./ORACLE_SUPPORT_GUIDE.md#concurrent-queries) |

### Supported Oracle Versions

- ✅ Oracle 23c (Free)
- ✅ Oracle 21c
- ✅ Oracle 19c
- ✅ Oracle 18c
- ✅ Oracle 12c (12.1, 12.2)
- ✅ Oracle 11g (11.2.0.4+)

## 🔧 Configuration Examples

### CDB Connection (Container Database)

```python
config = ConnectionConfig(
    host='localhost',
    port=1521,
    database='free',  # CDB service name
    username='SYS',
    password='password',
    extra_params={'mode': 'SYSDBA'}  # For SYS user
)
```

### PDB Connection (Pluggable Database)

```python
config = ConnectionConfig(
    host='localhost',
    port=1521,
    database='freepdb1',  # PDB service name
    username='myuser',
    password='mypass'
)
```

## 📊 Examples

### Basic CRUD Operations

```python
# INSERT
await client.execute_query(
    "INSERT INTO users (id, name, email) VALUES (:id, :name, :email)",
    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
)

# SELECT
result = await client.execute_query(
    "SELECT * FROM users WHERE id = :id",
    {'id': 1}
)

# UPDATE
await client.execute_query(
    "UPDATE users SET email = :email WHERE id = :id",
    {'email': 'newemail@example.com', 'id': 1}
)

# DELETE
await client.execute_query(
    "DELETE FROM users WHERE id = :id",
    {'id': 1}
)
```

### DDL Operations

```python
# CREATE TABLE
await client.execute_ddl("""
    CREATE TABLE products (
        id NUMBER PRIMARY KEY,
        name VARCHAR2(100) NOT NULL,
        price NUMBER(10,2),
        created_at DATE DEFAULT SYSDATE
    )
""")

# CREATE INDEX
await client.execute_ddl(
    "CREATE INDEX idx_products_name ON products(name)"
)

# DROP TABLE
await client.execute_ddl("DROP TABLE products")
```

### Table Metadata

```python
# Get table structure
info = await client.get_table_info('employees')
print(f"Table: {info['table_name']}")
for col in info['columns']:
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    print(f"  {col['name']}: {col['type']}({col['length']}) {nullable}")

# List all tables
tables = await client.get_table_list()
print(f"Found {len(tables)} tables")
```

## 🧪 Testing

### Run Unit Tests

```bash
# Run all Oracle unit tests
pytest tests/mcp_clients/test_oracle_thin.py -v

# Run specific test
pytest tests/mcp_clients/test_oracle_thin.py::TestOracleConnection::test_connect_success_cdb -v
```

### Run Integration Tests

```bash
# Requires Oracle database running on localhost:1521
pytest tests/integration/test_oracle_integration.py -v -m integration
```

## 🛠️ Development

### Project Structure

```
src/mcp_clients/
├── base.py              # Base MCP protocol
└── oracle_client.py     # Oracle implementation

python-package/ai_shell_py/mcp_clients/
├── base.py              # Package version
└── oracle_client.py     # Package version

tests/
├── mcp_clients/
│   └── test_oracle_thin.py          # Unit tests (43 tests)
└── integration/
    └── test_oracle_integration.py   # Integration tests (30+ tests)

docs/oracle/
├── README.md                         # This file
├── ORACLE_SUPPORT_GUIDE.md          # User guide
└── ORACLE_IMPLEMENTATION_SUMMARY.md # Technical details

examples/oracle/
├── basic_connection.py              # Basic example
└── advanced_features.py             # Advanced example
```

### Code Examples Location

```
examples/
├── oracle/
│   ├── basic_connection.py     # Basic connection example (250+ lines)
│   └── advanced_features.py    # Advanced features (400+ lines)
└── scripts/
    └── setup_oracle.sh         # Setup script
```

## 🐛 Troubleshooting

### Common Issues

#### Connection Timeout

```python
# Increase timeout
config.extra_params = {'timeout': 60}
```

#### Table Not Found (ORA-00942)

```python
# Oracle stores table names in UPPERCASE
table_info = await client.get_table_info('EMPLOYEES')  # Not 'employees'
```

#### Invalid Credentials (ORA-01017)

```python
# For SYS user, SYSDBA mode is required
config.extra_params = {'mode': 'SYSDBA'}
```

See the [Troubleshooting Guide](./ORACLE_SUPPORT_GUIDE.md#troubleshooting) for more solutions.

## 📞 Support

- **Documentation**: [Oracle Support Guide](./ORACLE_SUPPORT_GUIDE.md)
- **Examples**: [examples/oracle/](../../examples/oracle/)
- **Tests**: [tests/mcp_clients/test_oracle_thin.py](../../tests/mcp_clients/test_oracle_thin.py)
- **Issues**: [GitHub Issues](https://github.com/dimensigon/aishell/issues)

## 📚 Additional Resources

- [python-oracledb Documentation](https://python-oracledb.readthedocs.io/)
- [Oracle Database Documentation](https://docs.oracle.com/database/)
- [AI-Shell MCP Client API](../developer/MCP_CLIENT_API.md)
- [Database Operations Guide](../guides/DATABASE_OPERATIONS.md)

## 📝 License

This Oracle integration is part of AI-Shell and is licensed under the MIT License.

---

**Built with ❤️ for developers who need reliable Oracle connectivity without the hassle of Oracle Client installation**
