"""
Tests for GraphQL API Layer
"""

import pytest
import sqlite3
from src.api.graphql.server import GraphQLServer, GraphQLConfig
from src.api.graphql.schema_generator import SchemaGenerator
from src.api.graphql.subscriptions import SubscriptionManager


@pytest.fixture
def test_db():
    """Create test database"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create test table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    ''')

    # Insert test data
    cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)",
                  ("test@example.com", "Test User"))
    cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)",
                  ("admin@example.com", "Admin User"))

    conn.commit()

    yield conn

    conn.close()


@pytest.fixture
def graphql_config():
    """Create test GraphQL config"""
    return GraphQLConfig(
        database_url="sqlite:///:memory:",
        enable_playground=True,
        enable_subscriptions=True
    )


class TestSchemaGenerator:
    """Test GraphQL schema generation"""

    def test_initialization(self):
        """Test SchemaGenerator initialization"""
        generator = SchemaGenerator()
        assert generator is not None
        assert isinstance(generator.type_mappings, dict)

    def test_extract_table_metadata(self, test_db):
        """Test extracting table metadata"""
        generator = SchemaGenerator()
        metadata = generator._extract_table_metadata(test_db, ['users'])

        assert 'users' in metadata
        assert len(metadata['users']) > 0

        # Check columns
        columns = {col['name']: col for col in metadata['users']}
        assert 'id' in columns
        assert 'email' in columns
        assert 'name' in columns

    def test_type_mapping(self):
        """Test SQL to GraphQL type mapping"""
        generator = SchemaGenerator()

        assert generator._map_sql_to_graphql_type('INTEGER') == 'Int'
        assert generator._map_sql_to_graphql_type('TEXT') == 'String'
        assert generator._map_sql_to_graphql_type('REAL') == 'Float'
        assert generator._map_sql_to_graphql_type('BOOLEAN') == 'Boolean'

    def test_pascal_case_conversion(self):
        """Test snake_case to PascalCase conversion"""
        generator = SchemaGenerator()

        assert generator._to_pascal_case('user_profile') == 'UserProfile'
        assert generator._to_pascal_case('users') == 'Users'

    def test_camel_case_conversion(self):
        """Test snake_case to camelCase conversion"""
        generator = SchemaGenerator()

        assert generator._to_camel_case('user_profile') == 'userProfile'
        assert generator._to_camel_case('users') == 'users'

    def test_singularize(self):
        """Test word singularization"""
        generator = SchemaGenerator()

        assert generator._singularize('users') == 'user'
        assert generator._singularize('categories') == 'category'
        assert generator._singularize('boxes') == 'boxe'  # Simple implementation


class TestGraphQLServer:
    """Test GraphQL server"""

    def test_initialization(self, graphql_config):
        """Test server initialization"""
        server = GraphQLServer(graphql_config)

        assert server is not None
        assert server.config == graphql_config

    def test_rate_limiting(self, graphql_config):
        """Test rate limiting"""
        server = GraphQLServer(graphql_config)

        user_id = "test_user"

        # Should allow within limit
        for _ in range(graphql_config.rate_limit_per_minute):
            assert server._check_rate_limit(user_id) is True

        # Should deny after limit
        assert server._check_rate_limit(user_id) is False

    def test_cache_operations(self, graphql_config):
        """Test cache operations"""
        server = GraphQLServer(graphql_config)

        # Add to cache
        server.query_cache['test_key'] = {'data': 'test'}
        assert 'test_key' in server.query_cache

        # Clear cache
        server.clear_cache()
        assert len(server.query_cache) == 0


class TestSubscriptionManager:
    """Test subscription management"""

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self):
        """Test subscription lifecycle"""
        manager = SubscriptionManager()

        subscriber_id = "test_subscriber"
        topic = "test_topic"

        # Subscribe
        subscription = await manager.subscribe(subscriber_id, topic)
        assert subscription.id == subscriber_id
        assert subscription.topic == topic
        assert subscriber_id in manager.subscriptions

        # Unsubscribe
        await manager.unsubscribe(subscriber_id)
        assert subscriber_id not in manager.subscriptions

    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """Test publish-subscribe mechanism"""
        manager = SubscriptionManager()

        subscriber_id = "test_subscriber"
        topic = "test_topic"

        # Subscribe
        await manager.subscribe(subscriber_id, topic)

        # Publish
        test_data = {'message': 'test'}
        await manager.publish(topic, test_data)

        # Check message in queue
        assert not manager.queues[subscriber_id].empty()

    @pytest.mark.asyncio
    async def test_filtered_subscription(self):
        """Test subscription with filters"""
        manager = SubscriptionManager()

        subscriber_id = "filtered_subscriber"
        topic = "filtered_topic"
        filters = {'user_id': 'user123'}

        # Subscribe with filters
        await manager.subscribe(subscriber_id, topic, filters)

        # Publish matching data
        await manager.publish(topic, {'user_id': 'user123', 'data': 'test1'})

        # Publish non-matching data
        await manager.publish(topic, {'user_id': 'user456', 'data': 'test2'})

        # Should only receive matching message
        assert manager.queues[subscriber_id].qsize() == 1

    def test_subscriber_count(self):
        """Test getting subscriber counts"""
        manager = SubscriptionManager()

        assert manager.get_subscriber_count() == 0
        assert manager.get_subscriber_count("test_topic") == 0

    def test_get_topics(self):
        """Test getting active topics"""
        manager = SubscriptionManager()

        topics = manager.get_topics()
        assert isinstance(topics, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
