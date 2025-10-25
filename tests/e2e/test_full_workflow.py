"""End-to-End Full Workflow Tests.

Tests cover complete workflows:
- PyPI Installation
- Database Connection & Query Execution
- Agentic Workflows
- Multi-Tenancy Isolation
- RBAC Enforcement
- Audit Logging
- Plugin System
"""

import unittest
import subprocess
import tempfile
import os
import time
from pathlib import Path
import json


class TestPyPIInstallation(unittest.TestCase):
    """Test PyPI package installation workflow."""

    def test_package_installation(self):
        """Test installing package from PyPI."""
        # Note: This would test actual PyPI installation
        # For now, test local installation
        result = subprocess.run(
            ["pip", "show", "aishell"], capture_output=True, text=True, check=False
        )

        # Package should be installed
        self.assertEqual(result.returncode, 0)
        self.assertIn("aishell", result.stdout.lower())

    def test_command_line_interface(self):
        """Test CLI is accessible after installation."""
        result = subprocess.run(["aishell", "--version"], capture_output=True, text=True, check=False)

        self.assertEqual(result.returncode, 0)

    def test_import_in_python(self):
        """Test importing package in Python."""
        import src

        self.assertIsNotNone(src)


class TestDatabaseWorkflow(unittest.TestCase):
    """Test complete database connection and query workflow."""

    def setUp(self):
        """Set up test database."""
        from src.database import DatabaseModule

        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.db = DatabaseModule(db_path=self.temp_db.name, auto_confirm=True)

        # Create test schema
        self.db.execute_sql(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            );
        """
        )

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_complete_crud_workflow(self):
        """Test complete CRUD operations."""
        # Create
        create_result = self.db.execute_sql(
            "INSERT INTO users (username, email, role) VALUES ('john', 'john@example.com', 'admin');"
        )
        self.assertEqual(create_result["status"], "success")

        # Read
        read_result = self.db.execute_sql("SELECT * FROM users WHERE username = 'john';")
        self.assertEqual(read_result["status"], "success")
        self.assertEqual(len(read_result["results"]), 1)
        self.assertEqual(read_result["results"][0]["username"], "john")

        # Update
        update_result = self.db.execute_sql(
            "UPDATE users SET email = 'john.doe@example.com' WHERE username = 'john';"
        )
        self.assertEqual(update_result["status"], "success")

        # Verify update
        verify_result = self.db.execute_sql("SELECT email FROM users WHERE username = 'john';")
        self.assertEqual(verify_result["results"][0]["email"], "john.doe@example.com")

        # Delete
        delete_result = self.db.execute_sql("DELETE FROM users WHERE username = 'john';")
        self.assertEqual(delete_result["status"], "success")

        # Verify deletion
        final_result = self.db.execute_sql("SELECT * FROM users;")
        self.assertEqual(len(final_result["results"]), 0)

    def test_nlp_query_workflow(self):
        """Test natural language to SQL workflow."""
        # Insert test data
        self.db.execute_sql(
            "INSERT INTO users (username, email) VALUES ('alice', 'alice@example.com');"
        )
        self.db.execute_sql(
            "INSERT INTO users (username, email) VALUES ('bob', 'bob@example.com');"
        )

        # Execute NLP query
        result = self.db.execute_nlp("show me all users")

        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(len(result["results"]), 2)

    def test_query_history_workflow(self):
        """Test query history tracking."""
        # Execute some queries
        self.db.execute_sql("SELECT * FROM users;")
        self.db.execute_sql("INSERT INTO users (username, email) VALUES ('test', 'test@example.com');")

        # Check history
        history = self.db.get_history(10)

        self.assertGreaterEqual(len(history), 2)
        self.assertIn("SELECT", history[0]["sql"] + history[1]["sql"])


class TestAgenticWorkflow(unittest.TestCase):
    """Test complete agentic workflow."""

    def test_agent_coordination_workflow(self):
        """Test multi-agent coordination."""
        from src.agents.coordinator import AgentCoordinator

        coordinator = AgentCoordinator()

        # Create a complex task
        task = {"type": "database_analysis", "target": "users_table", "depth": "comprehensive"}

        # Orchestrate agents
        result = coordinator.orchestrate_task(task)

        self.assertIn("status", result)
        self.assertIn("results", result)

    def test_workflow_execution_with_state(self):
        """Test workflow execution with state management."""
        from src.agents.state.manager import StateManager

        state_mgr = StateManager()

        # Initialize workflow state
        workflow_id = "test_workflow_001"
        state_mgr.save_state(workflow_id, {"step": 1, "status": "started", "data": {}})

        # Simulate workflow progress
        state_mgr.update_state(workflow_id, {"step": 2, "status": "processing"})
        state_mgr.update_state(workflow_id, {"step": 3, "status": "completed", "result": "success"})

        # Verify final state
        final_state = state_mgr.load_state(workflow_id)
        self.assertEqual(final_state["status"], "completed")
        self.assertEqual(final_state["step"], 3)


class TestMultiTenancyWorkflow(unittest.TestCase):
    """Test complete multi-tenancy workflow."""

    def test_tenant_isolation_workflow(self):
        """Test complete tenant isolation."""
        from src.core.tenancy import TenantManager, TenantContext

        manager = TenantManager()

        # Create two tenants
        tenant1 = manager.create_tenant("tenant_1", {"name": "Tenant One"})
        tenant2 = manager.create_tenant("tenant_2", {"name": "Tenant Two"})

        # Create context and store data
        ctx1 = TenantContext("tenant_1")
        ctx2 = TenantContext("tenant_2")

        ctx1.set_data("users", [{"id": 1, "name": "User 1"}])
        ctx2.set_data("users", [{"id": 2, "name": "User 2"}])

        # Verify isolation
        self.assertNotEqual(ctx1.get_data("users"), ctx2.get_data("users"))

    def test_tenant_quota_enforcement_workflow(self):
        """Test tenant quota enforcement."""
        from src.core.tenancy import TenantQuotaManager

        quota_mgr = TenantQuotaManager()

        # Set quota
        quota_mgr.set_quota("tenant_test", max_queries=5, max_storage_mb=100)

        # Use quota
        for i in range(5):
            can_execute = quota_mgr.check_quota("tenant_test", "query")
            self.assertTrue(can_execute)
            quota_mgr.increment_usage("tenant_test", "queries")

        # Should be at limit
        can_execute = quota_mgr.check_quota("tenant_test", "query")
        self.assertFalse(can_execute)


class TestRBACWorkflow(unittest.TestCase):
    """Test complete RBAC workflow."""

    def test_role_based_access_workflow(self):
        """Test complete role-based access control."""
        from src.security.rbac import RBACManager

        rbac = RBACManager()

        # Create roles
        rbac.create_role("admin", permissions=["*"])
        rbac.create_role("analyst", permissions=["db.read", "db.analyze"])
        rbac.create_role("viewer", permissions=["db.read"])

        # Assign roles to users
        rbac.assign_role("user_admin", "admin")
        rbac.assign_role("user_analyst", "analyst")
        rbac.assign_role("user_viewer", "viewer")

        # Test permissions
        self.assertTrue(rbac.has_permission("user_admin", "db.delete"))
        self.assertFalse(rbac.has_permission("user_analyst", "db.delete"))
        self.assertTrue(rbac.has_permission("user_analyst", "db.read"))
        self.assertTrue(rbac.has_permission("user_viewer", "db.read"))
        self.assertFalse(rbac.has_permission("user_viewer", "db.write"))

    def test_permission_inheritance_workflow(self):
        """Test role inheritance workflow."""
        from src.security.rbac import RBACManager

        rbac = RBACManager()

        # Create role hierarchy
        rbac.create_role("user", permissions=["db.read"])
        rbac.create_role("power_user", permissions=["db.write"], inherits_from=["user"])
        rbac.create_role("admin", permissions=["db.delete", "db.admin"], inherits_from=["power_user"])

        rbac.assign_role("test_user", "admin")

        # Admin should inherit all permissions
        self.assertTrue(rbac.has_permission("test_user", "db.read"))  # From user
        self.assertTrue(rbac.has_permission("test_user", "db.write"))  # From power_user
        self.assertTrue(rbac.has_permission("test_user", "db.delete"))  # From admin


class TestAuditLoggingWorkflow(unittest.TestCase):
    """Test complete audit logging workflow."""

    def test_complete_audit_trail(self):
        """Test creating complete audit trail."""
        from src.security.audit import AuditLogger

        logger = AuditLogger()

        # Simulate user session
        logger.log_action("user_123", "login", "system", details={"ip": "192.168.1.1"})

        logger.log_action("user_123", "query_executed", "database", details={"query": "SELECT * FROM users"})

        logger.log_action(
            "user_123",
            "data_modified",
            "users_table",
            details={"action": "UPDATE", "rows": 5},
        )

        logger.log_action("user_123", "logout", "system")

        # Retrieve audit trail
        trail = logger.get_logs(user="user_123")

        self.assertEqual(len(trail), 4)
        self.assertEqual(trail[0]["action"], "login")
        self.assertEqual(trail[-1]["action"], "logout")

    def test_audit_search_and_filter(self):
        """Test searching and filtering audit logs."""
        from src.security.audit import AuditLogger

        logger = AuditLogger()

        # Create varied logs
        logger.log_action("user_1", "login", "system")
        logger.log_action("user_1", "query_executed", "database")
        logger.log_action("user_2", "login", "system")
        logger.log_action("user_2", "data_deleted", "database")

        # Search by action
        login_logs = logger.search_logs(action="login")
        self.assertEqual(len(login_logs), 2)

        # Search by user and action
        user1_queries = logger.search_logs(user="user_1", action="query_executed")
        self.assertEqual(len(user1_queries), 1)


class TestPluginWorkflow(unittest.TestCase):
    """Test complete plugin system workflow."""

    def test_plugin_lifecycle_workflow(self):
        """Test complete plugin lifecycle."""
        from src.plugins.manager import PluginManager

        manager = PluginManager()

        class TestPlugin:
            def __init__(self):
                self.state = "initialized"

            def activate(self):
                self.state = "active"
                return True

            def execute(self, data):
                return f"Processed: {data}"

            def deactivate(self):
                self.state = "inactive"

        # Register plugin
        plugin = TestPlugin()
        manager.register_plugin("test_plugin", plugin)

        # Activate plugin
        manager.activate_plugin("test_plugin")
        self.assertEqual(plugin.state, "active")

        # Use plugin
        result = plugin.execute("test data")
        self.assertEqual(result, "Processed: test data")

        # Deactivate plugin
        manager.deactivate_plugin("test_plugin")
        self.assertEqual(plugin.state, "inactive")


class TestIntegratedWorkflow(unittest.TestCase):
    """Test complete integrated workflow combining all features."""

    def test_full_system_workflow(self):
        """Test complete system workflow with all features."""
        # This is a high-level integration test
        from src.database import DatabaseModule
        from src.security.rbac import RBACManager
        from src.security.audit import AuditLogger
        from src.core.tenancy import TenantManager

        # 1. Setup multi-tenancy
        tenant_mgr = TenantManager()
        tenant = tenant_mgr.create_tenant("acme_corp", {"name": "ACME Corp"})

        # 2. Setup RBAC
        rbac = RBACManager()
        rbac.create_role("data_analyst", permissions=["db.read", "db.analyze"])
        rbac.assign_role("analyst_001", "data_analyst")

        # 3. Setup audit logging
        audit = AuditLogger()
        audit.log_action("analyst_001", "session_start", "system")

        # 4. Execute database operations
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        db = DatabaseModule(db_path=temp_db.name, auto_confirm=True)

        # Create schema
        db.execute_sql(
            """
            CREATE TABLE analytics_data (
                id INTEGER PRIMARY KEY,
                metric TEXT,
                value REAL
            );
        """
        )

        # Check permission
        if rbac.has_permission("analyst_001", "db.read"):
            # Execute query
            result = db.execute_sql("SELECT * FROM analytics_data;")
            audit.log_action("analyst_001", "query_executed", "analytics_data")

            self.assertEqual(result["status"], "success")

        # Cleanup
        db.close()
        os.unlink(temp_db.name)

        # Verify audit trail
        trail = audit.get_logs(user="analyst_001")
        self.assertGreaterEqual(len(trail), 2)


if __name__ == "__main__":
    unittest.main()
