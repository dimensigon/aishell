#!/bin/bash
# Quick script to run Oracle MCP client tests

echo "======================================"
echo "Oracle MCP Client Test Runner"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-asyncio"
    exit 1
fi

# Check if oracledb is installed
python -c "import oracledb" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: oracledb is not installed${NC}"
    echo "Install with: pip install oracledb"
    exit 1
fi

echo -e "${GREEN}Dependencies check: OK${NC}"
echo ""

# Menu
echo "Select test suite to run:"
echo "1) Unit tests only (no database required)"
echo "2) Integration tests only (requires Oracle database)"
echo "3) All tests (unit + integration)"
echo "4) Unit tests with coverage report"
echo "5) Quick smoke test"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo -e "${YELLOW}Running unit tests...${NC}"
        pytest tests/mcp_clients/test_oracle_thin.py -v
        ;;
    2)
        echo -e "${YELLOW}Running integration tests...${NC}"
        echo "Note: Oracle database must be running on localhost:1521"
        read -p "Press Enter to continue or Ctrl+C to cancel..."
        pytest tests/integration/test_oracle_integration.py -v -m integration
        ;;
    3)
        echo -e "${YELLOW}Running all tests...${NC}"
        pytest tests/mcp_clients/test_oracle_thin.py tests/integration/test_oracle_integration.py -v
        ;;
    4)
        echo -e "${YELLOW}Running unit tests with coverage...${NC}"
        pytest tests/mcp_clients/test_oracle_thin.py \
            --cov=src.mcp_clients.oracle_client \
            --cov-report=html \
            --cov-report=term-missing
        echo ""
        echo -e "${GREEN}Coverage report generated at: htmlcov/index.html${NC}"
        ;;
    5)
        echo -e "${YELLOW}Running smoke test...${NC}"
        pytest tests/mcp_clients/test_oracle_thin.py::TestOracleProtocolCompliance -v
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Test run completed!${NC}"
