"""
AI Query Assistant Demo

Demonstrates v2.0.0 AI-powered query features including:
- Natural language to complex SQL conversion
- Query explanation
- Performance optimization
- Query correction
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ai.query_assistant import QueryAssistant, QueryContext, QueryIntent
from src.ai.conversation_manager import ConversationManager


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_basic_sql_generation():
    """Demo: Basic SQL generation from natural language"""
    print_section("1. Natural Language to SQL Generation")

    # Create context with schema information
    context = QueryContext(
        database_type="sqlite",
        schema_info={
            'users': {
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'constraints': ['PRIMARY KEY']},
                    {'name': 'email', 'type': 'TEXT', 'constraints': ['UNIQUE']},
                    {'name': 'name', 'type': 'TEXT', 'constraints': []},
                    {'name': 'age', 'type': 'INTEGER', 'constraints': []},
                    {'name': 'created_at', 'type': 'TIMESTAMP', 'constraints': []}
                ]
            },
            'orders': {
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'constraints': ['PRIMARY KEY']},
                    {'name': 'user_id', 'type': 'INTEGER', 'constraints': ['FOREIGN KEY']},
                    {'name': 'amount', 'type': 'DECIMAL', 'constraints': []},
                    {'name': 'status', 'type': 'TEXT', 'constraints': []}
                ]
            }
        },
        table_names=['users', 'orders', 'products']
    )

    # Initialize query assistant (will use fallback without API key)
    assistant = QueryAssistant()

    # Example queries
    queries = [
        "show me all users",
        "find users where age is greater than 25",
        "count all orders",
        "get top 10 users by order amount"
    ]

    for nl_query in queries:
        print(f"Natural Language: '{nl_query}'")

        result = assistant.generate_sql(nl_query, context)

        if result.success:
            print(f"✓ Generated SQL: {result.sql_query}")
            if result.explanation:
                print(f"  Explanation: {result.explanation[:100]}...")
            print(f"  Confidence: {result.confidence:.2f}")
        else:
            print(f"✗ Failed: {result.warnings}")

        print()


def demo_query_explanation():
    """Demo: Explaining SQL queries in plain English"""
    print_section("2. Query Explanation")

    assistant = QueryAssistant()
    context = QueryContext(database_type="sqlite")

    # Example queries to explain
    queries = [
        "SELECT * FROM users WHERE age > 25 ORDER BY created_at DESC LIMIT 10",
        "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id",
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = 123"
    ]

    for sql in queries:
        print(f"SQL Query:\n{sql}\n")

        result = assistant.explain_query(sql, context, detail_level="medium")

        if result.success and result.explanation:
            print(f"Explanation:\n{result.explanation}\n")
        else:
            print(f"Could not explain: {result.warnings}\n")


def demo_query_optimization():
    """Demo: Query optimization suggestions"""
    print_section("3. Query Optimization")

    assistant = QueryAssistant()
    context = QueryContext(
        database_type="sqlite",
        schema_info={
            'users': {
                'columns': [
                    {'name': 'id', 'type': 'INTEGER'},
                    {'name': 'email', 'type': 'TEXT'},
                    {'name': 'status', 'type': 'TEXT'}
                ]
            }
        }
    )

    # Queries that could be optimized
    queries = [
        ("SELECT * FROM users", "Selecting all columns"),
        ("SELECT * FROM users WHERE status = 'active'", "Missing index on status"),
        ("SELECT DISTINCT email FROM users", "Using DISTINCT")
    ]

    for sql, description in queries:
        print(f"Query ({description}):\n{sql}\n")

        result = assistant.optimize_query(
            sql,
            context,
            performance_data={'execution_time': 1.5, 'rows_affected': 10000}
        )

        if result.success:
            print("Optimization Suggestions:")
            for i, suggestion in enumerate(result.optimization_suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print(f"Could not optimize: {result.warnings}")

        print()


def demo_query_fixing():
    """Demo: Automatic query correction"""
    print_section("4. Query Error Correction")

    assistant = QueryAssistant()
    context = QueryContext(
        database_type="sqlite",
        table_names=['users', 'orders']
    )

    # Common SQL errors
    errors = [
        ("SELECT * FROM user", "no such table: user"),
        ("SELECT name, email FROM users GROUP BY name", "column email is not in GROUP BY"),
        ("INSERT INTO users (name) VALUES", "syntax error near VALUES")
    ]

    for broken_sql, error_msg in errors:
        print(f"Broken SQL:\n{broken_sql}\n")
        print(f"Error: {error_msg}\n")

        # Note: Without API key, this will return an error
        # With API key, Claude would suggest corrections
        result = assistant.fix_query(broken_sql, error_msg, context)

        if result.success and result.sql_query:
            print(f"✓ Fixed SQL:\n{result.sql_query}\n")
            if result.explanation:
                print(f"Explanation: {result.explanation}\n")
        else:
            print("(Automatic fixing requires ANTHROPIC_API_KEY)\n")


def demo_conversation_context():
    """Demo: Multi-turn conversation with context"""
    print_section("5. Conversational Query Assistant")

    manager = ConversationManager()
    assistant = QueryAssistant()

    # Start conversation
    session_id = manager.start_session()
    print(f"Started conversation session: {session_id}\n")

    context = QueryContext(
        database_type="sqlite",
        table_names=['users', 'orders', 'products']
    )

    # Simulated conversation
    conversation = [
        ("Show me all users", None),
        ("Now filter by age greater than 25", None),
        ("Add an order by clause for the last query", None)
    ]

    for user_input, _ in conversation:
        print(f"User: {user_input}")

        # Add to conversation history
        manager.add_user_message(user_input, session_id)

        # Generate response
        result = assistant.generate_sql(user_input, context)

        response = f"Generated: {result.sql_query}" if result.success else "Could not generate SQL"
        print(f"Assistant: {response}\n")

        # Add assistant response
        manager.add_assistant_message(response, session_id)

    # Show conversation summary
    summary = manager.get_conversation_summary(session_id)
    print(f"Conversation Summary:")
    print(f"  Total messages: {summary['total_messages']}")
    print(f"  Duration: {summary['duration_minutes']:.2f} minutes")


def demo_with_api_key():
    """Demo with actual Claude API (requires ANTHROPIC_API_KEY)"""
    print_section("6. Advanced Features with Claude API")

    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set in environment")
        print("   Set it to enable AI-powered features:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("\nFalling back to pattern-based conversion...")
        return

    print("✓ API key found - using Claude for advanced features\n")

    assistant = QueryAssistant(api_key=api_key)
    context = QueryContext(
        database_type="postgresql",
        schema_info={
            'customers': {
                'columns': [
                    {'name': 'id', 'type': 'SERIAL'},
                    {'name': 'company_name', 'type': 'VARCHAR'},
                    {'name': 'industry', 'type': 'VARCHAR'},
                    {'name': 'revenue', 'type': 'DECIMAL'}
                ]
            }
        }
    )

    # Complex query requiring AI
    complex_query = """
    Get me the top 5 companies by revenue in the technology industry,
    but only include those with more than 100 employees,
    and show their average order value from the last quarter
    """

    print(f"Complex Query:\n{complex_query}\n")

    result = assistant.generate_sql(complex_query, context)

    if result.success:
        print(f"✓ Generated SQL:\n{result.sql_query}\n")
        print(f"Explanation:\n{result.explanation}\n")
        print(f"Confidence: {result.confidence:.2%}")
    else:
        print(f"Failed: {result.warnings}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  AI-Powered Query Assistant Demo - v2.0.0")
    print("="*60)

    try:
        demo_basic_sql_generation()
        demo_query_explanation()
        demo_query_optimization()
        demo_query_fixing()
        demo_conversation_context()
        demo_with_api_key()

        print_section("Demo Complete!")
        print("For production use:")
        print("1. Set ANTHROPIC_API_KEY environment variable")
        print("2. Install: pip install anthropic")
        print("3. Integrate with your database module")
        print("\nSee documentation for more examples.")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
