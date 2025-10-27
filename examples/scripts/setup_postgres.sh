#!/bin/bash
# AI-Shell PostgreSQL Database Setup Script
# Sets up PostgreSQL connection using pure Python client (no psql required)

set -e

echo "=== AI-Shell PostgreSQL Database Setup ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check AI-Shell
if ! command -v ai-shell &> /dev/null; then
    echo -e "${RED}Error: AI-Shell is not installed${NC}"
    exit 1
fi

# Check psycopg2
if ! python3 -c "import psycopg2" &> /dev/null; then
    echo -e "${YELLOW}Installing psycopg2...${NC}"
    pip install psycopg2-binary==2.9.9
fi

# Get connection details
echo -e "${GREEN}Enter PostgreSQL connection details:${NC}"
echo ""

read -p "Connection name (e.g., prod_postgres): " CONN_NAME
read -p "Username: " USERNAME
read -sp "Password: " PASSWORD
echo ""
read -p "Host: " HOST
read -p "Port (default 5432): " PORT
PORT=${PORT:-5432}
read -p "Database: " DATABASE

# SSL options
echo ""
echo "SSL Mode:"
echo "  1) disable"
echo "  2) prefer (default)"
echo "  3) require"
echo "  4) verify-ca"
echo "  5) verify-full"
read -p "Select (1-5, default 2): " SSL_CHOICE
SSL_CHOICE=${SSL_CHOICE:-2}

case $SSL_CHOICE in
    1) SSL_MODE="disable" ;;
    2) SSL_MODE="prefer" ;;
    3) SSL_MODE="require" ;;
    4) SSL_MODE="verify-ca" ;;
    5) SSL_MODE="verify-full" ;;
    *) SSL_MODE="prefer" ;;
esac

SSL_ROOT_CERT=""
if [ "$SSL_MODE" == "verify-ca" ] || [ "$SSL_MODE" == "verify-full" ]; then
    read -p "Path to CA certificate: " SSL_ROOT_CERT
fi

# Test connection
echo ""
echo -e "${YELLOW}Testing connection...${NC}"

python3 << EOF
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

try:
    # Connection parameters
    conn_params = {
        'dbname': '$DATABASE',
        'user': '$USERNAME',
        'password': '$PASSWORD',
        'host': '$HOST',
        'port': $PORT,
        'sslmode': '$SSL_MODE'
    }

    if '$SSL_ROOT_CERT':
        conn_params['sslrootcert'] = '$SSL_ROOT_CERT'

    # Connect
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get version
    cursor.execute("SELECT version()")
    version = cursor.fetchone()['version']
    print(f"✓ Connection successful!")
    print(f"  Database: {version.split(',')[0]}")

    # Get schema stats
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    table_count = cursor.fetchone()['count']
    print(f"  Public tables: {table_count}")

    cursor.close()
    conn.close()
    sys.exit(0)

except Exception as e:
    print(f"✗ Connection failed: {e}", file=sys.stderr)
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Connection test failed.${NC}"
    exit 1
fi

# Add to vault
echo ""
echo -e "${GREEN}Adding credentials to AI-Shell vault...${NC}"

ai-shell << EOF
vault add ${CONN_NAME} --type database
${USERNAME}
${PASSWORD}
${HOST}
${PORT}
${DATABASE}
exit
EOF

# Add connection config
CONFIG_FILE="$HOME/.ai-shell/connections.yaml"
mkdir -p "$HOME/.ai-shell"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "connections:" > "$CONFIG_FILE"
fi

# Append connection
cat >> "$CONFIG_FILE" << EOF

  ${CONN_NAME}:
    type: postgresql
    credentials: \$vault.${CONN_NAME}
    options:
      application_name: ai-shell
      sslmode: ${SSL_MODE}
$([ -n "$SSL_ROOT_CERT" ] && echo "      sslrootcert: ${SSL_ROOT_CERT}")
      preload_objects: true
EOF

echo ""
echo -e "${GREEN}✓ PostgreSQL connection '${CONN_NAME}' configured!${NC}"
echo ""
echo "To connect:"
echo "  AI\$ > db connect ${CONN_NAME}"
echo ""
echo "Example queries:"
echo "  AI\$ > SELECT * FROM pg_catalog.pg_tables LIMIT 10;"
echo "  AI\$ > #ai show me all tables in the public schema"
