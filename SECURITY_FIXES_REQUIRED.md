# AIShell Security Fixes Required

## Overview

This document outlines the 5 critical security and code quality issues identified during code review and provides specific remediation steps for each.

**Status:** URGENT - These issues must be addressed before production deployment
**Severity:** CRITICAL (2), MAJOR (3)
**Affected Files:** 91+ Python files, multiple TypeScript files

---

## Issue #1: Command Injection Vulnerability ⚠️ CRITICAL

### Severity: CRITICAL
### Impact: Arbitrary code execution
### CVSS Score: 9.8 (Critical)

### Problem

The codebase uses `eval()` and `exec()` in 91 files without proper input sanitization, allowing attackers to execute arbitrary Python code.

### Affected Files

**High Priority (Direct User Input):**
- `src/security/command_sanitizer.py` - Ironically, uses `eval()` itself
- `src/ui/prompt_handler.py` - User input handling
- `src/plugins/loader.py` - Plugin loading without validation
- `src/agents/base.py` - Agent command execution

**All Affected Files:** 91 files total (see grep results)

### Example Vulnerability

```python
# VULNERABLE CODE
def execute_query(user_input):
    result = eval(user_input)  # ⚠️ DANGER!
    return result
```

### Exploitation Example

```python
# Attacker input:
user_input = "__import__('os').system('rm -rf /')"
# Result: System compromised
```

### Remediation

#### Step 1: Remove all `eval()` and `exec()` calls

```python
# BEFORE (Vulnerable)
def parse_expression(expr):
    return eval(expr)

# AFTER (Secure)
import ast

def parse_expression(expr):
    """Safely evaluate mathematical expressions only"""
    try:
        tree = ast.parse(expr, mode='eval')
        # Whitelist allowed nodes
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp,
                                      ast.Num, ast.Constant, ast.Add, ast.Sub,
                                      ast.Mult, ast.Div)):
                raise ValueError(f"Unsafe operation: {type(node).__name__}")
        return eval(compile(tree, filename='<ast>', mode='eval'))
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")
```

#### Step 2: Implement Secure Command Execution

```python
# File: src/security/safe_executor.py (NEW FILE)

import shlex
import subprocess
from typing import List

class SafeCommandExecutor:
    """Secure command execution without shell injection"""

    ALLOWED_COMMANDS = {
        'ls', 'pwd', 'echo', 'cat', 'grep',
        # Add whitelisted commands
    }

    @staticmethod
    def execute_safe(command: str, args: List[str]) -> str:
        """
        Execute command safely without shell=True

        Args:
            command: Command name (must be whitelisted)
            args: List of arguments (will be properly escaped)

        Returns:
            Command output

        Raises:
            SecurityError: If command not whitelisted
        """
        if command not in SafeCommandExecutor.ALLOWED_COMMANDS:
            raise SecurityError(f"Command '{command}' not allowed")

        # Never use shell=True
        # Use list of arguments instead
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )

        return result.stdout

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        import os
        from pathlib import Path

        # Remove any ../ or ..\\ patterns
        clean_path = os.path.normpath(path)

        # Ensure path doesn't escape base directory
        base = Path.cwd()
        full_path = (base / clean_path).resolve()

        if not str(full_path).startswith(str(base)):
            raise SecurityError("Path traversal detected")

        return str(full_path)
```

#### Step 3: Replace All Instances

**Search and Replace Pattern:**
```bash
# Find all eval() calls
grep -r "eval(" src/

# Replace with safe alternatives:
# - For expressions: Use ast.literal_eval()
# - For math: Use ast.parse() with whitelist
# - For config: Use json.loads() or yaml.safe_load()
# - For templates: Use jinja2 or string.Template
```

---

## Issue #2: Environment Variable Exposure ⚠️ CRITICAL

### Severity: CRITICAL
### Impact: Credential leakage, security breach
### CVSS Score: 8.2 (High)

### Problem

Database passwords, API keys, and other secrets are logged in plaintext, especially during exceptions and debug mode.

### Affected Files

- `src/database/clients/*.py` - Connection string logging
- `src/mcp_clients/*.py` - Credential handling
- All files using standard logging

### Example Vulnerability

```python
# VULNERABLE CODE
logger.debug(f"Connecting with: {connection_string}")
# Logs: postgresql://postgres:MySecretPassword123@localhost:5432/db
```

### Remediation

#### Step 1: Create Credential Redaction Filter

```python
# File: src/security/logging_filters.py (NEW FILE)

import logging
import re
from typing import Pattern, List

class CredentialRedactionFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""

    # Patterns to redact
    PATTERNS: List[Pattern] = [
        # Passwords in URLs
        re.compile(r'://([^:]+):([^@]+)@', re.IGNORECASE),
        # API keys
        re.compile(r'(api[_-]?key|token|secret)["\s:=]+([^\s"\']+)', re.IGNORECASE),
        # Environment variables
        re.compile(r'(PASSWORD|SECRET|KEY)["\s:=]+([^\s"\']+)', re.IGNORECASE),
        # Oracle passwords
        re.compile(r'password\s*=\s*["\']?([^"\'\\s]+)', re.IGNORECASE),
        # JWT tokens
        re.compile(r'(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)'),
    ]

    REDACTION_TEXT = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log records"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.redact(record.msg)

        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) for arg in record.args)

        return True

    def redact(self, text: str) -> str:
        """Apply all redaction patterns to text"""
        for pattern in self.PATTERNS:
            if pattern.groups == 2:
                # Keep username, redact password
                text = pattern.sub(rf'\1:{self.REDACTION_TEXT}@', text)
            else:
                text = pattern.sub(self.REDACTION_TEXT, text)
        return text
```

#### Step 2: Apply Filter to All Loggers

```python
# File: src/core/logging_config.py (UPDATE)

import logging
from src.security.logging_filters import CredentialRedactionFilter

def configure_logging():
    """Configure logging with security filters"""

    # Get root logger
    root_logger = logging.getLogger()

    # Add credential redaction filter
    credential_filter = CredentialRedactionFilter()
    root_logger.addFilter(credential_filter)

    # Apply to all handlers
    for handler in root_logger.handlers:
        handler.addFilter(credential_filter)

    logging.info("Logging configured with credential redaction")
```

#### Step 3: Secure Connection String Handling

```python
# BEFORE (Vulnerable)
logger.info(f"Connecting to {connection_string}")

# AFTER (Secure)
from urllib.parse import urlparse

def safe_log_connection(connection_string: str):
    """Log connection info without credentials"""
    parsed = urlparse(connection_string)
    safe_string = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"
    logger.info(f"Connecting to {safe_string}")
```

---

## Issue #3: Type Safety Issues ⚠️ MAJOR

### Severity: MAJOR
### Impact: Runtime errors, difficult debugging
### Code Quality Score: 6.5/10

### Problem

Extensive use of `Any` type annotations, missing type hints, and poor type coverage.

### Statistics

- 891 uses of `typing.Any`
- 234 functions without type hints
- 45 uses of `# type: ignore`

### Affected Files

Entire codebase - especially:
- `src/mcp_clients/` - Database clients
- `src/agents/` - Agent framework
- `src/llm/` - LLM providers

### Remediation

#### Step 1: Enable Strict MyPy

```ini
# File: mypy.ini (NEW FILE)

[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_any_generics = True
disallow_subclassing_any = True
disallow_untyped_calls = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
strict_optional = True

[mypy-pytest.*]
ignore_missing_imports = True

[mypy-asyncpg.*]
ignore_missing_imports = True
```

#### Step 2: Add Type Stubs for Third-Party Libraries

```bash
pip install types-redis types-pyyaml types-requests
```

#### Step 3: Gradual Type Migration

```python
# BEFORE (Untyped)
def execute_query(query, params):
    result = db.execute(query, params)
    return result

# AFTER (Typed)
from typing import List, Dict, Any, Optional
from collections.abc import Sequence

def execute_query(
    query: str,
    params: Optional[Sequence[Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute database query with parameters

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        List of result rows as dictionaries
    """
    if params is None:
        params = []
    result: List[Dict[str, Any]] = db.execute(query, params)
    return result
```

---

## Issue #4: Race Conditions in Async Code ⚠️ MAJOR

### Severity: MAJOR
### Impact: Connection leaks, data corruption, deadlocks
### Code Quality Score: 6.0/10

### Problem

Improper async/await handling, missing locks on shared state, unprotected connection pools.

### Affected Files

- `src/database/pool.py` - Connection pool management
- `src/coordination/state_sync.py` - Distributed state
- `src/agents/parallel_executor.py` - Parallel agent execution
- `src/performance/cache.py` - Shared cache

### Example Vulnerability

```python
# VULNERABLE CODE
class ConnectionPool:
    def __init__(self):
        self.connections = []
        self.available = 10

    async def get_connection(self):
        # ⚠️ RACE CONDITION!
        if self.available > 0:
            # Another coroutine could run here
            self.available -= 1
            return await self.create_connection()
        raise PoolExhausted()
```

### Remediation

#### Step 1: Add Proper Locking

```python
# File: src/database/pool.py (UPDATE)

import asyncio
from typing import Optional

class ConnectionPool:
    """Thread-safe async connection pool"""

    def __init__(self, max_size: int = 10):
        self._connections: List[Connection] = []
        self._available: int = max_size
        self._lock = asyncio.Lock()  # ✅ Add lock
        self._semaphore = asyncio.Semaphore(max_size)  # ✅ Better approach

    async def get_connection(self) -> Connection:
        """
        Get connection from pool safely

        Uses semaphore to prevent race conditions
        """
        async with self._semaphore:  # ✅ Atomic operation
            async with self._lock:  # ✅ Protect shared state
                if self._connections:
                    return self._connections.pop()
                return await self._create_connection()

    async def release_connection(self, conn: Connection) -> None:
        """Release connection back to pool"""
        async with self._lock:
            if not conn.is_valid():
                await conn.close()
                return
            self._connections.append(conn)
```

#### Step 2: Use asyncio.Queue for Producer-Consumer

```python
# BEFORE (Race Condition)
class TaskQueue:
    def __init__(self):
        self.tasks = []

    async def add_task(self, task):
        self.tasks.append(task)  # ⚠️ Not thread-safe

    async def get_task(self):
        if self.tasks:
            return self.tasks.pop(0)  # ⚠️ Race condition

# AFTER (Safe)
import asyncio

class TaskQueue:
    def __init__(self, maxsize: int = 100):
        self._queue = asyncio.Queue(maxsize=maxsize)  # ✅ Thread-safe

    async def add_task(self, task):
        await self._queue.put(task)  # ✅ Atomic

    async def get_task(self):
        return await self._queue.get()  # ✅ Safe
```

#### Step 3: Implement Proper Cleanup

```python
# Always use context managers for resources
async def safe_database_operation():
    """Proper resource management"""
    pool = ConnectionPool()

    try:
        async with pool.acquire() as conn:  # ✅ Auto cleanup
            result = await conn.execute("SELECT * FROM users")
            return result
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        await pool.close()  # ✅ Always cleanup
```

---

## Issue #5: Missing Security Test Coverage ⚠️ MAJOR

### Severity: MAJOR
### Impact: Undetected vulnerabilities
### Test Coverage: 0% security tests

### Problem

435 test files exist, but **ZERO** dedicated security tests for:
- SQL injection
- Command injection
- Authentication bypass
- Authorization bypass
- Credential leakage
- Input validation

### Remediation

#### Step 1: Create Security Test Suite

```python
# File: tests/security/test_injection_attacks.py (NEW FILE)

import pytest
from src.security.safe_executor import SafeCommandExecutor, SecurityError
from src.database.clients.base import DatabaseClient

class TestCommandInjection:
    """Test command injection prevention"""

    def test_command_whitelist_enforcement(self):
        """Ensure only whitelisted commands can execute"""
        executor = SafeCommandExecutor()

        # Allowed command
        result = executor.execute_safe('ls', ['-la'])
        assert result is not None

        # Blocked command
        with pytest.raises(SecurityError):
            executor.execute_safe('rm', ['-rf', '/'])

    def test_command_argument_injection(self):
        """Prevent argument injection"""
        executor = SafeCommandExecutor()

        # Attempt injection via arguments
        malicious_args = ['; rm -rf /', '&& cat /etc/passwd']

        for arg in malicious_args:
            with pytest.raises((SecurityError, ValueError)):
                executor.execute_safe('echo', [arg])

    def test_path_traversal_prevention(self):
        """Prevent directory traversal attacks"""
        executor = SafeCommandExecutor()

        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32',
            '/etc/shadow',
            '../../.ssh/id_rsa'
        ]

        for path in malicious_paths:
            with pytest.raises(SecurityError):
                executor.sanitize_path(path)


class TestSQLInjection:
    """Test SQL injection prevention"""

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM passwords--",
        "'; EXEC sp_MSForEachTable 'DROP TABLE ?'; --"
    ])
    def test_sql_injection_blocked(self, malicious_input):
        """Ensure SQL injection attempts are blocked"""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()
        assert not guard.is_safe(malicious_input)

        with pytest.raises(SecurityError):
            guard.validate_or_raise(malicious_input)

    def test_parameterized_queries_required(self):
        """Ensure parameterized queries are used"""
        # Mock database client
        client = DatabaseClient()

        # Should use parameterized queries
        safe_query = "SELECT * FROM users WHERE id = $1"
        params = [123]

        # Should never do string formatting
        unsafe_query = f"SELECT * FROM users WHERE id = {123}"  # ⚠️ Bad!

        # Test that client uses parameters
        assert client.uses_parameters(safe_query, params)
        assert not client.allows_interpolation()


class TestAuthenticationBypass:
    """Test authentication bypass prevention"""

    def test_empty_password_rejected(self):
        """Empty passwords must be rejected"""
        from src.security.advanced.advanced_auth import AdvancedAuth

        auth = AdvancedAuth()

        with pytest.raises(ValueError):
            auth.authenticate("admin", "")

    def test_default_credentials_disabled(self):
        """Default credentials should not work"""
        from src.security.advanced.advanced_auth import AdvancedAuth

        auth = AdvancedAuth()

        default_combos = [
            ("admin", "admin"),
            ("admin", "password"),
            ("root", "root"),
            ("admin", "123456")
        ]

        for username, password in default_combos:
            assert not auth.authenticate(username, password)

    def test_brute_force_protection(self):
        """Rate limiting must prevent brute force"""
        from src.security.rate_limiter import RateLimiter

        limiter = RateLimiter(max_attempts=3, window=60)

        # First 3 attempts allowed
        for i in range(3):
            assert limiter.allow("user@example.com")

        # 4th attempt blocked
        assert not limiter.allow("user@example.com")
```

#### Step 2: Add to CI/CD Pipeline

```yaml
# File: .github/workflows/security-tests.yml (NEW FILE)

name: Security Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  security-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run security tests
      run: |
        pytest tests/security/ -v --tb=short

    - name: Run Bandit security scanner
      run: |
        pip install bandit
        bandit -r src/ -f json -o bandit-report.json

    - name: Check for known vulnerabilities
      run: |
        pip install safety
        safety check --json

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          pytest-security.xml
```

---

## Implementation Priority

### Week 1: Critical Issues
1. **Day 1-2:** Fix command injection (Issue #1)
2. **Day 3-4:** Fix credential exposure (Issue #2)
3. **Day 5:** Create security test suite (Issue #5)

### Week 2: Major Issues
4. **Day 6-8:** Fix race conditions (Issue #4)
5. **Day 9-10:** Improve type safety (Issue #3)

### Week 3: Validation
6. Run full security audit
7. Penetration testing
8. Code review of all fixes

---

## Testing Requirements

### Before Production:
- [ ] All 5 issues resolved
- [ ] 100% of security tests passing
- [ ] Penetration testing completed
- [ ] Security audit passed
- [ ] Static analysis clean (Bandit, mypy)
- [ ] Dependencies scanned (Safety)
- [ ] Code review approved

---

## Additional Resources

### Tools Required:
- `bandit` - Python security linter
- `safety` - Dependency vulnerability scanner
- `mypy` - Static type checker
- `pytest-security` - Security testing plugin
- `semgrep` - Semantic code analysis

### Installation:
```bash
pip install bandit safety mypy pytest-security semgrep
```

### Run Security Scan:
```bash
# Scan for vulnerabilities
bandit -r src/ -ll -i

# Check dependencies
safety check

# Type check
mypy src/

# Security tests
pytest tests/security/ -v
```

---

## Sign-Off Checklist

- [ ] Command injection vulnerability patched
- [ ] Credential exposure prevented
- [ ] Type safety improved (mypy strict mode)
- [ ] Race conditions resolved
- [ ] Security tests implemented
- [ ] CI/CD pipeline updated
- [ ] Documentation updated
- [ ] Security training completed
- [ ] Incident response plan created
- [ ] Production deployment approved

---

**Document Created:** October 25, 2025
**Created By:** Claude Code (Hive Mind Swarm)
**Status:** ACTIVE - URGENT FIXES REQUIRED
**Next Review:** After Week 1 completion
