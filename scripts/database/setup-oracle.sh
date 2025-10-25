#!/bin/bash
# Oracle Database Setup Script

echo "Setting up Oracle Database for AIShell..."

# Configuration
ORACLE_HOST="${ORACLE_HOST:-51.15.90.27}"
ORACLE_PORT="${ORACLE_PORT:-1521}"
ORACLE_PASSWORD="${ORACLE_PASSWORD:-MyOraclePass123}"

# Test CDB$ROOT connection
echo "Testing CDB\$ROOT connection..."
sqlplus -S SYS/${ORACLE_PASSWORD}@${ORACLE_HOST}:${ORACLE_PORT}/free as SYSDBA <<EOF
SELECT 'CDB\$ROOT Connection Successful' as status FROM dual;
EXIT;
EOF

if [ $? -eq 0 ]; then
    echo "✓ CDB\$ROOT connection successful"
else
    echo "✗ CDB\$ROOT connection failed"
    exit 1
fi

# Test FREEPDB1 connection
echo "Testing FREEPDB1 connection..."
sqlplus -S SYS/${ORACLE_PASSWORD}@${ORACLE_HOST}:${ORACLE_PORT}/freepdb1 as SYSDBA <<EOF
SELECT 'FREEPDB1 Connection Successful' as status FROM dual;
EXIT;
EOF

if [ $? -eq 0 ]; then
    echo "✓ FREEPDB1 connection successful"
else
    echo "✗ FREEPDB1 connection failed"
    exit 1
fi

# Create test user in FREEPDB1
echo "Creating test user in FREEPDB1..."
sqlplus -S SYS/${ORACLE_PASSWORD}@${ORACLE_HOST}:${ORACLE_PORT}/freepdb1 as SYSDBA <<EOF
CREATE USER aishell_test IDENTIFIED BY test123;
GRANT CONNECT, RESOURCE TO aishell_test;
GRANT CREATE SESSION TO aishell_test;
GRANT CREATE TABLE TO aishell_test;
GRANT UNLIMITED TABLESPACE TO aishell_test;
EXIT;
EOF

echo "Oracle Database setup complete!"
