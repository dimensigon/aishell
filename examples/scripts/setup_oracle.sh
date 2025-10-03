#!/bin/bash
# AI-Shell Oracle Database Setup Script
# Sets up Oracle database connection using MCP thin client (no Oracle client required)

set -e

echo "=== AI-Shell Oracle Database Setup ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AI-Shell is installed
if ! command -v ai-shell &> /dev/null; then
    echo -e "${RED}Error: AI-Shell is not installed${NC}"
    echo "Please install AI-Shell first: pip install ai-shell"
    exit 1
fi

# Check if Python cx_Oracle is installed
if ! python3 -c "import cx_Oracle" &> /dev/null; then
    echo -e "${YELLOW}Installing cx_Oracle (thin mode)...${NC}"
    pip install cx-Oracle==8.3.0
fi

# Prompt for connection details
echo -e "${GREEN}Enter Oracle connection details:${NC}"
echo ""

read -p "Connection name (e.g., prod_oracle): " CONN_NAME
read -p "Username: " USERNAME
read -sp "Password: " PASSWORD
echo ""
read -p "Host: " HOST
read -p "Port (default 1521): " PORT
PORT=${PORT:-1521}

# Service name or SID?
echo ""
echo "Connection type:"
echo "  1) Service Name"
echo "  2) SID"
read -p "Select (1 or 2): " CONN_TYPE

if [ "$CONN_TYPE" == "1" ]; then
    read -p "Service Name: " SERVICE_NAME
    DSN_TYPE="service_name"
    DSN_VALUE="$SERVICE_NAME"
else
    read -p "SID: " SID
    DSN_TYPE="sid"
    DSN_VALUE="$SID"
fi

# Test connection
echo ""
echo -e "${YELLOW}Testing connection...${NC}"

python3 << EOF
import cx_Oracle
import sys

try:
    # Enable thin mode - no Oracle client required
    cx_Oracle.init_oracle_client(lib_dir=None)

    # Build DSN
    if "$DSN_TYPE" == "service_name":
        dsn = cx_Oracle.makedsn("$HOST", $PORT, service_name="$DSN_VALUE")
    else:
        dsn = cx_Oracle.makedsn("$HOST", $PORT, sid="$DSN_VALUE")

    # Test connection
    connection = cx_Oracle.connect("$USERNAME", "$PASSWORD", dsn)
    cursor = connection.cursor()

    # Get database version
    cursor.execute("SELECT banner FROM v\$version WHERE ROWNUM = 1")
    version = cursor.fetchone()[0]

    print(f"✓ Connection successful!")
    print(f"  Database: {version}")

    # Get schema stats
    cursor.execute("SELECT COUNT(*) FROM user_tables")
    table_count = cursor.fetchone()[0]
    print(f"  Tables: {table_count}")

    cursor.close()
    connection.close()
    sys.exit(0)

except Exception as e:
    print(f"✗ Connection failed: {e}", file=sys.stderr)
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Connection test failed. Please check your credentials.${NC}"
    exit 1
fi

# Add to AI-Shell vault
echo ""
echo -e "${GREEN}Adding credentials to AI-Shell vault...${NC}"

ai-shell << EOF
vault add ${CONN_NAME} --type database
${USERNAME}
${PASSWORD}
${HOST}
${PORT}
${DSN_VALUE}
${DSN_TYPE}
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
    type: oracle
    credentials: \$vault.${CONN_NAME}
    options:
      thin_mode: true
      events: true
      preload_objects: true
EOF

echo ""
echo -e "${GREEN}✓ Oracle connection '${CONN_NAME}' configured successfully!${NC}"
echo ""
echo "To connect:"
echo "  ai-shell"
echo "  AI\$ > db connect ${CONN_NAME}"
echo ""
echo "To test query:"
echo "  AI\$ > SELECT * FROM user_tables;"
echo ""
echo -e "${YELLOW}Note: Using thin mode - no Oracle Instant Client required${NC}"
