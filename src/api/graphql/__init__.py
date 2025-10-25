"""
GraphQL API Layer - v2.0.0

Provides GraphQL interface for database operations with:
- Automatic schema generation from database tables
- Query optimization (batching, caching, N+1 prevention)
- Real-time subscriptions for live data
- Authentication integration with RBAC
- Rate limiting per user/role
"""

from src.api.graphql.server import GraphQLServer
from src.api.graphql.schema_generator import SchemaGenerator
from src.api.graphql.resolvers import ResolverFactory
from src.api.graphql.subscriptions import SubscriptionManager

__all__ = [
    'GraphQLServer',
    'SchemaGenerator',
    'ResolverFactory',
    'SubscriptionManager'
]

__version__ = '2.0.0'
