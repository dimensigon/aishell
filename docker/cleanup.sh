#!/bin/bash

################################################################################
# Docker Environment Cleanup Script
################################################################################
# This script performs complete cleanup of Docker test environment:
# - Stop all running containers
# - Remove containers
# - Remove volumes and networks
# - Clean up test data and logs
# - Optional: Remove images
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
FORCE_MODE=false
REMOVE_IMAGES=false
REMOVE_ALL=false

################################################################################
# Logging functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*" >&2
}

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $*${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

################################################################################
# Cleanup functions
################################################################################

stop_containers() {
    log_section "Stopping Containers"

    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_warning "Docker Compose file not found: ${COMPOSE_FILE}"
        return 0
    fi

    log_info "Stopping all containers..."
    if docker-compose -f "${COMPOSE_FILE}" stop --timeout 30 2>/dev/null; then
        log_success "All containers stopped"
    else
        log_warning "Some containers may have failed to stop gracefully"
    fi
}

remove_containers() {
    log_section "Removing Containers"

    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_warning "Docker Compose file not found: ${COMPOSE_FILE}"
        return 0
    fi

    log_info "Removing containers..."
    if docker-compose -f "${COMPOSE_FILE}" rm -f 2>/dev/null; then
        log_success "Containers removed"
    else
        log_warning "Failed to remove some containers"
    fi

    # Clean up any orphaned containers
    log_info "Checking for orphaned containers..."
    local orphaned=$(docker ps -a --filter "name=test-" --format "{{.Names}}" 2>/dev/null || echo "")
    if [[ -n "${orphaned}" ]]; then
        log_info "Found orphaned containers: ${orphaned}"
        echo "${orphaned}" | xargs docker rm -f 2>/dev/null || true
        log_success "Orphaned containers removed"
    else
        log_info "No orphaned containers found"
    fi
}

remove_volumes() {
    log_section "Removing Volumes"

    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_warning "Docker Compose file not found: ${COMPOSE_FILE}"
        return 0
    fi

    log_info "Removing volumes..."
    if docker-compose -f "${COMPOSE_FILE}" down -v 2>/dev/null; then
        log_success "Volumes removed"
    else
        log_warning "Failed to remove some volumes"
    fi

    # Clean up any orphaned volumes
    log_info "Checking for orphaned volumes..."
    local orphaned_volumes=$(docker volume ls --filter "name=test" --format "{{.Name}}" 2>/dev/null || echo "")
    if [[ -n "${orphaned_volumes}" ]]; then
        log_info "Found orphaned volumes: ${orphaned_volumes}"
        echo "${orphaned_volumes}" | xargs docker volume rm 2>/dev/null || true
        log_success "Orphaned volumes removed"
    else
        log_info "No orphaned volumes found"
    fi
}

remove_networks() {
    log_section "Removing Networks"

    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_warning "Docker Compose file not found: ${COMPOSE_FILE}"
        return 0
    fi

    log_info "Removing networks..."
    docker-compose -f "${COMPOSE_FILE}" down 2>/dev/null || true

    # Clean up any orphaned networks
    log_info "Checking for orphaned networks..."
    local orphaned_networks=$(docker network ls --filter "name=test" --format "{{.Name}}" 2>/dev/null | grep -v "bridge\|host\|none" || echo "")
    if [[ -n "${orphaned_networks}" ]]; then
        log_info "Found orphaned networks: ${orphaned_networks}"
        echo "${orphaned_networks}" | xargs docker network rm 2>/dev/null || true
        log_success "Orphaned networks removed"
    else
        log_info "No orphaned networks found"
    fi
}

remove_images() {
    log_section "Removing Images"

    if [[ "${REMOVE_IMAGES}" != "true" ]]; then
        log_info "Skipping image removal (use --remove-images to enable)"
        return 0
    fi

    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_warning "Docker Compose file not found: ${COMPOSE_FILE}"
        return 0
    fi

    log_info "Removing images used by services..."
    docker-compose -f "${COMPOSE_FILE}" down --rmi local 2>/dev/null || true
    log_success "Images removed"
}

clean_test_data() {
    log_section "Cleaning Test Data"

    cd "${PROJECT_ROOT}"

    # Remove test output files
    if [[ -f "test-output.log" ]]; then
        rm -f test-output.log
        log_success "Removed test-output.log"
    fi

    # Remove test results directory
    if [[ -d "test-results" ]]; then
        if [[ "${FORCE_MODE}" == "true" ]]; then
            rm -rf test-results
            log_success "Removed test-results directory"
        else
            log_info "test-results directory exists (use --force to remove)"
        fi
    fi

    # Remove docker logs
    local docker_logs=$(find . -maxdepth 1 -name "docker-logs-*.log" 2>/dev/null || echo "")
    if [[ -n "${docker_logs}" ]]; then
        rm -f docker-logs-*.log
        log_success "Removed Docker log files"
    fi

    # Remove coverage directory (optional)
    if [[ "${FORCE_MODE}" == "true" ]] && [[ -d "coverage" ]]; then
        rm -rf coverage
        log_success "Removed coverage directory"
    fi

    log_success "Test data cleanup completed"
}

prune_docker_system() {
    log_section "Pruning Docker System"

    if [[ "${REMOVE_ALL}" != "true" ]]; then
        log_info "Skipping system prune (use --prune to enable)"
        return 0
    fi

    log_warning "This will remove all unused Docker resources system-wide!"

    if [[ "${FORCE_MODE}" != "true" ]]; then
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "System prune cancelled"
            return 0
        fi
    fi

    log_info "Pruning Docker system..."
    docker system prune -af --volumes 2>/dev/null || true
    log_success "Docker system pruned"
}

display_cleanup_summary() {
    log_section "Cleanup Summary"

    log_info "Docker containers:"
    docker ps -a --filter "name=test-" 2>/dev/null || log_info "  No test containers found"

    log_info "Docker volumes:"
    docker volume ls --filter "name=test" 2>/dev/null || log_info "  No test volumes found"

    log_info "Docker networks:"
    docker network ls --filter "name=test" 2>/dev/null | grep -v "NETWORK ID" || log_info "  No test networks found"

    if [[ "${REMOVE_IMAGES}" == "true" ]]; then
        log_info "Docker images:"
        docker images --filter "reference=test-*" 2>/dev/null || log_info "  No test images found"
    fi
}

################################################################################
# Main execution
################################################################################

show_help() {
    cat << EOF
Docker Environment Cleanup Script

Usage: $0 [OPTIONS]

Options:
  --force, -f           Force cleanup without prompts, remove test-results
  --remove-images, -i   Remove Docker images used by services
  --prune, -p           Prune entire Docker system (removes ALL unused resources)
  --all, -a             Equivalent to --force --remove-images --prune
  --help, -h            Show this help message

Examples:
  $0                    # Basic cleanup (stop, remove containers/volumes/networks)
  $0 --force            # Force cleanup including test data
  $0 --remove-images    # Also remove Docker images
  $0 --all              # Complete cleanup of everything

Exit codes:
  0 - Cleanup successful
  1 - Cleanup failed or interrupted
EOF
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force|-f)
                FORCE_MODE=true
                shift
                ;;
            --remove-images|-i)
                REMOVE_IMAGES=true
                shift
                ;;
            --prune|-p)
                REMOVE_ALL=true
                shift
                ;;
            --all|-a)
                FORCE_MODE=true
                REMOVE_IMAGES=true
                REMOVE_ALL=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_section "Docker Environment Cleanup"
    log_info "Started at: $(date)"

    if [[ "${FORCE_MODE}" == "true" ]]; then
        log_warning "Running in FORCE mode"
    fi

    # Perform cleanup steps
    stop_containers
    remove_containers
    remove_volumes
    remove_networks
    remove_images
    clean_test_data
    prune_docker_system

    # Show summary
    display_cleanup_summary

    log_section "Cleanup Complete"
    log_success "All cleanup operations completed successfully!"
    log_info "Finished at: $(date)"

    exit 0
}

# Run main function
main "$@"
