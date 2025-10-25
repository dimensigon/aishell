#!/bin/bash
# MySQL Database Setup Script

echo "Setting up MySQL Database for AIShell..."

# Configuration
MYSQL_HOST="${MYSQL_HOST:-51.15.90.27}"
MYSQL_PORT="${MYSQL_PORT:-3307}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-MyMySQLPass123}"
MYSQL_USER="root"

# Test connection
echo "Testing MySQL connection..."
mysql -h ${MYSQL_HOST} -P ${MYSQL_PORT} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -e "SELECT 'MySQL Connection Successful' as status;"

if [ $? -eq 0 ]; then
    echo "✓ MySQL connection successful"
else
    echo "✗ MySQL connection failed"
    exit 1
fi

# Create test database
echo "Creating test database..."
mysql -h ${MYSQL_HOST} -P ${MYSQL_PORT} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} <<EOF
DROP DATABASE IF EXISTS aishell_test;
CREATE DATABASE aishell_test;
USE aishell_test;
EOF

# Create test user
echo "Creating test user..."
mysql -h ${MYSQL_HOST} -P ${MYSQL_PORT} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} <<EOF
DROP USER IF EXISTS 'aishell_test'@'%';
CREATE USER 'aishell_test'@'%' IDENTIFIED BY 'test123';
GRANT ALL PRIVILEGES ON aishell_test.* TO 'aishell_test'@'%';
FLUSH PRIVILEGES;
EOF

echo "MySQL Database setup complete!"
