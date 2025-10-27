#!/bin/bash

################################################################################
# Database Service Health Checker
################################################################################
# This script verifies the health of all database services:
# - Container status
# - Service connectivity
# - Authentication
# - Basic query execution
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
QUIET_MODE=false

# Health status tracking
ALL_HEALTHY=true

################################################################################
# Logging functions
################################################################################

log_info() {
    [[ "${QUIET_MODE}" == "true" ]] && return
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    [[ "${QUIET_MODE}" == "true" ]] && return
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[✗]${NC} $*" >&2
}

log_section() {
    [[ "${QUIET_MODE}" == "true" ]] && return
    echo ""
    echo -e "${BLUE}─────────────────────────────────────────${NC}"
    echo -e "${BLUE}  $*${NC}"
    echo -e "${BLUE}─────────────────────────────────────────${NC}"
}

################################################################################
# Health check functions
################################################################################

check_container_status() {
    local container_name="$1"
    local service_name="$2"

    log_info "Checking container: ${container_name}"

    # Check if container exists
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        log_error "${service_name}: Container not found"
        ALL_HEALTHY=false
        return 1
    fi

    # Check if container is running
    local status=$(docker inspect -f '{{.State.Status}}' "${container_name}" 2>/dev/null)
    if [[ "${status}" != "running" ]]; then
        log_error "${service_name}: Container is not running (status: ${status})"
        ALL_HEALTHY=false
        return 1
    fi

    # Check health status if available
    local health=$(docker inspect -f '{{.State.Health.Status}}' "${container_name}" 2>/dev/null || echo "none")
    if [[ "${health}" == "healthy" ]]; then
        log_success "${service_name}: Container is healthy"
        return 0
    elif [[ "${health}" == "starting" ]]; then
        log_warning "${service_name}: Container is starting..."
        ALL_HEALTHY=false
        return 1
    elif [[ "${health}" == "unhealthy" ]]; then
        log_error "${service_name}: Container is unhealthy"
        ALL_HEALTHY=false
        return 1
    else
        log_success "${service_name}: Container is running (no health check defined)"
        return 0
    fi
}

check_postgres() {
    local container_name="${1:-test-postgres}"
    local host="${2:-localhost}"
    local port="${3:-5432}"
    local user="${4:-test_user}"
    local password="${5:-test_password}"
    local database="${6:-test_db}"

    log_section "PostgreSQL Health Check"

    # Check container status
    if ! check_container_status "${container_name}" "PostgreSQL"; then
        return 1
    fi

    # Test connection and authentication
    log_info "Testing PostgreSQL connection..."
    if docker exec "${container_name}" psql -U "${user}" -d "${database}" -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "PostgreSQL: Connection successful"
    else
        log_error "PostgreSQL: Connection failed"
        ALL_HEALTHY=false
        return 1
    fi

    # Test basic query
    log_info "Testing PostgreSQL query execution..."
    local result=$(docker exec "${container_name}" psql -U "${user}" -d "${database}" -t -c "SELECT version();" 2>/dev/null | head -n 1)
    if [[ -n "${result}" ]]; then
        log_success "PostgreSQL: Query execution successful"
        [[ "${QUIET_MODE}" == "false" ]] && log_info "  Version: ${result}"
    else
        log_error "PostgreSQL: Query execution failed"
        ALL_HEALTHY=false
        return 1
    fi

    return 0
}

check_mysql() {
    local container_name="${1:-test-mysql}"
    local host="${2:-localhost}"
    local port="${3:-3306}"
    local user="${4:-test_user}"
    local password="${5:-test_password}"
    local database="${6:-test_db}"

    log_section "MySQL Health Check"

    # Check container status
    if ! check_container_status "${container_name}" "MySQL"; then
        return 1
    fi

    # Test connection and authentication
    log_info "Testing MySQL connection..."
    if docker exec "${container_name}" mysql -u"${user}" -p"${password}" -e "SELECT 1;" > /dev/null 2>&1; then
        log_success "MySQL: Connection successful"
    else
        log_error "MySQL: Connection failed"
        ALL_HEALTHY=false
        return 1
    fi

    # Test basic query
    log_info "Testing MySQL query execution..."
    local result=$(docker exec "${container_name}" mysql -u"${user}" -p"${password}" -N -e "SELECT VERSION();" 2>/dev/null)
    if [[ -n "${result}" ]]; then
        log_success "MySQL: Query execution successful"
        [[ "${QUIET_MODE}" == "false" ]] && log_info "  Version: ${result}"
    else
        log_error "MySQL: Query execution failed"
        ALL_HEALTHY=false
        return 1
    fi

    return 0
}

check_mongodb() {
    local container_name="${1:-test-mongodb}"
    local host="${2:-localhost}"
    local port="${3:-27017}"
    local user="${4:-test_user}"
    local password="${5:-test_password}"
    local database="${6:-test_db}"

    log_section "MongoDB Health Check"

    # Check container status
    if ! check_container_status "${container_name}" "MongoDB"; then
        return 1
    fi

    # Test connection and authentication
    log_info "Testing MongoDB connection..."
    if docker exec "${container_name}" mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        log_success "MongoDB: Connection successful"
    else
        log_error "MongoDB: Connection failed"
        ALL_HEALTHY=false
        return 1
    fi

    # Test basic query
    log_info "Testing MongoDB query execution..."
    local result=$(docker exec "${container_name}" mongosh --quiet --eval "db.version()" 2>/dev/null)
    if [[ -n "${result}" ]]; then
        log_success "MongoDB: Query execution successful"
        [[ "${QUIET_MODE}" == "false" ]] && log_info "  Version: ${result}"
    else
        log_error "MongoDB: Query execution failed"
        ALL_HEALTHY=false
        return 1
    fi

    return 0
}

check_redis() {
    local container_name="${1:-test-redis}"
    local host="${2:-localhost}"
    local port="${3:-6379}"

    log_section "Redis Health Check"

    # Check container status
    if ! check_container_status "${container_name}" "Redis"; then
        return 1
    fi

    # Test connection
    log_info "Testing Redis connection..."
    if docker exec "${container_name}" redis-cli ping > /dev/null 2>&1; then
        log_success "Redis: Connection successful"
    else
        log_error "Redis: Connection failed"
        ALL_HEALTHY=false
        return 1
    fi

    # Test basic operations
    log_info "Testing Redis operations..."
    if docker exec "${container_name}" redis-cli SET health_check "test" > /dev/null 2>&1 && \
       docker exec "${container_name}" redis-cli GET health_check > /dev/null 2>&1 && \
       docker exec "${container_name}" redis-cli DEL health_check > /dev/null 2>&1; then
        log_success "Redis: Operations successful"
    else
        log_error "Redis: Operations failed"
        ALL_HEALTHY=false
        return 1
    fi

    # Get Redis info
    local info=$(docker exec "${container_name}" redis-cli INFO server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    if [[ -n "${info}" ]]; then
        [[ "${QUIET_MODE}" == "false" ]] && log_info "  Version: ${info}"
    fi

    return 0
}

check_all_services() {
    log_section "Database Services Health Check"
    log_info "Started at: $(date)"

    # Get list of running containers from docker-compose
    local containers=$(docker-compose -f "${COMPOSE_FILE}" ps --services 2>/dev/null || echo "")

    if [[ -z "${containers}" ]]; then
        log_error "No services found or docker-compose.yml not present"
        return 1
    fi

    # Check each service based on its type
    for service in ${containers}; do
        local container_name=$(docker-compose -f "${COMPOSE_FILE}" ps -q "${service}" 2>/dev/null | xargs docker inspect -f '{{.Name}}' 2>/dev/null | sed 's/^///' || echo "")

        if [[ -z "${container_name}" ]]; then
            log_warning "Could not find container for service: ${service}"
            continue
        fi

        case "${service}" in
            *postgres*)
                check_postgres "${container_name}" || true
                ;;
            *mysql*)
                check_mysql "${container_name}" || true
                ;;
            *mongo*)
                check_mongodb "${container_name}" || true
                ;;
            *redis*)
                check_redis "${container_name}" || true
                ;;
            *)
                log_info "Unknown service type: ${service}, checking container only"
                check_container_status "${container_name}" "${service}" || true
                ;;
        esac
    done
}

generate_health_report() {
    log_section "Health Check Summary"

    if [[ "${ALL_HEALTHY}" == "true" ]]; then
        log_success "All services are healthy! ✓"
        return 0
    else
        log_error "Some services are unhealthy! ✗"
        return 1
    fi
}

################################################################################
# Main execution
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --quiet|-q)
                QUIET_MODE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --quiet, -q     Quiet mode (only show errors)"
                echo "  --help, -h      Show this help message"
                echo ""
                echo "Exit codes:"
                echo "  0 - All services healthy"
                echo "  1 - One or more services unhealthy"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Check if docker-compose file exists
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_error "Docker Compose file not found: ${COMPOSE_FILE}"
        exit 1
    fi

    # Run health checks
    check_all_services

    # Generate report and exit with appropriate code
    if generate_health_report; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
