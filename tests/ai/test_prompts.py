"""
Comprehensive tests for Prompt Templates

Tests template rendering, validation, and context formatting.
"""

import pytest
from src.ai.prompt_templates import PromptTemplates
from src.ai.query_assistant import QueryContext


class TestPromptTemplatesInitialization:
    """Test PromptTemplates initialization"""

    def test_init_creates_instance(self):
        """Test PromptTemplates initialization"""
        prompts = PromptTemplates()

        assert prompts is not None
        assert hasattr(prompts, 'generate_sql_prompt')
        assert hasattr(prompts, 'explain_query_prompt')
        assert hasattr(prompts, 'optimize_query_prompt')


class TestGenerateSQLPrompt:
    """Test SQL generation prompt template"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    @pytest.fixture
    def basic_context(self):
        return QueryContext(
            database_type="sqlite",
            table_names=["users", "orders"],
            schema_info={
                "users": {
                    "columns": [
                        {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY"]},
                        {"name": "email", "type": "TEXT", "constraints": ["UNIQUE"]}
                    ]
                }
            }
        )

    def test_generate_sql_prompt_basic(self, prompts, basic_context):
        """Test basic SQL generation prompt"""
        query = "get all users"

        prompt = prompts.generate_sql_prompt(query, basic_context)

        assert query in prompt
        assert "sqlite" in prompt
        assert "users" in prompt
        assert "orders" in prompt

    def test_generate_sql_prompt_includes_schema(self, prompts, basic_context):
        """Test prompt includes schema information"""
        prompt = prompts.generate_sql_prompt("test", basic_context)

        assert "SCHEMA INFORMATION" in prompt
        assert "users" in prompt
        assert "id" in prompt
        assert "email" in prompt
        assert "INTEGER" in prompt

    def test_generate_sql_prompt_includes_recent_queries(self, prompts):
        """Test prompt includes recent queries"""
        context = QueryContext(
            recent_queries=[
                "SELECT * FROM users WHERE active = 1",
                "SELECT COUNT(*) FROM orders",
                "DELETE FROM logs WHERE created_at < '2024-01-01'"
            ]
        )

        prompt = prompts.generate_sql_prompt("test", context)

        assert "RECENT QUERIES" in prompt
        assert "SELECT * FROM users" in prompt
        assert "SELECT COUNT(*)" in prompt

    def test_generate_sql_prompt_no_schema(self, prompts):
        """Test prompt without schema information"""
        context = QueryContext()

        prompt = prompts.generate_sql_prompt("test query", context)

        assert "test query" in prompt
        assert "Not available" in prompt or "Not specified" in prompt

    def test_generate_sql_prompt_includes_instructions(self, prompts, basic_context):
        """Test prompt includes generation instructions"""
        prompt = prompts.generate_sql_prompt("test", basic_context)

        assert "INSTRUCTIONS" in prompt
        assert "Generate a valid SQL query" in prompt
        assert "OUTPUT FORMAT" in prompt
        assert "json" in prompt

    def test_generate_sql_prompt_database_type(self, prompts):
        """Test prompt adapts to database type"""
        context = QueryContext(database_type="postgresql")

        prompt = prompts.generate_sql_prompt("test", context)

        assert "postgresql" in prompt


class TestExplainQueryPrompt:
    """Test query explanation prompt template"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    @pytest.fixture
    def context(self):
        return QueryContext(
            database_type="mysql",
            schema_info={
                "users": {
                    "columns": [{"name": "id"}, {"name": "name"}]
                }
            }
        )

    def test_explain_query_prompt_basic(self, prompts, context):
        """Test basic explanation prompt"""
        sql = "SELECT * FROM users WHERE id = 1"

        prompt = prompts.explain_query_prompt(sql, context)

        assert sql in prompt
        assert "mysql" in prompt

    def test_explain_query_prompt_detail_levels(self, prompts, context):
        """Test different detail levels"""
        sql = "SELECT * FROM users"

        for level in ['simple', 'medium', 'detailed']:
            prompt = prompts.explain_query_prompt(sql, context, detail_level=level)

            assert level.upper() in prompt
            if level == 'simple':
                assert "non-technical" in prompt or "brief" in prompt
            elif level == 'detailed':
                assert "comprehensive" in prompt or "technical" in prompt

    def test_explain_query_prompt_includes_schema(self, prompts, context):
        """Test prompt includes schema context"""
        sql = "SELECT * FROM users"

        prompt = prompts.explain_query_prompt(sql, context)

        assert "users" in prompt
        assert "id" in prompt or "name" in prompt

    def test_explain_query_prompt_instructions(self, prompts, context):
        """Test prompt includes explanation instructions"""
        prompt = prompts.explain_query_prompt("SELECT 1", context)

        assert "INSTRUCTIONS" in prompt
        assert "step by step" in prompt.lower()
        assert "expected output" in prompt.lower()


class TestOptimizeQueryPrompt:
    """Test query optimization prompt template"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    @pytest.fixture
    def context(self):
        return QueryContext(
            database_type="postgresql",
            schema_info={
                "orders": {
                    "columns": [
                        {"name": "id"},
                        {"name": "user_id"},
                        {"name": "created_at"}
                    ]
                }
            }
        )

    def test_optimize_query_prompt_basic(self, prompts, context):
        """Test basic optimization prompt"""
        sql = "SELECT * FROM orders"

        prompt = prompts.optimize_query_prompt(sql, context)

        assert sql in prompt
        assert "postgresql" in prompt
        assert "optimize" in prompt.lower()

    def test_optimize_query_prompt_with_performance_data(self, prompts, context):
        """Test prompt includes performance data"""
        sql = "SELECT * FROM orders"
        perf_data = {
            'execution_time': 2.5,
            'rows_affected': 10000,
            'rows_scanned': 50000
        }

        prompt = prompts.optimize_query_prompt(sql, context, perf_data)

        assert "CURRENT PERFORMANCE" in prompt
        assert "2.5" in prompt
        assert "10000" in prompt
        assert "50000" in prompt

    def test_optimize_query_prompt_no_performance_data(self, prompts, context):
        """Test prompt without performance data"""
        sql = "SELECT * FROM orders"

        prompt = prompts.optimize_query_prompt(sql, context, None)

        assert sql in prompt
        assert "CURRENT PERFORMANCE" not in prompt or "N/A" in prompt

    def test_optimize_query_prompt_includes_goals(self, prompts, context):
        """Test prompt includes optimization goals"""
        prompt = prompts.optimize_query_prompt("SELECT 1", context)

        assert "OPTIMIZATION GOALS" in prompt
        assert "execution speed" in prompt.lower()
        assert "resource consumption" in prompt.lower()

    def test_optimize_query_prompt_output_format(self, prompts, context):
        """Test prompt specifies output format"""
        prompt = prompts.optimize_query_prompt("SELECT 1", context)

        assert "OUTPUT FORMAT" in prompt
        assert "Optimized Query" in prompt
        assert "Index Recommendations" in prompt


class TestFixQueryPrompt:
    """Test query fixing prompt template"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    @pytest.fixture
    def context(self):
        return QueryContext(database_type="sqlite")

    def test_fix_query_prompt_basic(self, prompts, context):
        """Test basic fix query prompt"""
        sql = "SELCT * FROM users"
        error = "Syntax error near SELCT"

        prompt = prompts.fix_query_prompt(sql, error, context)

        assert sql in prompt
        assert error in prompt
        assert "sqlite" in prompt

    def test_fix_query_prompt_includes_error(self, prompts, context):
        """Test prompt prominently includes error message"""
        sql = "SELECT * FROM non_existent_table"
        error = "Table 'non_existent_table' does not exist"

        prompt = prompts.fix_query_prompt(sql, error, context)

        assert "ERROR MESSAGE" in prompt
        assert error in prompt

    def test_fix_query_prompt_instructions(self, prompts, context):
        """Test prompt includes fixing instructions"""
        prompt = prompts.fix_query_prompt("bad sql", "error", context)

        assert "INSTRUCTIONS" in prompt
        assert "root cause" in prompt.lower()
        assert "corrected version" in prompt.lower()

    def test_fix_query_prompt_output_format(self, prompts, context):
        """Test prompt specifies JSON output format"""
        prompt = prompts.fix_query_prompt("bad sql", "error", context)

        assert "OUTPUT FORMAT" in prompt
        assert "json" in prompt
        assert "sql" in prompt
        assert "explanation" in prompt
        assert "best_practices" in prompt


class TestAnalyzeSchemaPrompt:
    """Test schema analysis prompt template"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    @pytest.fixture
    def schema(self):
        return {
            "users": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "email", "type": "TEXT"}
                ],
                "indexes": ["idx_email"],
                "foreign_keys": []
            },
            "orders": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "user_id", "type": "INTEGER"}
                ],
                "foreign_keys": ["user_id -> users.id"]
            }
        }

    def test_analyze_schema_prompt_basic(self, prompts, schema):
        """Test basic schema analysis prompt"""
        prompt = prompts.analyze_schema_prompt(schema)

        assert "users" in prompt
        assert "orders" in prompt
        assert "id" in prompt
        assert "email" in prompt

    def test_analyze_schema_prompt_analysis_types(self, prompts, schema):
        """Test different analysis types"""
        for analysis_type in ['general', 'relationships', 'optimization']:
            prompt = prompts.analyze_schema_prompt(schema, analysis_type)

            assert analysis_type.upper() in prompt
            if analysis_type == 'relationships':
                assert "foreign key" in prompt.lower() or "relationships" in prompt.lower()
            elif analysis_type == 'optimization':
                assert "optimization" in prompt.lower() or "performance" in prompt.lower()

    def test_analyze_schema_prompt_includes_indexes(self, prompts, schema):
        """Test prompt includes index information"""
        prompt = prompts.analyze_schema_prompt(schema)

        assert "idx_email" in prompt
        assert "Indexes" in prompt

    def test_analyze_schema_prompt_includes_foreign_keys(self, prompts, schema):
        """Test prompt includes foreign key information"""
        prompt = prompts.analyze_schema_prompt(schema)

        assert "Foreign Keys" in prompt or "foreign_keys" in prompt
        assert "user_id -> users.id" in prompt

    def test_analyze_schema_prompt_instructions(self, prompts, schema):
        """Test prompt includes analysis instructions"""
        prompt = prompts.analyze_schema_prompt(schema)

        assert "INSTRUCTIONS" in prompt
        assert "insights" in prompt.lower()
        assert "structure" in prompt.lower()


class TestHelperMethods:
    """Test prompt template helper methods"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    def test_format_schema_context_empty(self, prompts):
        """Test formatting empty schema context"""
        context = QueryContext()

        result = prompts._format_schema_context(context)

        assert "Not available" in result or "Schema Information" in result

    def test_format_schema_context_with_data(self, prompts):
        """Test formatting schema with data"""
        context = QueryContext(
            schema_info={
                "users": {
                    "columns": [
                        {"name": "id", "type": "INTEGER", "constraints": ["PRIMARY KEY"]},
                        {"name": "email", "type": "TEXT", "constraints": ["UNIQUE", "NOT NULL"]}
                    ]
                }
            }
        )

        result = prompts._format_schema_context(context)

        assert "users" in result
        assert "id" in result
        assert "INTEGER" in result
        assert "PRIMARY KEY" in result
        assert "email" in result
        assert "UNIQUE" in result

    def test_format_recent_queries_empty(self, prompts):
        """Test formatting empty recent queries"""
        context = QueryContext()

        result = prompts._format_recent_queries(context)

        assert result == ""

    def test_format_recent_queries_with_data(self, prompts):
        """Test formatting recent queries with data"""
        context = QueryContext(
            recent_queries=[
                "SELECT * FROM users",
                "DELETE FROM logs WHERE id = 1",
                "UPDATE users SET active = 1"
            ]
        )

        result = prompts._format_recent_queries(context)

        assert "RECENT QUERIES" in result
        assert "SELECT * FROM users" in result
        assert "DELETE FROM logs" in result

    def test_format_recent_queries_limits_to_three(self, prompts):
        """Test formatting limits to last 3 queries"""
        context = QueryContext(
            recent_queries=[
                "Query 1",
                "Query 2",
                "Query 3",
                "Query 4",
                "Query 5"
            ]
        )

        result = prompts._format_recent_queries(context)

        # Should only include last 3
        assert "Query 3" in result
        assert "Query 4" in result
        assert "Query 5" in result
        assert "Query 1" not in result

    def test_format_schema_info_complete(self, prompts):
        """Test formatting complete schema info"""
        schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "TEXT"}
                ],
                "indexes": ["idx_id", "idx_name"],
                "foreign_keys": ["fk_org_id"]
            }
        }

        result = prompts._format_schema_info(schema)

        assert "Table: users" in result
        assert "Columns:" in result
        assert "id: INTEGER" in result
        assert "name: TEXT" in result
        assert "Indexes:" in result
        assert "idx_id" in result
        assert "Foreign Keys:" in result
        assert "fk_org_id" in result


class TestPromptQuality:
    """Test prompt quality and consistency"""

    @pytest.fixture
    def prompts(self):
        return PromptTemplates()

    @pytest.fixture
    def sample_context(self):
        return QueryContext(
            database_type="postgresql",
            table_names=["users"],
            schema_info={
                "users": {
                    "columns": [{"name": "id", "type": "INTEGER"}]
                }
            }
        )

    def test_all_prompts_are_non_empty(self, prompts, sample_context):
        """Test all prompts generate non-empty strings"""
        sql = "SELECT * FROM users"
        error = "Test error"
        schema = {"users": {}}
        perf_data = {"execution_time": 1.0}

        prompts_to_test = [
            prompts.generate_sql_prompt("test", sample_context),
            prompts.explain_query_prompt(sql, sample_context),
            prompts.optimize_query_prompt(sql, sample_context, perf_data),
            prompts.fix_query_prompt(sql, error, sample_context),
            prompts.analyze_schema_prompt(schema)
        ]

        for prompt in prompts_to_test:
            assert prompt
            assert len(prompt) > 100  # Should be reasonably detailed

    def test_prompts_include_context(self, prompts, sample_context):
        """Test prompts include database context"""
        prompt = prompts.generate_sql_prompt("test", sample_context)

        assert "postgresql" in prompt.lower()
        assert "users" in prompt.lower()

    def test_prompts_have_consistent_structure(self, prompts, sample_context):
        """Test prompts follow consistent structure"""
        sql = "SELECT * FROM users"

        test_prompts = [
            prompts.generate_sql_prompt("test", sample_context),
            prompts.explain_query_prompt(sql, sample_context),
            prompts.optimize_query_prompt(sql, sample_context)
        ]

        # All should have instructions section
        for prompt in test_prompts:
            assert "INSTRUCTIONS" in prompt or "instructions" in prompt.lower()

    def test_prompts_specify_output_format(self, prompts, sample_context):
        """Test prompts specify expected output format"""
        sql = "SELECT * FROM users"

        # These prompts should specify output format
        prompts_with_format = [
            prompts.generate_sql_prompt("test", sample_context),
            prompts.fix_query_prompt(sql, "error", sample_context)
        ]

        for prompt in prompts_with_format:
            assert "OUTPUT FORMAT" in prompt or "format" in prompt.lower()
