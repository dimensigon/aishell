"""Comprehensive tests for database module."""

import unittest
import tempfile
import os
from pathlib import Path

from src.database import DatabaseModule, SQLRiskAnalyzer, RiskLevel, NLPToSQL, SQLHistoryManager


class TestSQLRiskAnalyzer(unittest.TestCase):
    """Test SQL risk analysis."""

    def setUp(self):
        self.analyzer = SQLRiskAnalyzer()

    def test_low_risk_select(self):
        """Test LOW risk level for SELECT queries."""
        sql = "SELECT * FROM users;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.LOW.value)
        self.assertFalse(result['requires_confirmation'])
        self.assertTrue(result['safe_to_execute'])

    def test_low_risk_show(self):
        """Test LOW risk level for SHOW queries."""
        sql = "SHOW TABLES;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.LOW.value)
        self.assertFalse(result['requires_confirmation'])

    def test_medium_risk_update_with_where(self):
        """Test MEDIUM risk level for UPDATE with WHERE clause."""
        sql = "UPDATE users SET active = 1 WHERE id = 5;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.MEDIUM.value)
        self.assertFalse(result['requires_confirmation'])
        self.assertIn('MEDIUM RISK', result['warnings'][0])

    def test_medium_risk_delete_with_where(self):
        """Test MEDIUM risk level for DELETE with WHERE clause."""
        sql = "DELETE FROM logs WHERE date < '2024-01-01';"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.MEDIUM.value)
        self.assertFalse(result['requires_confirmation'])

    def test_medium_risk_insert(self):
        """Test MEDIUM risk level for INSERT queries."""
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com');"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.MEDIUM.value)

    def test_high_risk_update_without_where(self):
        """Test HIGH risk level for UPDATE without WHERE clause."""
        sql = "UPDATE users SET active = 0;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.HIGH.value)
        self.assertTrue(result['requires_confirmation'])
        self.assertFalse(result['safe_to_execute'])
        self.assertIn('UPDATE without WHERE', result['warnings'][0])

    def test_high_risk_delete_without_where(self):
        """Test HIGH risk level for DELETE without WHERE clause."""
        sql = "DELETE FROM logs;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.HIGH.value)
        self.assertTrue(result['requires_confirmation'])
        self.assertIn('DELETE without WHERE', result['warnings'][0])

    def test_critical_risk_drop_table(self):
        """Test CRITICAL risk level for DROP TABLE."""
        sql = "DROP TABLE users;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.CRITICAL.value)
        self.assertTrue(result['requires_confirmation'])
        self.assertIn('CRITICAL', result['warnings'][0])
        self.assertIn('permanently delete', result['warnings'][0])

    def test_critical_risk_truncate(self):
        """Test CRITICAL risk level for TRUNCATE."""
        sql = "TRUNCATE TABLE logs;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.CRITICAL.value)
        self.assertTrue(result['requires_confirmation'])

    def test_critical_risk_drop_database(self):
        """Test CRITICAL risk level for DROP DATABASE."""
        sql = "DROP DATABASE production;"
        result = self.analyzer.analyze(sql)

        self.assertEqual(result['risk_level'], RiskLevel.CRITICAL.value)

    def test_common_issues_select_star(self):
        """Test detection of SELECT * issue."""
        sql = "SELECT * FROM large_table;"
        result = self.analyzer.analyze(sql)

        self.assertIn('SELECT *', ' '.join(result['issues']))

    def test_common_issues_no_semicolon(self):
        """Test detection of missing semicolon."""
        sql = "SELECT id FROM users"
        result = self.analyzer.analyze(sql)

        issues_text = ' '.join(result['issues'])
        self.assertIn('semicolon', issues_text.lower())

    def test_confirmation_message(self):
        """Test confirmation message generation."""
        sql = "DROP TABLE users;"
        analysis = self.analyzer.analyze(sql)
        message = self.analyzer.get_confirmation_message(analysis)

        self.assertIn('CRITICAL', message)
        self.assertIn('DROP TABLE users', message)
        self.assertIn('Do you want to proceed?', message)


class TestNLPToSQL(unittest.TestCase):
    """Test NLP to SQL conversion."""

    def setUp(self):
        self.converter = NLPToSQL()

    def test_show_all_pattern(self):
        """Test 'show all' pattern conversion."""
        result = self.converter.convert("show me all users")

        self.assertIsNotNone(result['sql'])
        self.assertEqual(result['sql'], 'SELECT * FROM users;')
        self.assertEqual(result['confidence'], 'high')

    def test_list_pattern(self):
        """Test 'list' pattern conversion."""
        result = self.converter.convert("list products")

        self.assertIsNotNone(result['sql'])
        self.assertEqual(result['sql'], 'SELECT * FROM products;')

    def test_count_pattern(self):
        """Test 'count' pattern conversion."""
        result = self.converter.convert("count orders")

        self.assertIsNotNone(result['sql'])
        self.assertEqual(result['sql'], 'SELECT COUNT(*) FROM orders;')

    def test_how_many_pattern(self):
        """Test 'how many' pattern conversion."""
        result = self.converter.convert("how many customers")

        self.assertEqual(result['sql'], 'SELECT COUNT(*) FROM customers;')

    def test_find_where_pattern(self):
        """Test 'find where' pattern conversion."""
        result = self.converter.convert("find users where status is active")

        self.assertEqual(result['sql'], "SELECT * FROM users WHERE status = active;")

    def test_update_pattern(self):
        """Test 'update' pattern conversion."""
        result = self.converter.convert("update users set active to true where id is 1")

        self.assertEqual(result['sql'], "UPDATE users SET active = true WHERE id = 1;")

    def test_delete_pattern(self):
        """Test 'delete' pattern conversion."""
        result = self.converter.convert("delete from logs where date is 2024-01-01")

        self.assertEqual(result['sql'], "DELETE FROM logs WHERE date = 2024-01-01;")

    def test_unsupported_query(self):
        """Test handling of unsupported queries."""
        result = self.converter.convert("do something complex")

        self.assertIsNone(result['sql'])
        self.assertEqual(result['confidence'], 'none')
        self.assertIn('suggestions', result)

    def test_is_supported(self):
        """Test is_supported method."""
        self.assertTrue(self.converter.is_supported("show users"))
        self.assertFalse(self.converter.is_supported("random text"))


class TestSQLHistoryManager(unittest.TestCase):
    """Test SQL history management."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.history = SQLHistoryManager(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_add_entry(self):
        """Test adding history entry."""
        self.history.add_entry(
            sql="SELECT * FROM users;",
            risk_level="LOW",
            success=True,
            rows_affected=10,
            execution_time=0.05,
        )

        entries = self.history.get_recent(1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['sql'], "SELECT * FROM users;")
        self.assertEqual(entries[0]['risk_level'], "LOW")
        self.assertTrue(entries[0]['success'])

    def test_get_recent(self):
        """Test getting recent entries."""
        for i in range(15):
            self.history.add_entry(
                sql=f"SELECT {i};",
                risk_level="LOW",
                success=True,
            )

        recent = self.history.get_recent(5)
        self.assertEqual(len(recent), 5)
        # Should be most recent first
        self.assertIn("SELECT 14", recent[0]['sql'])

    def test_search(self):
        """Test searching history."""
        self.history.add_entry(sql="SELECT * FROM users;", risk_level="LOW", success=True)
        self.history.add_entry(sql="SELECT * FROM products;", risk_level="LOW", success=True)
        self.history.add_entry(sql="UPDATE users SET active = 1;", risk_level="HIGH", success=True)

        results = self.history.search("users")
        self.assertEqual(len(results), 2)

    def test_get_by_risk_level(self):
        """Test filtering by risk level."""
        self.history.add_entry(sql="SELECT * FROM users;", risk_level="LOW", success=True)
        self.history.add_entry(sql="UPDATE users SET active = 1;", risk_level="HIGH", success=True)
        self.history.add_entry(sql="DROP TABLE old_data;", risk_level="CRITICAL", success=True)

        critical = self.history.get_by_risk_level("CRITICAL")
        self.assertEqual(len(critical), 1)
        self.assertIn("DROP TABLE", critical[0]['sql'])

    def test_get_failed_queries(self):
        """Test getting failed queries."""
        self.history.add_entry(sql="SELECT * FROM users;", risk_level="LOW", success=True)
        self.history.add_entry(
            sql="SELECT * FROM nonexistent;",
            risk_level="LOW",
            success=False,
            error="Table not found",
        )

        failed = self.history.get_failed_queries()
        self.assertEqual(len(failed), 1)
        self.assertFalse(failed[0]['success'])

    def test_statistics(self):
        """Test statistics generation."""
        self.history.add_entry(sql="SELECT 1;", risk_level="LOW", success=True)
        self.history.add_entry(sql="SELECT 2;", risk_level="LOW", success=True)
        self.history.add_entry(sql="UPDATE users;", risk_level="HIGH", success=False, error="Error")

        stats = self.history.get_statistics()

        self.assertEqual(stats['total_queries'], 3)
        self.assertEqual(stats['successful_queries'], 2)
        self.assertEqual(stats['failed_queries'], 1)
        self.assertEqual(stats['risk_level_distribution']['LOW'], 2)
        self.assertEqual(stats['risk_level_distribution']['HIGH'], 1)


class TestDatabaseModule(unittest.TestCase):
    """Test unified database module."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        self.temp_history = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_history.close()

        self.db = DatabaseModule(
            db_path=self.temp_db.name,
            history_file=self.temp_history.name,
            auto_confirm=True,  # Skip confirmations for tests
        )

        # Create test table
        self.db.execute_sql("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                active INTEGER DEFAULT 1
            );
        """)

    def tearDown(self):
        self.db.close()
        os.unlink(self.temp_db.name)
        os.unlink(self.temp_history.name)

    def test_execute_select(self):
        """Test executing SELECT query."""
        # Insert test data
        self.db.execute_sql("INSERT INTO users (name, email) VALUES ('John', 'john@example.com');")

        result = self.db.execute_sql("SELECT * FROM users;")

        self.assertEqual(result['status'], 'success')
        self.assertIsNotNone(result['results'])
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], 'John')

    def test_execute_insert(self):
        """Test executing INSERT query."""
        result = self.db.execute_sql(
            "INSERT INTO users (name, email) VALUES ('Jane', 'jane@example.com');"
        )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['rows_affected'], 1)

    def test_execute_update(self):
        """Test executing UPDATE query."""
        self.db.execute_sql("INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');")

        result = self.db.execute_sql("UPDATE users SET active = 0 WHERE name = 'Bob';")

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['rows_affected'], 1)

    def test_execute_error(self):
        """Test handling SQL errors."""
        result = self.db.execute_sql("SELECT * FROM nonexistent_table;")

        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)

    def test_execute_nlp_success(self):
        """Test NLP query execution."""
        self.db.execute_sql("INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');")

        result = self.db.execute_nlp("show me all users")

        self.assertEqual(result['status'], 'success')
        self.assertIsNotNone(result['results'])
        self.assertIn('conversion', result)

    def test_execute_nlp_failed_conversion(self):
        """Test failed NLP conversion."""
        result = self.db.execute_nlp("do something impossible")

        self.assertEqual(result['status'], 'conversion_failed')

    def test_history_tracking(self):
        """Test that queries are tracked in history."""
        self.db.execute_sql("SELECT * FROM users;")
        self.db.execute_sql("INSERT INTO users (name, email) VALUES ('Test', 'test@example.com');")

        history = self.db.get_history(10)

        self.assertGreaterEqual(len(history), 2)

    def test_get_statistics(self):
        """Test statistics retrieval."""
        self.db.execute_sql("SELECT * FROM users;")

        stats = self.db.get_statistics()

        self.assertIn('total_queries', stats)
        self.assertIn('successful_queries', stats)

    def test_search_history(self):
        """Test history search."""
        self.db.execute_sql("SELECT * FROM users;")

        results = self.db.search_history("users")

        self.assertGreater(len(results), 0)

    def test_context_manager(self):
        """Test database as context manager."""
        with DatabaseModule(auto_confirm=True) as db:
            result = db.execute_sql("SELECT 1;")
            self.assertEqual(result['status'], 'success')

        # Connection should be closed
        self.assertIsNone(db.connection)


if __name__ == '__main__':
    unittest.main()
