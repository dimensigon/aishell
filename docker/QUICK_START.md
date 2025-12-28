# Docker Test Runner - Quick Start Guide

## 🚀 One-Line Test Execution

```bash
cd /home/claude/AIShell/aishell/docker && ./test-runner.sh
```

## 📋 Common Commands

### Run Tests
```bash
# Full test suite with all checks
./test-runner.sh

# The script will automatically:
# ✓ Validate Docker environment
# ✓ Start database services
# ✓ Wait for services to be healthy
# ✓ Run tests with coverage
# ✓ Collect results
# ✓ Cleanup resources
```

### Check Service Health
```bash
# Detailed health check
./health-check.sh

# Quick check (only errors)
./health-check.sh --quiet

# Use in scripts
if ./health-check.sh --quiet; then
    echo "All services healthy"
else
    echo "Services unhealthy"
fi
```

### Cleanup Resources
```bash
# Basic cleanup (safe)
./cleanup.sh

# Force cleanup (removes test data)
./cleanup.sh --force

# Complete cleanup (removes images and prunes Docker)
./cleanup.sh --all
```

## 🔍 Troubleshooting

### Quick Diagnostics
```bash
# 1. Check if Docker is running
docker info

# 2. Check service status
docker compose -f docker-compose.test.yml ps

# 3. View service logs
docker compose -f docker-compose.test.yml logs

# 4. Test connections
./health-check.sh

# 5. Cleanup and restart
./cleanup.sh --force && ./test-runner.sh
```

### Common Issues

#### "Services failed to become healthy"
```bash
# View logs to identify the issue
docker compose -f docker-compose.test.yml logs

# Increase wait time by editing test-runner.sh
# Change: MAX_WAIT_TIME=120
# To: MAX_WAIT_TIME=180
```

#### "Port already in use"
```bash
# Find what's using the port
lsof -i :5432  # PostgreSQL
lsof -i :3306  # MySQL
lsof -i :27017 # MongoDB
lsof -i :6379  # Redis

# Stop conflicting service
sudo systemctl stop postgresql
# or kill the process
```

#### "Out of disk space"
```bash
# Check disk usage
docker system df

# Clean up Docker resources
./cleanup.sh --all

# Prune everything
docker system prune -af --volumes
```

#### "Tests timeout"
```bash
# Run tests with more time
# Edit test-runner.sh:
# TEST_TIMEOUT=600  # Change to 900 or higher

# Or run tests manually
npm run test -- --testTimeout=60000
```

## 📊 View Test Results

### After Running Tests

```bash
# View test summary
cat test-results/test-summary.txt

# View detailed test output
less test-results/test-output.log

# View coverage report (HTML)
open test-results/coverage/lcov-report/index.html

# View container logs
less test-results/docker-containers.log
```

## 🎯 Development Workflow

### Standard Flow
```bash
# 1. Start development
cd /home/claude/AIShell/aishell/docker

# 2. Run tests
./test-runner.sh

# 3. If tests fail, debug
./health-check.sh
docker compose -f docker-compose.test.yml logs [service]

# 4. Fix code and rerun
npm run test -- --testPathPattern=your-test

# 5. Cleanup when done
./cleanup.sh --force
```

### Manual Testing
```bash
# 1. Start services only (no tests)
docker compose -f docker-compose.test.yml up -d

# 2. Wait for services
./health-check.sh

# 3. Run specific tests
npm run test -- --testPathPattern=database

# 4. Keep services running for debugging
# ... make changes, rerun tests ...

# 5. Cleanup when done
./cleanup.sh
```

## 🔧 Script Options

### test-runner.sh
- No options (runs everything automatically)
- Configurable via environment variables:
  ```bash
  MAX_WAIT_TIME=180 ./test-runner.sh
  TEST_TIMEOUT=900 ./test-runner.sh
  ```

### health-check.sh
- `--quiet, -q` - Only show errors
- `--help, -h` - Show help message

### cleanup.sh
- `--force, -f` - No prompts, remove test data
- `--remove-images, -i` - Also remove Docker images
- `--prune, -p` - Prune entire Docker system
- `--all, -a` - Complete cleanup (all options)
- `--help, -h` - Show help message

## 📈 Performance Tips

### Faster Tests
```bash
# Use parallel test execution
npm run test -- --maxWorkers=4

# Run only changed tests
npm run test -- --onlyChanged

# Skip coverage for faster runs
npm run test -- --coverage=false
```

### Reduce Docker Overhead
```bash
# Pre-pull images (do once)
docker compose -f docker-compose.test.yml pull

# Use Docker layer caching
# Keep images around between runs
# Only use cleanup.sh without --remove-images
```

## 🤖 CI/CD Integration

### GitHub Actions
The workflow runs automatically on:
- Push to `main`, `develop`, `feature/**`
- Pull requests to `main`, `develop`
- Manual trigger via Actions tab

### View Results
1. Go to GitHub Actions tab
2. Select "Database Integration Tests" workflow
3. View test results and artifacts
4. Download coverage reports

### Manual Trigger
1. Go to Actions tab
2. Select "Database Integration Tests"
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow" button

## 📞 Getting Help

### Script Help
```bash
./health-check.sh --help
./cleanup.sh --help
```

### View Documentation
```bash
# Full documentation
cat README.md

# This quick start guide
cat QUICK_START.md
```

### Debug Mode
```bash
# Run with verbose output
set -x
./test-runner.sh
set +x
```

## 🎓 Examples

### Example 1: Quick Test Run
```bash
cd /home/claude/AIShell/aishell/docker
./test-runner.sh
# Wait for completion
# Results in: test-results/
```

### Example 2: Debug Failed Test
```bash
# Start services
docker compose -f docker-compose.test.yml up -d

# Check what's wrong
./health-check.sh
docker compose -f docker-compose.test.yml logs postgres

# Run specific test
npm run test -- --testPathPattern=postgres --verbose

# Cleanup
./cleanup.sh --force
```

### Example 3: CI/CD Simulation
```bash
# Simulate CI environment
export NODE_ENV=test
export CI=true
export DATABASE_TEST_MODE=docker

# Run as CI would
./test-runner.sh

# Check exit code
echo $?  # 0 = success, non-zero = failure
```

### Example 4: Performance Testing
```bash
# Start services
docker compose -f docker-compose.test.yml up -d

# Wait for ready
./health-check.sh

# Run tests with timing
time npm run test

# Run multiple times for average
for i in {1..5}; do
    time npm run test -- --silent
done

# Cleanup
./cleanup.sh
```

## ⚡ Tips & Tricks

1. **Keep services running between test runs** - Don't cleanup until done coding
2. **Use --quiet mode in scripts** - `./health-check.sh --quiet`
3. **Pre-pull images** - Save time on subsequent runs
4. **Monitor resources** - Use `docker stats` to watch resource usage
5. **Check logs first** - Most issues are visible in service logs
6. **Use tmpfs for speed** - Add tmpfs mounts for database data (Linux only)
7. **Run tests in parallel** - Use `--maxWorkers` for faster execution
8. **Keep Docker clean** - Run cleanup regularly to free disk space

---

**Quick Links:**
- Full Documentation: [README.md](README.md)
- GitHub Actions Workflow: [.github/workflows/database-tests.yml](../.github/workflows/database-tests.yml)
- Docker Compose: [docker-compose.test.yml](docker-compose.test.yml)

**Script Locations:**
- `/home/claude/AIShell/aishell/docker/test-runner.sh`
- `/home/claude/AIShell/aishell/docker/health-check.sh`
- `/home/claude/AIShell/aishell/docker/cleanup.sh`
