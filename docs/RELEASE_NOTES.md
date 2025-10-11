# AI-Shell Release Notes

## Version 2.0.0 (October 2025) - Major Release

**Status:** Production Ready
**Python Support:** 3.9 - 3.14
**FAISS Version:** 1.12.0

### Overview

Version 2.0.0 represents a major milestone in AI-Shell's evolution, introducing autonomous agent workflows, comprehensive health monitoring, and production-grade safety controls. This release includes 12 major implementation phases completed over 6 months of development.

### Breaking Changes

#### Database Client Updates
- **Oracle Client Migration:** Replaced `cx_Oracle` with `python-oracledb` (thin mode)
  - **Action Required:** Remove Oracle client dependencies
  - **Migration:** Connection strings remain compatible

#### Configuration Schema Changes
- New configuration format for agent safety controls
- Updated health check configuration options
- **Action Required:** Run `ai-shell --init` to upgrade config

#### API Changes
- `DatabaseModule.execute_query()` now returns structured `QueryResult` objects
- Agent execution methods now require `SafetyContext`
- **Action Required:** Update custom integrations to use new APIs

### New Features

#### Phase 11: Advanced Health Check System
- **Parallel Health Monitoring** (< 2s total execution time)
  - LLM availability checks
  - Database connectivity validation
  - Filesystem health monitoring
  - Memory usage tracking
  - Concurrent execution with timeout protection

- **Custom Health Checks** - Extensible framework for application-specific checks
- **Degraded Mode Operation** - Graceful degradation when components fail
- **Health Dashboard** - Real-time monitoring UI

#### Phase 12: Agentic AI Workflows
- **Custom AI Agents**
  - Multi-step task decomposition
  - LLM-powered planning
  - State persistence and checkpointing
  - Error recovery and rollback

- **Tool Registry System**
  - Centralized tool management
  - JSON Schema-based parameter validation
  - Risk-level classification (5 levels)
  - Capability-based tool matching
  - Rate limiting and audit trails

- **Safety and Approval System**
  - Multi-layer protection for autonomous operations
  - Risk assessment engine
  - Human-in-the-loop for critical operations
  - SQL deep inspection
  - Audit logging for compliance

#### Vector Search & Auto-completion
- FAISS 1.12.0 support
- Extended Python version support (3.9 - 3.14)
- Improved semantic search performance
- Context-aware command suggestions

#### Security Enhancements
- **Credential Vault Improvements**
  - Per-vault unique cryptographic salts
  - Enhanced key derivation (PBKDF2 with 100k iterations)
  - Automatic redaction on retrieval
  - Multiple credential types (Database, API, SSH, OAuth)

- **Command Sanitization**
  - Expanded dangerous pattern detection
  - Path traversal prevention
  - SQL injection protection
  - Risk-based command blocking

- **Audit System**
  - Comprehensive operation logging
  - Compliance tracking
  - PII detection and handling

#### Performance Optimizations
- Asynchronous event bus for non-blocking operations
- Query caching with configurable TTL
- Connection pooling for all database clients
- Lazy-loading for UI components
- Memory-efficient vector operations

#### Database Support
- Oracle (thin client - no Oracle installation required)
- PostgreSQL
- MySQL/MariaDB
- MongoDB
- Redis
- Cassandra
- Neo4j
- DynamoDB

#### UI Enhancements
- Textual-based TUI with adaptive panels
- Real-time panel resizing based on content
- Context suggestion engine
- Dynamic command preview
- Memory usage monitoring
- Startup animation with Matrix theme

### Improvements

#### Code Quality
- **Test Coverage:** 54% → 85% target
- **Type Safety:** mypy strict mode enabled
- **Documentation:** 100% public API documented
- **Code Style:** black + ruff formatting enforced

#### Developer Experience
- Comprehensive tutorial series (6 tutorials)
- API reference documentation
- Architecture decision records
- Example plugins and integrations
- Quick reference guide

#### Reliability
- Graceful error handling throughout
- Automatic retry mechanisms
- Connection health monitoring
- Resource cleanup on shutdown
- Rate limiting for API calls

### Bug Fixes

#### v2.0.0
- Fixed Oracle client compatibility issues (cx_Oracle → python-oracledb)
- Resolved FAISS compatibility with Python 3.12+
- Fixed integration test failures in CI/CD pipeline
- Corrected initialization sequence in main entry point
- Fixed cache TTL expiration timing issues
- Resolved type annotation inconsistencies

#### Security Fixes
- Fixed hardcoded salt vulnerability in vault encryption
- Added null checks to prevent potential crashes in MCP clients
- Improved path validation to prevent directory traversal
- Enhanced SQL injection protection in query analyzer

### Known Issues

#### Non-Critical
1. **UI Widget Test Coverage:** Currently at 29%, target 80%
   - Impact: Low (UI functionality working, tests incomplete)
   - Planned: Q4 2025

2. **Performance Cache Tests:** 2 timing-sensitive tests occasionally fail
   - Impact: Low (false positives in test suite)
   - Workaround: Tests pass with retry
   - Planned fix: Add timing tolerance buffers

3. **Memory Monitor:** Memory usage reporting inaccurate on containers
   - Impact: Low (monitoring only, no functional impact)
   - Workaround: Use host metrics for containers
   - Planned: Container-aware detection

### Upgrade Guide

#### From v1.x to v2.0.0

##### 1. Backup Your Data
```bash
# Backup vault
cp -r ~/.ai-shell/vault ~/.ai-shell/vault.backup

# Backup configuration
cp ~/.ai-shell/config.yaml ~/.ai-shell/config.yaml.backup

# Backup command history
cp ~/.ai-shell/history.db ~/.ai-shell/history.db.backup
```

##### 2. Update Installation
```bash
# Update from PyPI
pip install --upgrade aishell

# Or from source
cd ai-shell
git pull origin main
pip install -e .
```

##### 3. Update Configuration
```bash
# Initialize new configuration format
ai-shell --init

# The tool will guide you through:
# - Agent safety settings
# - Health check configuration
# - Tool registry setup
```

##### 4. Oracle Database Users
If using Oracle database:
```bash
# Remove old Oracle client
pip uninstall cx-Oracle

# python-oracledb is already installed with aishell
# No additional Oracle client software needed!

# Test connection
ai-shell --execute "health"
```

##### 5. Update Custom Integrations

**Old API (v1.x):**
```python
# Old execute_query
result = await db.execute_query(sql)
print(result)  # Returns raw dict
```

**New API (v2.0.0):**
```python
# New execute_query with structured results
from src.database.module import QueryResult

result: QueryResult = await db.execute_query(sql)
print(result.rows)  # Access rows
print(result.metadata)  # Access metadata
print(result.execution_time)  # Timing info
```

**Agent Execution (New in v2.0.0):**
```python
from src.agents.safety.controller import SafetyController, SafetyContext

# Create safety context
context = SafetyContext(
    operation="data_export",
    risk_level=RiskLevel.HIGH,
    requires_approval=True
)

# Execute with safety checks
result = await safety_controller.validate_and_execute(
    agent=export_agent,
    task="Export user data",
    context=context
)
```

##### 6. Verify Installation
```bash
# Run health checks
ai-shell --health-check

# Should show:
# ✓ LLM: healthy
# ✓ Database: healthy
# ✓ Filesystem: healthy
# ✓ Memory: healthy

# Check version
ai-shell --version
# AI-Shell 2.0.0
```

### Deprecation Notices

#### Deprecated in v2.0.0 (Removed in v3.0.0)
- `DatabaseModule.raw_execute()` → Use `execute_query()` with structured results
- `LLMManager.simple_query()` → Use `generate_response()` with context
- Legacy vault format (< v1.5) → Will require migration tool in v3.0.0

#### Planned Deprecations (v2.1.0)
- Direct vault file access → Use vault API exclusively
- Synchronous MCP client methods → Async-only API

### Performance Benchmarks

#### v2.0.0 vs v1.5.0
- Health check time: 15s → 1.8s (8.3x faster)
- Agent task planning: 3.2s → 0.9s (3.5x faster)
- Query optimization: 450ms → 180ms (2.5x faster)
- Startup time: 2.1s → 1.3s (38% faster)
- Memory footprint: 145MB → 98MB (32% reduction)

#### Scalability
- Concurrent connections: 50 → 200 (4x increase)
- Agent parallel tasks: 5 → 20 (4x increase)
- Cache capacity: 1000 → 5000 queries (5x increase)

### Migration Path from v1.x

#### Step 1: Assess Custom Code
```bash
# Search for deprecated APIs
grep -r "raw_execute" your_code/
grep -r "simple_query" your_code/
```

#### Step 2: Update Dependencies
```bash
# Update requirements.txt
aishell>=2.0.0
python-oracledb>=2.5.0  # If using Oracle
faiss-cpu>=1.9.0  # Or faiss-gpu for GPU support
```

#### Step 3: Test Migration
```bash
# Run in test environment first
pytest tests/ -v

# Verify all connections
ai-shell --execute "health"

# Test critical workflows
ai-shell --execute "query SELECT 1"
```

#### Step 4: Production Deployment
```bash
# Deploy with rollback plan
# Keep v1.x available for quick rollback
pip install aishell==2.0.0

# Monitor logs for issues
tail -f ~/.ai-shell/logs/aishell.log
```

### Security Updates

#### CVE Addressed
- **Vault Salt Hardcoding** (Internal-2025-001)
  - Severity: Medium
  - Impact: Potential credential decryption if vault file accessed
  - Fixed: Per-vault unique cryptographic salts (v2.0.0)
  - Action: Existing vaults automatically migrated on first access

#### Security Enhancements
- PBKDF2 iterations increased: 10k → 100k
- Added rate limiting to prevent brute force attacks
- Enhanced SQL injection detection patterns
- Improved path validation for file operations
- Added audit logging for all sensitive operations

### Documentation Updates

#### New Documentation
- `/docs/ARCHITECTURE.md` - Complete system architecture
- `/tutorials/*.md` - 6 comprehensive tutorials
- `/docs/api/*.md` - Full API reference
- `/docs/enterprise/*.md` - Enterprise deployment guides
- `/docs/video-tutorials/*.md` - Video tutorial scripts

#### Updated Documentation
- `README.md` - Complete feature overview
- `/docs/guides/*.md` - Updated integration guides
- `/examples/*` - Real-world usage examples

### Contributors

**Core Team:**
- AI-Shell Development Team

**Special Thanks:**
- Community contributors for bug reports
- Beta testers for Phase 11 & 12 features
- Documentation reviewers

### Support and Resources

- **Documentation:** https://ai-shell.readthedocs.io
- **GitHub Issues:** https://github.com/dimensigon/aishell/issues
- **Discussions:** https://github.com/dimensigon/aishell/discussions
- **Tutorials:** `/tutorials` directory
- **Examples:** `/examples` directory

### Roadmap

#### v2.1.0 (Q1 2026) - Planned
- Multi-tenant support
- Role-based access control (RBAC)
- Cloud-native deployment options
- GraphQL API endpoint
- WebSocket support for real-time updates

#### v2.2.0 (Q2 2026) - Planned
- Machine learning model integration
- Advanced query optimization with ML
- Natural language to SQL improvements
- Custom agent marketplace
- Browser-based UI option

#### v3.0.0 (Q4 2026) - Vision
- Distributed agent coordination
- Multi-database transactions
- Advanced security compliance (SOC2, HIPAA)
- Enterprise SSO integration
- Kubernetes operator

---

## Version 1.5.0 (April 2025)

### Features
- FAISS 1.8.0 integration
- Python 3.12 support
- Enhanced vector search
- Performance optimizations

### Bug Fixes
- Fixed memory leaks in vector store
- Resolved connection pool exhaustion
- Corrected type hints in core modules

---

## Version 1.0.0 (October 2024) - Initial Release

### Features
- Multi-database support (Oracle, PostgreSQL, MySQL)
- Local LLM integration (Ollama)
- Secure credential vault
- Basic auto-completion
- Command history
- Configuration management

### Components
- Core application framework
- MCP client architecture
- Security module
- Database module
- UI framework

---

**Release Date:** October 11, 2025
**Next Release:** v2.1.0 (Q1 2026)
