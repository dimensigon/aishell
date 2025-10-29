#!/bin/bash
# Test installation script for ai-shell-py

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}AI-Shell Python Package Test${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Parse arguments
SOURCE="testpypi"
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --pypi)
            SOURCE="pypi"
            shift
            ;;
        --local)
            SOURCE="local"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "Usage: $0 [--pypi|--testpypi|--local] [--clean]"
            exit 1
            ;;
    esac
done

# Create test virtual environment
TEST_VENV="/tmp/ai-shell-py-test-$$"
echo -e "${YELLOW}[1/5]${NC} Creating test virtual environment..."
python3 -m venv "$TEST_VENV"
source "$TEST_VENV/bin/activate"
echo -e "${GREEN}✓${NC} Virtual environment created"

# Upgrade pip
echo -e "${YELLOW}[2/5]${NC} Upgrading pip..."
pip install --upgrade pip > /dev/null
echo -e "${GREEN}✓${NC} Pip upgraded"

# Install package
echo -e "${YELLOW}[3/5]${NC} Installing ai-shell-py from ${SOURCE}..."
case $SOURCE in
    pypi)
        pip install ai-shell-py
        ;;
    testpypi)
        pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ai-shell-py
        ;;
    local)
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
        pip install -e "$PACKAGE_DIR"
        ;;
esac
echo -e "${GREEN}✓${NC} Package installed"

# Test import
echo -e "${YELLOW}[4/5]${NC} Testing package import..."
python3 << 'EOF'
import sys

try:
    import ai_shell_py
    print(f"✓ ai_shell_py imported successfully")
    print(f"  Version: {ai_shell_py.__version__}")
    print(f"  Package: {ai_shell_py.PACKAGE_NAME}")

    # Test submodules
    try:
        from ai_shell_py import database
        print("✓ database submodule available")
    except ImportError as e:
        print(f"⚠ database submodule not available: {e}")

    try:
        from ai_shell_py import mcp_clients
        print("✓ mcp_clients submodule available")
    except ImportError as e:
        print(f"⚠ mcp_clients submodule not available: {e}")

    try:
        from ai_shell_py import agents
        print("✓ agents submodule available")
    except ImportError as e:
        print(f"⚠ agents submodule not available: {e}")

    sys.exit(0)
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Import tests passed"
else
    echo -e "${RED}✗${NC} Import tests failed"
    deactivate
    if [ "$CLEAN" = true ]; then
        rm -rf "$TEST_VENV"
    fi
    exit 1
fi

# List installed files
echo -e "${YELLOW}[5/5]${NC} Checking installed files..."
pip show -f ai-shell-py | tail -20

# Cleanup
echo ""
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""

deactivate

if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning up test environment...${NC}"
    rm -rf "$TEST_VENV"
    echo -e "${GREEN}✓${NC} Cleanup complete"
else
    echo -e "${YELLOW}Test environment preserved at: ${TEST_VENV}${NC}"
    echo -e "To activate: ${BLUE}source ${TEST_VENV}/bin/activate${NC}"
    echo -e "To clean up: ${BLUE}rm -rf ${TEST_VENV}${NC}"
fi

echo ""
