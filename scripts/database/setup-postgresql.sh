#!/bin/bash
# PostgreSQL Database Setup Script

echo "Setting up PostgreSQL Database for AIShell..."

# Configuration
PG_HOST="${PG_HOST:-51.15.90.27}"
PG_PORT="${PG_PORT:-5432}"
PG_PASSWORD="${PG_PASSWORD:-MyPostgresPass123}"
PG_USER="postgres"
PG_DATABASE="postgres"

# Test connection
echo "Testing PostgreSQL connection..."
PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST} -p ${PG_PORT} -U ${PG_USER} -d ${PG_DATABASE} -c "SELECT 'PostgreSQL Connection Successful' as status;"

if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL connection successful"
else
    echo "✗ PostgreSQL connection failed"
    exit 1
fi

# Create test database
echo "Creating test database..."
PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST} -p ${PG_PORT} -U ${PG_USER} -d ${PG_DATABASE} <<EOF
DROP DATABASE IF EXISTS aishell_test;
CREATE DATABASE aishell_test;
\c aishell_test;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
EOF

echo "PostgreSQL Database setup complete!"
