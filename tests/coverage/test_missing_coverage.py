"""
Critical Coverage Gap Tests
===========================

This test suite targets the most critical coverage gaps identified in the codebase.
Tests are prioritized by risk level and impact on system security and reliability.

Priority Breakdown:
- CRITICAL: Security, authentication, data loss prevention (110 files, 0% coverage)
- HIGH: Async operations, database connections, error handling
- MEDIUM: Feature completeness from README.md
- LOW: UI components, formatting utilities

Generated: 2025-10-12
Coverage Analysis: 110/138 files < 50% coverage (79.7% of codebase)
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any


# ==============================================================================
# PRIORITY 1: SECURITY-CRITICAL PATHS (0% Coverage)
# ==============================================================================

class TestSecurityVault:
    """
    Tests for src/security/vault.py (32.4% coverage, 117 missing lines)

    Critical gaps:
    - Encryption key derivation
    - Credential storage/retrieval
    - Auto-redaction on access
    - OS keyring integration fallback
    """

    def test_vault_initialization_without_keyring(self):
        """Test vault initialization when OS keyring is unavailable."""
        from src.security.vault import Vault, MockKeyring

        vault = Vault(use_keyring=False)
        assert vault is not None
        assert isinstance(vault.keyring, type(MockKeyring))

    def test_credential_encryption_decryption(self):
        """Test encryption/decryption of credentials."""
        from src.security.vault import Vault, CredentialType

        vault = Vault(use_keyring=False)

        # Store encrypted credential
        credential_data = {
            'username': 'admin',
            'password': 'super_secret_123',
            'host': 'db.example.com'
        }

        vault.store_credential(
            'test_db',
            credential_data,
            cred_type=CredentialType.DATABASE
        )

        # Retrieve and verify decryption
        retrieved = vault.get_credential('test_db')
        assert retrieved is not None
        assert retrieved['username'] == 'admin'
        assert retrieved['password'] == 'super_secret_123'

    def test_credential_auto_redaction(self):
        """Test automatic redaction of sensitive fields."""
        from src.security.vault import Vault

        vault = Vault(use_keyring=False)

        # Store credential
        vault.store_credential('api_key', {'token': 'sk_live_abcdef123456'})

        # Get redacted version
        redacted = vault.get_credential('api_key', redact=True)
        assert 'sk_live_' not in str(redacted)
        assert '***' in str(redacted) or 'REDACTED' in str(redacted)

    def test_vault_encryption_key_rotation(self):
        """Test encryption key rotation without data loss."""
        from src.security.vault import Vault

        vault = Vault(use_keyring=False)

        # Store credentials
        vault.store_credential('old_cred', {'secret': 'value1'})

        # Rotate key
        vault.rotate_encryption_key()

        # Verify data still accessible
        retrieved = vault.get_credential('old_cred')
        assert retrieved['secret'] == 'value1'

    def test_vault_concurrent_access(self):
        """Test thread-safety of vault operations."""
        import threading
        from src.security.vault import Vault

        vault = Vault(use_keyring=False)
        errors = []

        def store_cred(i):
            try:
                vault.store_credential(f'cred_{i}', {'value': i})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=store_cred, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(vault.list_credentials()) == 50


class TestSecurityEncryption:
    """
    Tests for src/security/encryption.py (0% coverage, 54 missing lines)

    Critical gaps:
    - Fernet encryption implementation
    - Key derivation from password
    - Encrypted file operations
    """

    def test_fernet_encryption_basic(self):
        """Test basic Fernet encryption/decryption."""
        from src.security.encryption import encrypt_data, decrypt_data, generate_key

        key = generate_key()
        plaintext = b"Sensitive data that needs encryption"

        ciphertext = encrypt_data(plaintext, key)
        assert ciphertext != plaintext

        decrypted = decrypt_data(ciphertext, key)
        assert decrypted == plaintext

    def test_password_based_encryption(self):
        """Test PBKDF2 key derivation from password."""
        from src.security.encryption import derive_key_from_password

        password = "my_secure_password"
        salt = b"random_salt_12345678"

        key1 = derive_key_from_password(password, salt)
        key2 = derive_key_from_password(password, salt)

        # Same password and salt should produce same key
        assert key1 == key2

        # Different salt should produce different key
        key3 = derive_key_from_password(password, b"different_salt_87654321")
        assert key1 != key3

    def test_encrypted_file_operations(self):
        """Test reading/writing encrypted files."""
        from src.security.encryption import write_encrypted_file, read_encrypted_file

        key = "test_password"
        data = {"username": "admin", "api_key": "secret"}

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            write_encrypted_file(tmp_path, data, key)
            retrieved = read_encrypted_file(tmp_path, key)
            assert retrieved == data
        finally:
            tmp_path.unlink(missing_ok=True)


class TestSecurityRBAC:
    """
    Tests for src/security/rbac.py (0% coverage, 109 missing lines)

    Critical gaps:
    - Role-based access control
    - Permission checking
    - User role assignment
    """

    def test_rbac_role_creation(self):
        """Test creation of RBAC roles."""
        from src.security.rbac import RBACManager, Role

        rbac = RBACManager()

        admin_role = Role('admin', permissions=['read', 'write', 'delete', 'admin'])
        user_role = Role('user', permissions=['read', 'write'])

        rbac.add_role(admin_role)
        rbac.add_role(user_role)

        assert rbac.get_role('admin') == admin_role
        assert rbac.get_role('user') == user_role

    def test_rbac_permission_check(self):
        """Test permission checking for users."""
        from src.security.rbac import RBACManager, Role

        rbac = RBACManager()
        rbac.add_role(Role('admin', permissions=['read', 'write', 'delete']))
        rbac.assign_user_role('alice', 'admin')

        assert rbac.has_permission('alice', 'read')
        assert rbac.has_permission('alice', 'delete')
        assert not rbac.has_permission('alice', 'execute')

    def test_rbac_hierarchical_permissions(self):
        """Test role inheritance and hierarchical permissions."""
        from src.security.rbac import RBACManager, Role

        rbac = RBACManager()

        # Create role hierarchy
        basic = Role('basic', permissions=['read'])
        advanced = Role('advanced', permissions=['read', 'write'], parent='basic')

        rbac.add_role(basic)
        rbac.add_role(advanced)

        rbac.assign_user_role('bob', 'advanced')

        # Should inherit 'read' from parent
        assert rbac.has_permission('bob', 'read')
        assert rbac.has_permission('bob', 'write')


class TestSecurityAudit:
    """
    Tests for src/security/audit.py (0% coverage, 105 missing lines)

    Critical gaps:
    - Audit logging
    - Security event tracking
    - Compliance reporting
    """

    def test_audit_log_security_event(self):
        """Test logging of security events."""
        from src.security.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = AuditLogger(log_dir=tmpdir)

            audit_log.log_event(
                event_type='authentication',
                user='alice',
                action='login',
                status='success',
                details={'ip': '192.168.1.100'}
            )

            events = audit_log.get_events(event_type='authentication')
            assert len(events) == 1
            assert events[0]['user'] == 'alice'
            assert events[0]['status'] == 'success'

    def test_audit_log_data_access(self):
        """Test logging of data access events."""
        from src.security.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = AuditLogger(log_dir=tmpdir)

            audit_log.log_data_access(
                user='bob',
                resource='customer_database',
                operation='SELECT',
                rows_affected=150
            )

            events = audit_log.get_events(event_type='data_access')
            assert len(events) == 1
            assert events[0]['resource'] == 'customer_database'

    def test_audit_log_retention_policy(self):
        """Test audit log retention and cleanup."""
        from src.security.audit import AuditLogger
        from datetime import datetime, timedelta

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_log = AuditLogger(log_dir=tmpdir, retention_days=7)

            # Create old event
            old_event = {
                'timestamp': (datetime.now() - timedelta(days=30)).isoformat(),
                'event_type': 'test',
                'user': 'alice'
            }

            audit_log._write_event(old_event)

            # Clean up old events
            audit_log.cleanup_old_logs()

            events = audit_log.get_events()
            assert all(
                (datetime.now() - datetime.fromisoformat(e['timestamp'])).days <= 7
                for e in events
            )


class TestSecuritySQLGuard:
    """
    Tests for src/security/sql_guard.py (0% coverage, 67 missing lines)

    Critical gaps:
    - SQL injection detection
    - Dangerous query pattern detection
    - Query sanitization
    """

    def test_sql_injection_detection(self):
        """Test detection of SQL injection attempts."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        # Obvious injection attempts
        assert guard.is_injection("SELECT * FROM users WHERE id = '1' OR '1'='1'")
        assert guard.is_injection("'; DROP TABLE users; --")
        assert guard.is_injection("1'; EXEC sp_executesql @query; --")

        # Safe queries
        assert not guard.is_injection("SELECT * FROM users WHERE id = 123")
        assert not guard.is_injection("SELECT name FROM products WHERE price < 100")

    def test_dangerous_query_patterns(self):
        """Test detection of dangerous SQL patterns."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        # Dangerous patterns
        assert guard.is_dangerous("DROP TABLE users")
        assert guard.is_dangerous("TRUNCATE customers")
        assert guard.is_dangerous("DELETE FROM orders WHERE 1=1")
        assert guard.is_dangerous("GRANT ALL PRIVILEGES ON *.* TO 'user'@'%'")

        # Safe patterns
        assert not guard.is_dangerous("SELECT * FROM users LIMIT 10")
        assert not guard.is_dangerous("UPDATE users SET status = 'active' WHERE id = 5")

    def test_query_sanitization(self):
        """Test SQL query sanitization."""
        from src.security.sql_guard import SQLGuard

        guard = SQLGuard()

        dirty_query = "SELECT * FROM users WHERE name = 'O''Reilly' -- comment"
        sanitized = guard.sanitize(dirty_query)

        assert "O''Reilly" in sanitized or "O\\'Reilly" in sanitized
        assert "--" not in sanitized or guard.is_safe(sanitized)


# ==============================================================================
# PRIORITY 2: ASYNC/DATABASE OPERATIONS (High Risk)
# ==============================================================================

class TestAsyncEventBus:
    """
    Tests for src/core/event_bus.py (0% coverage, 98 missing lines)

    Critical gaps:
    - Async pub/sub messaging
    - Priority queue handling
    - Backpressure management
    - Event ordering guarantees
    """

    @pytest.mark.asyncio
    async def test_event_bus_publish_subscribe(self):
        """Test basic pub/sub functionality."""
        from src.core.event_bus import AsyncEventBus, Event

        bus = AsyncEventBus()
        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        # Subscribe to events
        bus.subscribe('test_event', handler)

        # Publish event
        await bus.publish(Event('test_event', data={'key': 'value'}))

        # Start processing
        await bus.start()
        await asyncio.sleep(0.1)  # Allow processing
        await bus.stop()

        assert len(received_events) == 1
        assert received_events[0].type == 'test_event'
        assert received_events[0].data['key'] == 'value'

    @pytest.mark.asyncio
    async def test_event_bus_priority_ordering(self):
        """Test priority-based event ordering."""
        from src.core.event_bus import AsyncEventBus, Event, EventPriority

        bus = AsyncEventBus()
        received_order = []

        async def handler(event: Event):
            received_order.append(event.data['order'])

        bus.subscribe('priority_test', handler)

        # Publish events in reverse priority order
        await bus.publish(Event('priority_test', {'order': 3}, EventPriority.LOW))
        await bus.publish(Event('priority_test', {'order': 1}, EventPriority.CRITICAL))
        await bus.publish(Event('priority_test', {'order': 2}, EventPriority.HIGH))

        await bus.start()
        await asyncio.sleep(0.1)
        await bus.stop()

        # Should process in priority order
        assert received_order == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_event_bus_backpressure(self):
        """Test backpressure handling when queue is full."""
        from src.core.event_bus import AsyncEventBus, Event

        bus = AsyncEventBus(max_queue_size=5)

        # Fill queue
        for i in range(5):
            await bus.publish(Event('test', {'num': i}))

        # Next publish should handle backpressure
        with pytest.raises(asyncio.QueueFull):
            await bus.publish(Event('test', {'num': 6}), timeout=0.1)

    @pytest.mark.asyncio
    async def test_event_bus_error_handling(self):
        """Test error handling in event handlers."""
        from src.core.event_bus import AsyncEventBus, Event

        bus = AsyncEventBus()
        successful_calls = []

        async def failing_handler(event: Event):
            raise ValueError("Handler error")

        async def success_handler(event: Event):
            successful_calls.append(event)

        bus.subscribe('error_test', failing_handler)
        bus.subscribe('error_test', success_handler)

        await bus.publish(Event('error_test', {}))
        await bus.start()
        await asyncio.sleep(0.1)
        await bus.stop()

        # Success handler should still be called
        assert len(successful_calls) == 1


class TestDatabaseConnectionPool:
    """
    Tests for src/database/pool.py (0% coverage, 68 missing lines)

    Critical gaps:
    - Connection pooling
    - Connection lifecycle management
    - Pool exhaustion handling
    - Auto-scaling
    """

    def test_connection_pool_creation(self):
        """Test creation of database connection pool."""
        from src.database.pool import ConnectionPool

        pool = ConnectionPool(
            connection_string="postgresql://localhost/test",
            max_connections=10
        )

        assert pool.max_connections == 10
        assert pool.available_connections == 10
        assert pool.active_connections == 0

    def test_connection_acquisition_release(self):
        """Test acquiring and releasing connections."""
        from src.database.pool import ConnectionPool

        pool = ConnectionPool("postgresql://localhost/test", max_connections=5)

        # Acquire connections
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()

        assert pool.active_connections == 2
        assert pool.available_connections == 3

        # Release connections
        pool.release_connection(conn1)
        pool.release_connection(conn2)

        assert pool.active_connections == 0
        assert pool.available_connections == 5

    def test_connection_pool_exhaustion(self):
        """Test behavior when connection pool is exhausted."""
        from src.database.pool import ConnectionPool

        pool = ConnectionPool("postgresql://localhost/test", max_connections=2)

        conn1 = pool.get_connection()
        conn2 = pool.get_connection()

        # Pool is exhausted
        with pytest.raises(Exception, match="pool exhausted"):
            pool.get_connection(timeout=0.1)

    def test_connection_pool_manager(self):
        """Test multi-database connection pool management."""
        from src.database.pool import ConnectionPoolManager

        manager = ConnectionPoolManager()

        # Create pools for different databases
        manager.create_pool('db1', 'postgresql://localhost/db1', max_connections=10)
        manager.create_pool('db2', 'mysql://localhost/db2', max_connections=5)

        # Get connections from different pools
        conn1 = manager.get_connection('db1')
        conn2 = manager.get_connection('db2')

        assert conn1 is not None
        assert conn2 is not None

        # Release connections
        manager.release_connection('db1', conn1)
        manager.release_connection('db2', conn2)


class TestHealthCheckSystem:
    """
    Tests for src/core/health_checks.py (0% coverage, 166 missing lines)

    Critical gaps:
    - Async health check execution
    - Parallel check execution
    - Timeout handling
    - Built-in system checks
    """

    @pytest.mark.asyncio
    async def test_health_check_runner_basic(self):
        """Test basic health check execution."""
        from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

        runner = HealthCheckRunner()

        # Register custom check
        def check_memory():
            return True  # Mock always passes

        runner.register_check(
            HealthCheck(
                name='memory_check',
                description='Check available memory',
                check_function=check_memory,
                is_async=False,
                timeout=2.0
            )
        )

        results = await runner.run_all_checks()

        assert 'memory_check' in [r.name for r in results]
        memory_result = next(r for r in results if r.name == 'memory_check')
        assert memory_result.status == HealthStatus.PASS

    @pytest.mark.asyncio
    async def test_health_check_parallel_execution(self):
        """Test parallel execution of health checks."""
        import time
        from src.core.health_checks import HealthCheckRunner, HealthCheck

        runner = HealthCheckRunner()

        async def slow_check():
            await asyncio.sleep(0.5)
            return True

        # Register multiple slow checks
        for i in range(5):
            runner.register_check(
                HealthCheck(
                    name=f'slow_check_{i}',
                    description='Slow check',
                    check_function=slow_check,
                    is_async=True,
                    timeout=2.0
                )
            )

        start = time.time()
        results = await runner.run_all_checks()
        duration = time.time() - start

        # Should complete in ~0.5s (parallel), not 2.5s (sequential)
        assert duration < 1.0
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_health_check_timeout_handling(self):
        """Test timeout handling for hung checks."""
        from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

        runner = HealthCheckRunner()

        async def hung_check():
            await asyncio.sleep(10)  # Exceeds timeout
            return True

        runner.register_check(
            HealthCheck(
                name='hung_check',
                description='Check that hangs',
                check_function=hung_check,
                is_async=True,
                timeout=0.5
            )
        )

        results = await runner.run_all_checks()

        hung_result = next(r for r in results if r.name == 'hung_check')
        assert hung_result.status == HealthStatus.FAIL
        assert 'timeout' in hung_result.message.lower()

    @pytest.mark.asyncio
    async def test_health_check_builtin_checks(self):
        """Test built-in health checks."""
        from src.core.health_checks import HealthCheckRunner

        runner = HealthCheckRunner()

        # Should have built-in checks registered
        results = await runner.run_all_checks()

        check_names = [r.name for r in results]
        assert 'filesystem_check' in check_names or 'memory_check' in check_names


# ==============================================================================
# PRIORITY 3: README FEATURE COMPLETENESS
# ==============================================================================

class TestLLMManager:
    """
    Tests for src/llm/manager.py (26.2% coverage, 118 missing lines)

    Missing from README "LLM Integration" section:
    - Local LLM support (Ollama)
    - Cloud provider fallback
    - Intent analysis
    - Model switching
    """

    @pytest.mark.asyncio
    async def test_llm_manager_ollama_connection(self):
        """Test connection to Ollama local LLM."""
        from src.llm.manager import LLMManager

        manager = LLMManager(provider='ollama', model='llama2:7b')

        # Mock successful connection
        with patch('src.llm.manager.OllamaClient') as mock:
            mock.return_value.is_available.return_value = True

            is_available = await manager.check_availability()
            assert is_available

    @pytest.mark.asyncio
    async def test_llm_manager_provider_fallback(self):
        """Test fallback to cloud provider when local LLM unavailable."""
        from src.llm.manager import LLMManager

        manager = LLMManager(
            provider='ollama',
            fallback_provider='openai'
        )

        with patch('src.llm.manager.OllamaClient') as ollama_mock:
            ollama_mock.return_value.is_available.return_value = False

            with patch('src.llm.manager.OpenAIClient') as openai_mock:
                openai_mock.return_value.is_available.return_value = True

                # Should fallback to OpenAI
                response = await manager.complete("Test prompt")
                assert response is not None

    @pytest.mark.asyncio
    async def test_llm_intent_analysis(self):
        """Test AI-powered intent analysis for commands."""
        from src.llm.manager import LLMManager

        manager = LLMManager(provider='mock')

        command = "find all log files larger than 100MB"
        intent = await manager.analyze_intent(command)

        assert intent is not None
        assert 'action' in intent
        assert intent['action'] in ['search', 'find', 'locate']


class TestVectorStore:
    """
    Tests for src/vector/store.py (20.8% coverage)

    Missing from README "Vector-Based Auto-completion" section:
    - FAISS semantic search
    - Command similarity
    - Context-aware suggestions
    """

    def test_vector_store_initialization(self):
        """Test FAISS vector store initialization."""
        from src.vector.store import VectorStore

        store = VectorStore(dimension=384)
        assert store.dimension == 384
        assert store.index is not None

    def test_vector_store_add_and_search(self):
        """Test adding and searching vectors."""
        from src.vector.store import VectorStore
        import numpy as np

        store = VectorStore(dimension=384)

        # Add vectors
        vectors = np.random.random((10, 384)).astype('float32')
        metadata = [{'command': f'cmd_{i}'} for i in range(10)]

        store.add_vectors(vectors, metadata)

        # Search for similar
        query = np.random.random((1, 384)).astype('float32')
        results = store.search(query, k=3)

        assert len(results) == 3

    def test_vector_store_semantic_command_search(self):
        """Test semantic search for similar commands."""
        from src.vector.store import VectorStore
        from src.vector.autocomplete import CommandCompleter

        completer = CommandCompleter()

        # Add command history
        completer.add_command("git commit -m 'fix bug'")
        completer.add_command("git push origin main")
        completer.add_command("docker build -t myapp .")

        # Search for similar commands
        suggestions = completer.get_suggestions("git commit")

        assert len(suggestions) > 0
        assert any('commit' in s for s in suggestions)


class TestAgentWorkflows:
    """
    Tests for src/agents/workflow_orchestrator.py (27.8% coverage)

    Missing from README "Agentic Workflows" section:
    - Multi-step task execution
    - Agent coordination
    - State persistence
    - Error recovery
    """

    @pytest.mark.asyncio
    async def test_workflow_multi_step_execution(self):
        """Test multi-step workflow execution."""
        from src.agents.workflow_orchestrator import WorkflowOrchestrator
        from src.agents.base import ExecutionStep

        orchestrator = WorkflowOrchestrator()

        steps = [
            ExecutionStep(name='step1', action='backup_db', params={}),
            ExecutionStep(name='step2', action='compress', params={}),
            ExecutionStep(name='step3', action='upload', params={})
        ]

        with patch('src.agents.workflow_orchestrator.execute_tool') as mock:
            mock.return_value = {'success': True}

            result = await orchestrator.execute_workflow(steps)

            assert result.success
            assert len(result.completed_steps) == 3

    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self):
        """Test workflow error recovery and rollback."""
        from src.agents.workflow_orchestrator import WorkflowOrchestrator
        from src.agents.base import ExecutionStep

        orchestrator = WorkflowOrchestrator()

        steps = [
            ExecutionStep(name='step1', action='create_resource', params={}),
            ExecutionStep(name='step2', action='failing_action', params={}),
            ExecutionStep(name='step3', action='finalize', params={})
        ]

        with patch('src.agents.workflow_orchestrator.execute_tool') as mock:
            def side_effect(step):
                if step.action == 'failing_action':
                    raise Exception("Step failed")
                return {'success': True}

            mock.side_effect = side_effect

            result = await orchestrator.execute_workflow(steps, rollback_on_error=True)

            assert not result.success
            assert result.rollback_executed


# ==============================================================================
# PRIORITY 4: ERROR HANDLING PATHS
# ==============================================================================

class TestDatabaseRiskAnalyzer:
    """
    Tests for src/database/risk_analyzer.py (25.4% coverage)

    Critical error paths:
    - SQL impact estimation
    - Risk assessment for destructive operations
    - Table/row count predictions
    """

    def test_risk_analyzer_drop_table(self):
        """Test risk analysis for DROP TABLE operations."""
        from src.database.risk_analyzer import RiskAnalyzer

        analyzer = RiskAnalyzer()

        query = "DROP TABLE users"
        risk = analyzer.analyze_risk(query)

        assert risk.level == 'CRITICAL'
        assert risk.affected_tables == ['users']
        assert risk.is_destructive

    def test_risk_analyzer_delete_with_where(self):
        """Test risk analysis for DELETE with WHERE clause."""
        from src.database.risk_analyzer import RiskAnalyzer

        analyzer = RiskAnalyzer()

        query = "DELETE FROM orders WHERE created_at < '2023-01-01'"
        risk = analyzer.analyze_risk(query)

        assert risk.level in ['HIGH', 'MEDIUM']
        assert not risk.affects_all_rows

    def test_risk_analyzer_delete_no_where(self):
        """Test risk analysis for DELETE without WHERE (deletes all rows)."""
        from src.database.risk_analyzer import RiskAnalyzer

        analyzer = RiskAnalyzer()

        query = "DELETE FROM customers"
        risk = analyzer.analyze_risk(query)

        assert risk.level == 'CRITICAL'
        assert risk.affects_all_rows


class TestMCPClientRetry:
    """
    Tests for src/mcp_clients/retry.py (0% coverage, 245 missing lines)

    Critical error paths:
    - Connection retry logic
    - Exponential backoff
    - Circuit breaker pattern
    - Timeout handling
    """

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test exponential backoff retry strategy."""
        from src.mcp_clients.retry import RetryStrategy
        import time

        strategy = RetryStrategy(max_retries=3, base_delay=0.1)

        attempts = []

        async def failing_operation():
            attempts.append(time.time())
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            await strategy.execute(failing_operation)

        # Should have attempted max_retries times
        assert len(attempts) == 3

        # Delays should be exponential
        if len(attempts) >= 3:
            delay1 = attempts[1] - attempts[0]
            delay2 = attempts[2] - attempts[1]
            assert delay2 > delay1

    @pytest.mark.asyncio
    async def test_retry_circuit_breaker(self):
        """Test circuit breaker pattern for repeated failures."""
        from src.mcp_clients.retry import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)

        async def failing_operation():
            raise ConnectionError("Connection failed")

        # Should allow first few attempts
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_operation)

        # Circuit should be open now
        assert breaker.is_open()

        # Should immediately reject without trying
        with pytest.raises(Exception, match="circuit.*open"):
            await breaker.call(failing_operation)


# ==============================================================================
# COVERAGE IMPROVEMENT ROADMAP
# ==============================================================================

"""
COVERAGE IMPROVEMENT ROADMAP
============================

Phase 1: Security-Critical (Week 1-2)
--------------------------------------
Files to prioritize:
1. src/security/vault.py - Credential encryption/storage
2. src/security/encryption.py - Fernet encryption primitives
3. src/security/rbac.py - Role-based access control
4. src/security/audit.py - Security audit logging
5. src/security/sql_guard.py - SQL injection prevention

Target: Bring security/* from 0-32% to >80% coverage

Phase 2: Async/Database Operations (Week 3-4)
----------------------------------------------
Files to prioritize:
1. src/core/event_bus.py - Async messaging infrastructure
2. src/database/pool.py - Connection pooling
3. src/core/health_checks.py - Health monitoring
4. src/mcp_clients/retry.py - Retry and circuit breaker logic
5. src/database/ha.py - High availability features

Target: Bring async/database from 0-44% to >70% coverage

Phase 3: README Feature Completeness (Week 5-6)
------------------------------------------------
Files to prioritize:
1. src/llm/manager.py - LLM integration (26% -> 80%)
2. src/vector/store.py - Vector search (20% -> 80%)
3. src/agents/workflow_orchestrator.py - Workflows (27% -> 80%)
4. src/agents/tools/registry.py - Tool registry (35% -> 80%)
5. src/agents/safety/controller.py - Safety system (19% -> 80%)

Target: Ensure all README-advertised features have >80% coverage

Phase 4: Plugin & Enterprise (Week 7-8)
----------------------------------------
Files to prioritize:
1. src/plugins/plugin_manager.py - Plugin system (0% -> 70%)
2. src/core/tenancy.py - Multi-tenancy (0% -> 70%)
3. src/enterprise/tenancy/tenant_manager.py - Tenant management (33% -> 80%)
4. src/plugins/hooks.py - Plugin hooks (0% -> 70%)

Target: Enterprise features >70% coverage

Phase 5: Error Handling & Edge Cases (Week 9-10)
-------------------------------------------------
Focus on:
- Network timeout scenarios
- Database connection failures
- Memory exhaustion
- Concurrent access race conditions
- Invalid input validation
- Resource cleanup on errors

Target: All critical error paths tested

Expected Outcomes
-----------------
- Overall coverage: 85% -> 95%
- Security modules: 0-32% -> >80%
- Database/async: 0-44% -> >70%
- Zero modules with <50% coverage
- All README features have tests
- All error handling paths covered
"""
