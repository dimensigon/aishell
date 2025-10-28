#!/usr/bin/env python3
"""
AI-Shell Docker Database Setup Verification Script

This script verifies that all Docker database containers are running correctly
and can accept connections with the test credentials.
"""

import sys
import time
import subprocess
from typing import Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def run_command(command: List[str]) -> Tuple[bool, str]:
    """Run a shell command and return success status and output"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_docker_installed() -> bool:
    """Check if Docker is installed and running"""
    print_info("Checking Docker installation...")
    success, output = run_command(['docker', '--version'])
    if success:
        print_success(f"Docker is installed: {output.strip()}")
        return True
    else:
        print_error("Docker is not installed or not in PATH")
        return False


def check_docker_compose_installed() -> bool:
    """Check if Docker Compose is installed"""
    print_info("Checking Docker Compose installation...")
    success, output = run_command(['docker-compose', '--version'])
    if success:
        print_success(f"Docker Compose is installed: {output.strip()}")
        return True
    else:
        print_error("Docker Compose is not installed or not in PATH")
        return False


def check_container_running(container_name: str) -> bool:
    """Check if a specific container is running"""
    success, output = run_command(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'])
    return success and container_name in output


def check_container_health(container_name: str) -> str:
    """Get the health status of a container"""
    success, output = run_command([
        'docker', 'inspect',
        '--format', '{{.State.Health.Status}}',
        container_name
    ])
    if success and output.strip():
        return output.strip()
    return "no healthcheck"


def test_postgres_connection() -> bool:
    """Test PostgreSQL connection"""
    print_info("Testing PostgreSQL connection...")
    success, output = run_command([
        'docker', 'exec', 'test_postgres',
        'psql', '-U', 'postgres', '-c', 'SELECT version();'
    ])
    if success and 'PostgreSQL' in output:
        print_success("PostgreSQL connection successful")
        return True
    else:
        print_error(f"PostgreSQL connection failed: {output}")
        return False


def test_mongodb_connection() -> bool:
    """Test MongoDB connection"""
    print_info("Testing MongoDB connection...")
    success, output = run_command([
        'docker', 'exec', 'test_mongodb',
        'mongosh', '-u', 'admin', '-p', 'MyMongoPass123',
        '--authenticationDatabase', 'admin',
        '--eval', 'db.version()'
    ])
    if success:
        print_success("MongoDB connection successful")
        return True
    else:
        print_error(f"MongoDB connection failed: {output}")
        return False


def test_mysql_connection() -> bool:
    """Test MySQL connection"""
    print_info("Testing MySQL connection...")
    success, output = run_command([
        'docker', 'exec', 'test_mysql',
        'mysql', '-u', 'root', '-pMyMySQLPass123',
        '-e', 'SELECT VERSION();'
    ])
    if success and 'mysql' in output.lower():
        print_success("MySQL connection successful")
        return True
    else:
        print_error(f"MySQL connection failed: {output}")
        return False


def test_redis_connection() -> bool:
    """Test Redis connection"""
    print_info("Testing Redis connection...")
    success, output = run_command([
        'docker', 'exec', 'test_redis',
        'redis-cli', '--no-auth-warning', '-a', 'MyRedisPass123', 'PING'
    ])
    if success and 'PONG' in output:
        print_success("Redis connection successful")
        return True
    else:
        print_error(f"Redis connection failed: {output}")
        return False


def check_database_data(db_type: str, container_name: str) -> bool:
    """Check if test data was loaded correctly"""
    print_info(f"Checking {db_type} test data...")

    if db_type == 'PostgreSQL':
        success, output = run_command([
            'docker', 'exec', 'test_postgres',
            'psql', '-U', 'postgres', '-d', 'postgres',
            '-c', 'SELECT COUNT(*) FROM departments;'
        ])
        if success and '5' in output:
            print_success(f"{db_type} test data loaded (5 departments found)")
            return True

    elif db_type == 'MongoDB':
        success, output = run_command([
            'docker', 'exec', 'test_mongodb',
            'mongosh', '-u', 'admin', '-p', 'MyMongoPass123',
            '--authenticationDatabase', 'admin',
            '--eval', 'use test_integration_db; db.departments.countDocuments({})'
        ])
        if success and any(str(i) in output for i in range(1, 10)):
            print_success(f"{db_type} test data loaded")
            return True

    elif db_type == 'MySQL':
        success, output = run_command([
            'docker', 'exec', 'test_mysql',
            'mysql', '-u', 'root', '-pMyMySQLPass123',
            'test_integration_db',
            '-e', 'SELECT COUNT(*) FROM departments;'
        ])
        if success and '5' in output:
            print_success(f"{db_type} test data loaded (5 departments found)")
            return True

    print_warning(f"{db_type} test data check inconclusive")
    return False


def main():
    """Main execution function"""
    print_header("AI-Shell Docker Database Setup Verification")

    # Track results
    checks_passed = 0
    checks_failed = 0

    # Step 1: Check Docker installation
    if not check_docker_installed():
        print_error("Docker is required but not found. Please install Docker first.")
        sys.exit(1)
    checks_passed += 1

    if not check_docker_compose_installed():
        print_error("Docker Compose is required but not found. Please install Docker Compose first.")
        sys.exit(1)
    checks_passed += 1

    # Step 2: Check containers
    print_header("Checking Container Status")

    containers = {
        'test_postgres': 'PostgreSQL',
        'test_mongodb': 'MongoDB',
        'test_mysql': 'MySQL',
        'test_redis': 'Redis'
    }

    running_containers = []

    for container_name, db_name in containers.items():
        if check_container_running(container_name):
            health = check_container_health(container_name)
            if health == 'healthy':
                print_success(f"{db_name} container is running and healthy")
                running_containers.append(container_name)
                checks_passed += 1
            elif health == 'no healthcheck':
                print_warning(f"{db_name} container is running (no healthcheck configured)")
                running_containers.append(container_name)
                checks_passed += 1
            else:
                print_warning(f"{db_name} container is running but health status is: {health}")
                checks_passed += 1
        else:
            print_error(f"{db_name} container is not running")
            checks_failed += 1

    if not running_containers:
        print_error("\nNo containers are running. Please start them with:")
        print_info("    docker-compose up -d")
        sys.exit(1)

    # Step 3: Test connections
    print_header("Testing Database Connections")

    connection_tests = {
        'test_postgres': ('PostgreSQL', test_postgres_connection),
        'test_mongodb': ('MongoDB', test_mongodb_connection),
        'test_mysql': ('MySQL', test_mysql_connection),
        'test_redis': ('Redis', test_redis_connection)
    }

    for container_name, (db_name, test_func) in connection_tests.items():
        if container_name in running_containers:
            # Wait a bit for database to be ready
            time.sleep(1)
            if test_func():
                checks_passed += 1
            else:
                checks_failed += 1

    # Step 4: Check test data
    print_header("Verifying Test Data")

    data_checks = [
        ('PostgreSQL', 'test_postgres'),
        ('MongoDB', 'test_mongodb'),
        ('MySQL', 'test_mysql')
    ]

    for db_type, container_name in data_checks:
        if container_name in running_containers:
            if check_database_data(db_type, container_name):
                checks_passed += 1
            else:
                checks_failed += 1

    # Final summary
    print_header("Verification Summary")

    total_checks = checks_passed + checks_failed
    print(f"Total checks: {total_checks}")
    print_success(f"Passed: {checks_passed}")

    if checks_failed > 0:
        print_error(f"Failed: {checks_failed}")

    if checks_failed == 0:
        print_header("All Checks Passed! ✓")
        print_success("Your Docker database environment is ready for testing!")
        print_info("\nConnection strings:")
        print("  PostgreSQL: postgresql://postgres:MyPostgresPass123@localhost:5432/postgres")
        print("  MongoDB:    mongodb://admin:MyMongoPass123@localhost:27017/test_integration_db?authSource=admin")
        print("  MySQL:      mysql://testuser:testpass@localhost:3306/test_integration_db")
        print("  Redis:      redis://:MyRedisPass123@localhost:6379/0")
        sys.exit(0)
    else:
        print_header("Some Checks Failed ✗")
        print_warning("Please review the errors above and fix any issues.")
        print_info("\nCommon troubleshooting steps:")
        print("  1. Ensure all containers are running: docker-compose ps")
        print("  2. Check container logs: docker-compose logs <service-name>")
        print("  3. Restart containers: docker-compose restart")
        print("  4. Recreate containers: docker-compose down && docker-compose up -d")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        sys.exit(1)
