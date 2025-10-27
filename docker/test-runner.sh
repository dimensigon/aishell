#!/bin/bash

################################################################################
# Docker-Based Database Integration Test Runner
################################################################################
# This script orchestrates the complete test lifecycle:
# 1. Start Docker Compose services
# 2. Wait for all databases to be healthy
# 3. Run database integration tests
# 4. Collect test results and coverage
# 5. Cleanup containers and volumes
# 6. Exit with appropriate status code
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
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
HEALTH_CHECK_SCRIPT="${SCRIPT_DIR}/health-check.sh"
CLEANUP_SCRIPT="${SCRIPT_DIR}/cleanup.sh"
MAX_WAIT_TIME=120
HEALTH_CHECK_INTERVAL=5
TEST_TIMEOUT=600

# Test results
EXIT_CODE=0
START_TIME=$(date +%s)

################################################################################
# Logging functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $*${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

################################################################################
# Error handling
################################################################################

cleanup_on_error() {
    local exit_code=$?
    log_error "Test runner failed with exit code: ${exit_code}"

    # Collect container logs before cleanup
    log_info "Collecting container logs..."
    docker-compose -f "${COMPOSE_FILE}" logs > "${PROJECT_ROOT}/docker-logs-$(date +%s).log" 2>&1 || true

    # Run cleanup
    if [[ -x "${CLEANUP_SCRIPT}" ]]; then
        log_info "Running cleanup script..."
        "${CLEANUP_SCRIPT}" || true
    fi

    exit "${exit_code}"
}

trap cleanup_on_error ERR INT TERM

################################################################################
# Validation
################################################################################

validate_environment() {
    log_section "Validating Environment"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    log_success "Docker found: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    log_success "Docker Compose found: $(docker-compose --version)"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    log_success "Docker daemon is running"

    # Check compose file
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_error "Docker Compose file not found: ${COMPOSE_FILE}"
        exit 1
    fi
    log_success "Docker Compose file found"

    # Check health check script
    if [[ ! -x "${HEALTH_CHECK_SCRIPT}" ]]; then
        log_warning "Health check script not found or not executable: ${HEALTH_CHECK_SCRIPT}"
    else
        log_success "Health check script found"
    fi
}

################################################################################
# Docker Compose operations
################################################################################

start_services() {
    log_section "Starting Docker Services"

    log_info "Pulling latest images..."
    docker-compose -f "${COMPOSE_FILE}" pull --quiet || {
        log_warning "Failed to pull images, continuing with cached images"
    }

    log_info "Starting services in detached mode..."
    docker-compose -f "${COMPOSE_FILE}" up -d

    log_success "Services started"

    # Show running containers
    log_info "Running containers:"
    docker-compose -f "${COMPOSE_FILE}" ps
}

wait_for_healthy_services() {
    log_section "Waiting for Services to be Healthy"

    local elapsed=0

    while [[ ${elapsed} -lt ${MAX_WAIT_TIME} ]]; do
        log_info "Health check attempt (${elapsed}s / ${MAX_WAIT_TIME}s)..."

        if [[ -x "${HEALTH_CHECK_SCRIPT}" ]]; then
            if "${HEALTH_CHECK_SCRIPT}" --quiet; then
                log_success "All services are healthy!"
                return 0
            fi
        else
            # Fallback: Check container health status
            local unhealthy_count=0
            while IFS= read -r line; do
                if [[ "$line" != *"(healthy)"* ]] && [[ "$line" != *"Up"* ]]; then
                    ((unhealthy_count++))
                fi
            done < <(docker-compose -f "${COMPOSE_FILE}" ps)

            if [[ ${unhealthy_count} -eq 0 ]]; then
                log_success "All services are running!"
                return 0
            fi
        fi

        sleep ${HEALTH_CHECK_INTERVAL}
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
    done

    log_error "Services failed to become healthy within ${MAX_WAIT_TIME} seconds"

    # Show logs for debugging
    log_info "Container logs:"
    docker-compose -f "${COMPOSE_FILE}" logs --tail=50

    return 1
}

################################################################################
# Test execution
################################################################################

run_database_tests() {
    log_section "Running Database Integration Tests"

    cd "${PROJECT_ROOT}"

    # Set test environment variables
    export NODE_ENV=test
    export CI=true
    export DATABASE_TEST_MODE=docker

    log_info "Test configuration:"
    log_info "  Working directory: ${PROJECT_ROOT}"
    log_info "  Node environment: ${NODE_ENV}"
    log_info "  Test timeout: ${TEST_TIMEOUT}s"

    # Run tests with timeout
    local test_start=$(date +%s)

    log_info "Executing test suite..."
    if timeout ${TEST_TIMEOUT}s npm run test -- --coverage --verbose 2>&1 | tee test-output.log; then
        log_success "Tests passed!"
        EXIT_CODE=0
    else
        local test_exit_code=$?
        if [[ ${test_exit_code} -eq 124 ]]; then
            log_error "Tests timed out after ${TEST_TIMEOUT} seconds"
            EXIT_CODE=124
        else
            log_error "Tests failed with exit code: ${test_exit_code}"
            EXIT_CODE=${test_exit_code}
        fi
    fi

    local test_end=$(date +%s)
    local test_duration=$((test_end - test_start))
    log_info "Test execution completed in ${test_duration} seconds"
}

collect_test_results() {
    log_section "Collecting Test Results"

    cd "${PROJECT_ROOT}"

    local results_dir="${PROJECT_ROOT}/test-results"
    mkdir -p "${results_dir}"

    # Copy test output
    if [[ -f "test-output.log" ]]; then
        cp test-output.log "${results_dir}/" || true
        log_success "Test output saved to: ${results_dir}/test-output.log"
    fi

    # Copy coverage report
    if [[ -d "coverage" ]]; then
        cp -r coverage "${results_dir}/" || true
        log_success "Coverage report saved to: ${results_dir}/coverage/"

        # Display coverage summary
        if [[ -f "coverage/coverage-summary.json" ]]; then
            log_info "Coverage summary:"
            cat coverage/coverage-summary.json | grep -E "(lines|statements|functions|branches)" || true
        fi
    fi

    # Collect container logs
    log_info "Collecting container logs..."
    docker-compose -f "${COMPOSE_FILE}" logs > "${results_dir}/docker-containers.log" 2>&1 || true
    log_success "Container logs saved to: ${results_dir}/docker-containers.log"

    # Generate test report
    local report_file="${results_dir}/test-summary.txt"
    {
        echo "Database Integration Test Report"
        echo "================================="
        echo "Date: $(date)"
        echo "Exit Code: ${EXIT_CODE}"
        echo "Duration: $(($(date +%s) - START_TIME)) seconds"
        echo ""
        echo "Environment:"
        echo "  Docker: $(docker --version)"
        echo "  Docker Compose: $(docker-compose --version)"
        echo "  Node: $(node --version 2>/dev/null || echo 'N/A')"
        echo "  NPM: $(npm --version 2>/dev/null || echo 'N/A')"
        echo ""
        echo "Services:"
        docker-compose -f "${COMPOSE_FILE}" ps || echo "Failed to get service status"
    } > "${report_file}"

    log_success "Test summary saved to: ${report_file}"
}

cleanup_environment() {
    log_section "Cleaning Up Environment"

    if [[ -x "${CLEANUP_SCRIPT}" ]]; then
        log_info "Running cleanup script..."
        if "${CLEANUP_SCRIPT}"; then
            log_success "Cleanup completed successfully"
        else
            log_warning "Cleanup script exited with non-zero status"
        fi
    else
        log_info "Cleanup script not found, performing basic cleanup..."
        docker-compose -f "${COMPOSE_FILE}" down -v || true
        log_success "Basic cleanup completed"
    fi
}

################################################################################
# Main execution
################################################################################

main() {
    log_section "Database Integration Test Runner"
    log_info "Starting test run at $(date)"

    # Step 1: Validate environment
    validate_environment

    # Step 2: Start Docker services
    start_services

    # Step 3: Wait for services to be healthy
    if ! wait_for_healthy_services; then
        log_error "Failed to start healthy services"
        cleanup_environment
        exit 1
    fi

    # Step 4: Run tests
    run_database_tests

    # Step 5: Collect results
    collect_test_results

    # Step 6: Cleanup
    cleanup_environment

    # Final report
    log_section "Test Run Complete"
    local total_duration=$(($(date +%s) - START_TIME))

    if [[ ${EXIT_CODE} -eq 0 ]]; then
        log_success "All tests passed! Total duration: ${total_duration} seconds"
    else
        log_error "Tests failed with exit code: ${EXIT_CODE}. Total duration: ${total_duration} seconds"
    fi

    exit ${EXIT_CODE}
}

# Run main function
main "$@"
