"""
GraphQL API Demo

Demonstrates v2.0.0 GraphQL API features including:
- Automatic schema generation from database
- CRUD operations via GraphQL
- Real-time subscriptions
- Query optimization and batching
"""

import sys
import asyncio
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.graphql.server import GraphQLServer, GraphQLConfig
from src.api.graphql.subscriptions import SubscriptionManager


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def create_demo_database():
    """Create demo database with sample data"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            views INTEGER DEFAULT 0,
            published BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Insert sample data
    users = [
        ('alice@example.com', 'Alice Smith', 28, 1),
        ('bob@example.com', 'Bob Johnson', 35, 1),
        ('charlie@example.com', 'Charlie Brown', 42, 0)
    ]

    for email, name, age, active in users:
        cursor.execute(
            "INSERT INTO users (email, name, age, active) VALUES (?, ?, ?, ?)",
            (email, name, age, active)
        )

    posts = [
        (1, 'First Post', 'Hello world!', 100, 1),
        (1, 'Second Post', 'Another post by Alice', 50, 1),
        (2, 'Bob\'s Post', 'Thoughts by Bob', 25, 1),
        (3, 'Draft Post', 'Not published yet', 0, 0)
    ]

    for user_id, title, content, views, published in posts:
        cursor.execute(
            "INSERT INTO posts (user_id, title, content, views, published) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, content, views, published)
        )

    conn.commit()
    return conn


def demo_schema_generation():
    """Demo: Automatic schema generation"""
    print_section("1. Automatic Schema Generation")

    # Create demo database
    db = create_demo_database()

    # Create GraphQL server
    config = GraphQLConfig(
        database_url="sqlite:///:memory:",
        enable_playground=True,
        enable_introspection=True
    )

    server = GraphQLServer(config)

    if not server.available:
        print("⚠️  strawberry-graphql not installed")
        print("   Install with: pip install strawberry-graphql[fastapi]")
        return None, None

    # Generate schema from database
    server.generate_schema_from_database(db, tables=['users', 'posts'])

    print("✓ GraphQL schema generated from database tables: users, posts\n")

    # Show schema (if available)
    schema_sdl = server.get_schema_sdl()
    if schema_sdl:
        print("Generated Schema (SDL):")
        print(schema_sdl[:500] + "...")
    else:
        print("Schema generated successfully")

    return server, db


def demo_graphql_queries():
    """Demo: GraphQL query examples"""
    print_section("2. GraphQL Query Examples")

    print("Example GraphQL queries:\n")

    # Query 1: List all users
    query1 = """
    query {
      users(limit: 10) {
        id
        email
        name
        active
      }
    }
    """
    print("1. List all users:")
    print(query1)

    # Query 2: Get single user by ID
    query2 = """
    query {
      user(id: 1) {
        id
        name
        email
        posts {
          id
          title
          views
        }
      }
    }
    """
    print("2. Get user with their posts:")
    print(query2)

    # Query 3: Filter and pagination
    query3 = """
    query {
      users(where: "active = 1", limit: 5, offset: 0) {
        id
        name
        age
      }
    }
    """
    print("3. Filter active users:")
    print(query3)

    # Query 4: Aggregations
    query4 = """
    query {
      posts(limit: 100) {
        id
        title
        views
      }
    }
    """
    print("4. Get posts with view counts:")
    print(query4)


def demo_graphql_mutations():
    """Demo: GraphQL mutation examples"""
    print_section("3. GraphQL Mutation Examples")

    print("Example GraphQL mutations:\n")

    # Mutation 1: Create user
    mutation1 = """
    mutation {
      createUser(input: {
        email: "newuser@example.com"
        name: "New User"
        age: 30
        active: true
      }) {
        id
        email
        name
      }
    }
    """
    print("1. Create new user:")
    print(mutation1)

    # Mutation 2: Update user
    mutation2 = """
    mutation {
      updateUser(id: 1, input: {
        age: 29
      }) {
        id
        name
        age
      }
    }
    """
    print("2. Update user:")
    print(mutation2)

    # Mutation 3: Delete user
    mutation3 = """
    mutation {
      deleteUser(id: 3)
    }
    """
    print("3. Delete user:")
    print(mutation3)


async def demo_subscriptions():
    """Demo: Real-time subscriptions"""
    print_section("4. Real-Time Subscriptions")

    manager = SubscriptionManager()

    print("Setting up real-time subscriptions...\n")

    # Example subscription
    subscription = """
    subscription {
      tableChanges(tableName: "users", operation: "INSERT") {
        operation
        table
        recordId
        data
      }
    }
    """

    print("Example subscription:")
    print(subscription)
    print()

    # Simulate subscription
    print("Simulating subscription events:\n")

    subscriber_id = "demo_subscriber"

    # Subscribe to table changes
    await manager.subscribe(subscriber_id, "table:users")

    # Publish some events
    events = [
        {
            'operation': 'INSERT',
            'table': 'users',
            'record_id': 4,
            'data': {'email': 'dave@example.com', 'name': 'Dave Wilson'}
        },
        {
            'operation': 'UPDATE',
            'table': 'users',
            'record_id': 1,
            'data': {'age': 29}
        }
    ]

    for event in events:
        await manager.publish("table:users", event)
        print(f"Published: {event['operation']} on {event['table']}")

    print(f"\n✓ {manager.get_subscriber_count('table:users')} subscribers notified")

    # Unsubscribe
    await manager.unsubscribe(subscriber_id)


def demo_advanced_features():
    """Demo: Advanced GraphQL features"""
    print_section("5. Advanced Features")

    print("Advanced GraphQL API features:\n")

    print("✓ Query Optimization:")
    print("  - DataLoader batching (N+1 query prevention)")
    print("  - Query result caching with TTL")
    print("  - Query complexity analysis")
    print("  - Automatic index recommendations")
    print()

    print("✓ Authentication & Authorization:")
    print("  - JWT token authentication")
    print("  - Role-based access control (RBAC)")
    print("  - Field-level permissions")
    print("  - Rate limiting per user/role")
    print()

    print("✓ Real-Time Features:")
    print("  - WebSocket subscriptions")
    print("  - Live query updates")
    print("  - Topic-based pub/sub")
    print("  - Connection pooling")
    print()

    print("✓ Developer Experience:")
    print("  - GraphQL Playground (GraphiQL)")
    print("  - Schema introspection")
    print("  - Automatic API documentation")
    print("  - Type-safe client generation")


def demo_server_deployment():
    """Demo: Server deployment"""
    print_section("6. Server Deployment")

    print("To deploy GraphQL server:\n")

    print("1. Install dependencies:")
    print("   pip install strawberry-graphql[fastapi] uvicorn\n")

    print("2. Create server instance:")
    print("""
    from src.api.graphql.server import GraphQLServer, GraphQLConfig

    config = GraphQLConfig(
        database_url="sqlite:///./database.db",
        enable_playground=True,
        enable_subscriptions=True,
        rate_limit_per_minute=100
    )

    server = GraphQLServer(config)
    server.generate_schema_from_database(db_connection)
    app = server.create_fastapi_app()
    """)

    print("\n3. Run server:")
    print("   uvicorn app:app --host 0.0.0.0 --port 8000 --reload\n")

    print("4. Access endpoints:")
    print("   - GraphQL API: http://localhost:8000/graphql")
    print("   - Playground: http://localhost:8000/graphql")
    print("   - Health check: http://localhost:8000/health\n")

    print("5. Example client query:")
    print("""
    import requests

    query = '''
    query {
      users {
        id
        name
        email
      }
    }
    '''

    response = requests.post(
        'http://localhost:8000/graphql',
        json={'query': query}
    )

    print(response.json())
    """)


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  GraphQL API Demo - v2.0.0")
    print("="*60)

    try:
        # Synchronous demos
        server, db = demo_schema_generation()
        demo_graphql_queries()
        demo_graphql_mutations()

        # Async demos
        asyncio.run(demo_subscriptions())

        demo_advanced_features()
        demo_server_deployment()

        # Cleanup
        if db:
            db.close()

        print_section("Demo Complete!")
        print("GraphQL API features demonstrated:")
        print("  ✓ Automatic schema generation")
        print("  ✓ CRUD operations (Query & Mutation)")
        print("  ✓ Real-time subscriptions")
        print("  ✓ Query optimization")
        print("  ✓ Authentication integration")
        print("\nFor production deployment:")
        print("  1. Install: pip install strawberry-graphql[fastapi] uvicorn")
        print("  2. Configure authentication & RBAC")
        print("  3. Set up monitoring and logging")
        print("  4. Enable HTTPS/TLS")
        print("  5. Configure CORS appropriately")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
