#!/bin/bash
################################################################################
# AI-Shell Production Environment Validation Script
#
# Purpose: Validates production environment readiness before deployment
# Usage: bash scripts/validate-production.sh
# Version: 1.0.0
# Last Updated: October 29, 2025
#
# This script performs comprehensive pre-deployment validation including:
# - System requirements verification
# - Environment variable validation
# - Database connectivity testing
# - SSL certificate validation
# - Disk space and resource checks
# - Security configuration validation
# - Dependency verification
# - Health check endpoint testing
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Log file
LOG_FILE="/tmp/ai-shell-validation-$(date +%Y%m%d-%H%M%S).log"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

print_check() {
    echo -n "[$((TOTAL_CHECKS + 1))] $1... "
    echo "[CHECK] $1" >> "$LOG_FILE"
}

check_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    echo "[PASS] $1" >> "$LOG_FILE"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_fail() {
    echo -e "${RED}✗ FAIL${NC}"
    echo "[FAIL] $1" >> "$LOG_FILE"
    if [ -n "${2:-}" ]; then
        echo -e "  ${RED}Error: $2${NC}"
        echo "  Error: $2" >> "$LOG_FILE"
    fi
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}"
    echo "[WARN] $1" >> "$LOG_FILE"
    if [ -n "${2:-}" ]; then
        echo -e "  ${YELLOW}Warning: $2${NC}"
        echo "  Warning: $2" >> "$LOG_FILE"
    fi
    ((WARNING_CHECKS++))
    ((TOTAL_CHECKS++))
}

################################################################################
# Validation Functions
################################################################################

# 1. System Requirements
validate_system_requirements() {
    print_header "System Requirements Validation"

    # Check Node.js version
    print_check "Node.js version (18+)"
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>/dev/null | sed 's/v//' | cut -d. -f1 || echo "0")
        if [ "$NODE_VERSION" -ge 18 ] 2>/dev/null; then
            check_pass "Node.js v$(node --version) detected"
        else
            check_fail "Node.js version" "Version $NODE_VERSION detected, v18+ required"
        fi
    else
        check_fail "Node.js not found" "Node.js is not installed"
    fi

    # Check npm
    print_check "npm installed"
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(timeout 3 npm --version 2>/dev/null || echo "unknown")
        check_pass "npm v${NPM_VERSION} detected"
    else
        check_fail "npm not found" "npm is not installed"
    fi

    # Check OS
    print_check "Operating System"
    OS=$(uname -s)
    if [ "$OS" = "Linux" ]; then
        check_pass "Linux detected"
    else
        check_warn "Operating System" "Non-Linux OS detected: $OS"
    fi

    # Check memory (requires at least 4GB)
    print_check "System memory (4GB minimum)"
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "0")
        if [ "$TOTAL_MEM" -ge 4 ] 2>/dev/null; then
            check_pass "${TOTAL_MEM}GB RAM detected"
        else
            check_fail "Insufficient memory" "${TOTAL_MEM}GB detected, 4GB minimum required"
        fi
    else
        check_warn "Memory check" "Cannot verify memory (free command not available)"
    fi

    # Check disk space (requires at least 20GB free)
    print_check "Disk space (20GB minimum)"
    if command -v df &> /dev/null; then
        DISK_AVAIL=$(df -BG / 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo "0")
        if [ "$DISK_AVAIL" -ge 20 ] 2>/dev/null; then
            check_pass "${DISK_AVAIL}GB available"
        else
            check_fail "Insufficient disk space" "${DISK_AVAIL}GB available, 20GB minimum required"
        fi
    else
        check_warn "Disk space check" "Cannot verify disk space"
    fi
}

# 2. Environment Variables
validate_environment_variables() {
    print_header "Environment Variables Validation"

    # Critical variables
    REQUIRED_VARS=(
        "ANTHROPIC_API_KEY"
        "DATABASE_URL"
        "NODE_ENV"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        print_check "Required variable: $var"
        if [ -n "${!var:-}" ]; then
            # Mask sensitive values in output
            if [[ "$var" == *"KEY"* ]] || [[ "$var" == *"PASSWORD"* ]]; then
                check_pass "$var is set (value masked)"
            else
                check_pass "$var is set"
            fi
        else
            check_fail "$var not set" "Critical environment variable missing"
        fi
    done

    # Recommended variables
    RECOMMENDED_VARS=(
        "POSTGRES_HOST"
        "POSTGRES_PORT"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "LOG_LEVEL"
    )

    for var in "${RECOMMENDED_VARS[@]}"; do
        print_check "Recommended variable: $var"
        if [ -n "${!var:-}" ]; then
            check_pass "$var is set"
        else
            check_warn "$var not set" "Recommended variable missing"
        fi
    done

    # Check NODE_ENV is production
    print_check "NODE_ENV is production"
    if [ "${NODE_ENV:-}" = "production" ]; then
        check_pass "NODE_ENV=production"
    else
        check_warn "NODE_ENV" "Expected 'production', found '${NODE_ENV:-not set}'"
    fi
}

# 3. Database Connectivity
validate_database_connectivity() {
    print_header "Database Connectivity Validation"

    # Check PostgreSQL client
    print_check "PostgreSQL client (psql)"
    if command -v psql &> /dev/null; then
        check_pass "psql v$(psql --version | awk '{print $3}') detected"
    else
        check_warn "psql not found" "PostgreSQL client tools not installed"
    fi

    # Test database connection (if DATABASE_URL is set)
    print_check "Database connection test"
    if [ -n "${DATABASE_URL:-}" ]; then
        if command -v psql &> /dev/null; then
            if timeout 5 psql "${DATABASE_URL}" -c "SELECT 1;" &> /dev/null 2>&1; then
                check_pass "Database connection successful"
            else
                check_warn "Database connection failed" "Cannot connect (expected if DB not configured yet)"
            fi
        else
            check_warn "Database connection" "Cannot test (psql not available)"
        fi
    else
        check_warn "Database connection" "DATABASE_URL not set, skipping test"
    fi

    # Test PostgreSQL connection (if POSTGRES variables set)
    print_check "PostgreSQL direct connection"
    if [ -n "${POSTGRES_HOST:-}" ] && [ -n "${POSTGRES_USER:-}" ] && [ -n "${POSTGRES_DB:-}" ]; then
        if command -v psql &> /dev/null; then
            if timeout 5 PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT version();" &> /dev/null 2>&1; then
                check_pass "PostgreSQL connection successful"
            else
                check_warn "PostgreSQL connection failed" "Cannot connect (expected if DB not configured yet)"
            fi
        else
            check_warn "PostgreSQL connection" "Cannot test (psql not available)"
        fi
    else
        check_warn "PostgreSQL connection" "PostgreSQL variables not set, skipping test"
    fi
}

# 4. SSL/TLS Certificates
validate_ssl_certificates() {
    print_header "SSL/TLS Certificate Validation"

    # Check if SSL directory exists
    SSL_DIR="/etc/ai-shell/ssl"
    print_check "SSL certificate directory"
    if [ -d "$SSL_DIR" ]; then
        check_pass "SSL directory exists: $SSL_DIR"

        # Check for certificate files
        print_check "SSL certificate files"
        if [ -f "$SSL_DIR/server.crt" ] && [ -f "$SSL_DIR/server.key" ]; then
            check_pass "Certificate and key files found"

            # Verify certificate validity
            print_check "Certificate validity"
            if command -v openssl &> /dev/null; then
                EXPIRY=$(openssl x509 -enddate -noout -in "$SSL_DIR/server.crt" 2>/dev/null | cut -d= -f2)
                EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo 0)
                NOW_EPOCH=$(date +%s)
                DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

                if [ "$DAYS_UNTIL_EXPIRY" -gt 30 ]; then
                    check_pass "Certificate valid for $DAYS_UNTIL_EXPIRY days"
                elif [ "$DAYS_UNTIL_EXPIRY" -gt 0 ]; then
                    check_warn "Certificate expiring soon" "Valid for only $DAYS_UNTIL_EXPIRY days"
                else
                    check_fail "Certificate expired" "Certificate is no longer valid"
                fi
            else
                check_warn "Certificate validity" "Cannot verify (openssl not available)"
            fi
        else
            check_warn "Certificate files" "Certificate or key file missing"
        fi
    else
        check_warn "SSL directory" "SSL directory not found: $SSL_DIR"
    fi
}

# 5. Disk Space and Resources
validate_resources() {
    print_header "Resource Availability Validation"

    # Check disk space on critical paths
    CRITICAL_PATHS=(
        "/opt/ai-shell"
        "/var/log/ai-shell"
        "/var/backups/ai-shell"
        "/etc/ai-shell"
    )

    for path in "${CRITICAL_PATHS[@]}"; do
        print_check "Disk space for $path"
        if [ -d "$path" ]; then
            AVAIL=$(df -BG "$path" | awk 'NR==2 {print $4}' | sed 's/G//')
            if [ "$AVAIL" -ge 10 ]; then
                check_pass "${AVAIL}GB available"
            else
                check_warn "Low disk space" "Only ${AVAIL}GB available"
            fi
        else
            check_warn "Directory not found" "$path does not exist"
        fi
    done

    # Check inode usage
    print_check "Inode usage"
    if command -v df &> /dev/null; then
        INODE_USAGE=$(df -i / | awk 'NR==2 {print $5}' | sed 's/%//')
        if [ "$INODE_USAGE" -lt 80 ]; then
            check_pass "Inode usage: ${INODE_USAGE}%"
        else
            check_warn "High inode usage" "${INODE_USAGE}% inodes used"
        fi
    else
        check_warn "Inode check" "Cannot verify inode usage"
    fi

    # Check CPU cores
    print_check "CPU cores (2+ recommended)"
    if command -v nproc &> /dev/null; then
        CPU_CORES=$(nproc)
        if [ "$CPU_CORES" -ge 2 ]; then
            check_pass "$CPU_CORES cores detected"
        else
            check_warn "CPU cores" "Only $CPU_CORES core detected, 2+ recommended"
        fi
    else
        check_warn "CPU check" "Cannot verify CPU cores"
    fi
}

# 6. Security Configuration
validate_security() {
    print_header "Security Configuration Validation"

    # Check vault directory
    print_check "Vault directory"
    VAULT_DIR="/etc/ai-shell"
    if [ -d "$VAULT_DIR" ]; then
        check_pass "Vault directory exists"

        # Check vault encryption key
        print_check "Vault encryption key"
        if [ -f "$VAULT_DIR/vault.key" ]; then
            # Check file permissions (should be 400)
            PERMS=$(stat -c %a "$VAULT_DIR/vault.key" 2>/dev/null || stat -f %Lp "$VAULT_DIR/vault.key" 2>/dev/null || echo "unknown")
            if [ "$PERMS" = "400" ]; then
                check_pass "Vault key exists with correct permissions (400)"
            else
                check_warn "Vault key permissions" "Found $PERMS, should be 400"
            fi
        else
            check_warn "Vault key" "Vault encryption key not found"
        fi
    else
        check_warn "Vault directory" "Vault directory not found: $VAULT_DIR"
    fi

    # Check audit log directory
    print_check "Audit log directory"
    AUDIT_DIR="/var/log/ai-shell"
    if [ -d "$AUDIT_DIR" ]; then
        check_pass "Audit log directory exists"

        # Check if writable
        if [ -w "$AUDIT_DIR" ]; then
            check_pass "Audit directory is writable"
        else
            check_fail "Audit directory not writable" "Cannot write to $AUDIT_DIR"
        fi
    else
        check_warn "Audit directory" "Audit log directory not found: $AUDIT_DIR"
    fi

    # Check backup directory
    print_check "Backup directory"
    BACKUP_DIR="/var/backups/ai-shell"
    if [ -d "$BACKUP_DIR" ]; then
        check_pass "Backup directory exists"

        # Check if writable
        if [ -w "$BACKUP_DIR" ]; then
            check_pass "Backup directory is writable"
        else
            check_fail "Backup directory not writable" "Cannot write to $BACKUP_DIR"
        fi
    else
        check_warn "Backup directory" "Backup directory not found: $BACKUP_DIR"
    fi
}

# 7. npm Dependencies
validate_dependencies() {
    print_header "Dependency Validation"

    # Check if package.json exists
    print_check "package.json exists"
    if [ -f "package.json" ]; then
        check_pass "package.json found"

        # Check if node_modules exists
        print_check "node_modules directory"
        if [ -d "node_modules" ]; then
            check_pass "Dependencies installed"

            # Run npm audit
            print_check "npm security audit"
            if command -v npm &> /dev/null; then
                AUDIT_OUTPUT=$(timeout 30 npm audit --production --audit-level=high 2>&1 || echo "audit_timeout")
                if echo "$AUDIT_OUTPUT" | grep -q "audit_timeout"; then
                    check_warn "npm audit timeout" "Audit took too long (skipped)"
                elif echo "$AUDIT_OUTPUT" | grep -q "found 0"; then
                    check_pass "No high/critical vulnerabilities found"
                else
                    VULN_COUNT=$(echo "$AUDIT_OUTPUT" | grep -oP '\d+(?= vulnerabilities)' | head -1 || echo "unknown")
                    check_warn "Security vulnerabilities" "$VULN_COUNT vulnerabilities found (run 'npm audit' for details)"
                fi
            else
                check_warn "npm audit" "Cannot run audit (npm not available)"
            fi
        else
            check_fail "Dependencies not installed" "Run 'npm ci --production' to install"
        fi
    else
        check_fail "package.json not found" "Not in AI-Shell project directory"
    fi

    # Check if build directory exists
    print_check "Build artifacts (dist/)"
    if [ -d "dist" ]; then
        check_pass "Build directory exists"

        # Check key build files
        REQUIRED_FILES=(
            "dist/cli/index.js"
            "dist/mcp/server.js"
        )

        ALL_EXIST=true
        for file in "${REQUIRED_FILES[@]}"; do
            if [ ! -f "$file" ]; then
                ALL_EXIST=false
                break
            fi
        done

        if $ALL_EXIST; then
            check_pass "All required build files exist"
        else
            check_warn "Build files" "Some required files missing (run 'npm run build')"
        fi
    else
        check_warn "Build directory" "Build not found (run 'npm run build')"
    fi
}

# 8. Health Check Endpoint
validate_health_check() {
    print_header "Health Check Endpoint Validation"

    # Check if service is running
    print_check "AI-Shell service status"
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet ai-shell 2>/dev/null; then
            check_pass "AI-Shell service is running"

            # Test health endpoint
            print_check "Health check endpoint"
            if command -v curl &> /dev/null; then
                HEALTH_RESPONSE=$(curl -sf http://localhost:8080/health 2>/dev/null || echo "")
                if [ -n "$HEALTH_RESPONSE" ]; then
                    STATUS=$(echo "$HEALTH_RESPONSE" | grep -oP '"status":"\K[^"]+' || echo "unknown")
                    if [ "$STATUS" = "healthy" ]; then
                        check_pass "Health endpoint responding (status: healthy)"
                    else
                        check_warn "Health endpoint" "Status: $STATUS"
                    fi
                else
                    check_warn "Health endpoint" "No response from http://localhost:8080/health"
                fi
            else
                check_warn "Health check" "Cannot test (curl not available)"
            fi
        else
            check_warn "Service not running" "AI-Shell service is not active (expected for fresh install)"
        fi
    else
        check_warn "Service check" "Cannot verify service status (systemctl not available)"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "AI-Shell Production Environment Validation"
    echo "Version: 1.0.0"
    echo "Date: $(date)"
    echo "Hostname: $(hostname)"
    echo "User: $(whoami)"
    echo ""
    echo "Validation results will be saved to: $LOG_FILE"

    # Initialize log file
    cat > "$LOG_FILE" <<EOF
AI-Shell Production Environment Validation
Generated: $(date)
Hostname: $(hostname)
User: $(whoami)
Node Version: $(node --version 2>/dev/null || echo "not installed")
npm Version: $(npm --version 2>/dev/null || echo "not installed")

================================ VALIDATION RESULTS ================================

EOF

    # Run all validation checks
    validate_system_requirements
    validate_environment_variables
    validate_database_connectivity
    validate_ssl_certificates
    validate_resources
    validate_security
    validate_dependencies
    validate_health_check

    # Print summary
    print_header "Validation Summary"
    echo ""
    echo "Total Checks:   $TOTAL_CHECKS"
    echo -e "${GREEN}Passed:         $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings:       $WARNING_CHECKS${NC}"
    echo -e "${RED}Failed:         $FAILED_CHECKS${NC}"
    echo ""

    # Calculate pass rate
    if [ "$TOTAL_CHECKS" -gt 0 ]; then
        PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
        echo "Pass Rate: ${PASS_RATE}%"
        echo ""
    fi

    # Write summary to log
    cat >> "$LOG_FILE" <<EOF

================================ VALIDATION SUMMARY ================================

Total Checks:   $TOTAL_CHECKS
Passed:         $PASSED_CHECKS
Warnings:       $WARNING_CHECKS
Failed:         $FAILED_CHECKS
Pass Rate:      ${PASS_RATE}%

EOF

    # Determine overall status
    if [ "$FAILED_CHECKS" -eq 0 ] && [ "$WARNING_CHECKS" -eq 0 ]; then
        echo -e "${GREEN}✓ VALIDATION PASSED${NC}"
        echo "Environment is ready for production deployment"
        echo "RESULT: VALIDATION PASSED - Environment ready for production" >> "$LOG_FILE"
        exit 0
    elif [ "$FAILED_CHECKS" -eq 0 ]; then
        echo -e "${YELLOW}⚠ VALIDATION PASSED WITH WARNINGS${NC}"
        echo "Environment is mostly ready, but some warnings were detected"
        echo "Review warnings above and address before production deployment"
        echo "RESULT: PASSED WITH WARNINGS - Review warnings before deployment" >> "$LOG_FILE"
        exit 0
    else
        echo -e "${RED}✗ VALIDATION FAILED${NC}"
        echo "Environment is NOT ready for production deployment"
        echo "Fix critical failures above before proceeding"
        echo "RESULT: VALIDATION FAILED - Critical issues must be resolved" >> "$LOG_FILE"
        exit 1
    fi
}

# Run main function
main
