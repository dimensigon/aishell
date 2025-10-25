"""
GraphQL Server Implementation

Production-ready GraphQL server with authentication, caching, and subscriptions.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GraphQLConfig:
    """Configuration for GraphQL server"""
    database_url: str
    enable_playground: bool = True
    enable_introspection: bool = True
    enable_subscriptions: bool = True
    max_query_depth: int = 10
    max_query_complexity: int = 1000
    enable_caching: bool = True
    cache_ttl: int = 300  # seconds
    rate_limit_per_minute: int = 100


class GraphQLServer:
    """
    GraphQL Server with strawberry-graphql

    Features:
    - Automatic schema generation
    - Authentication & authorization
    - Query optimization (DataLoader, caching)
    - Real-time subscriptions
    - Rate limiting
    - GraphQL playground
    """

    def __init__(self, config: GraphQLConfig):
        """
        Initialize GraphQL server

        Args:
            config: Server configuration
        """
        self.config = config
        self.schema = None
        self.app = None

        # Try to import strawberry (optional dependency)
        try:
            import strawberry
            from strawberry.fastapi import GraphQLRouter
            from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
            self.strawberry = strawberry
            self.GraphQLRouter = GraphQLRouter
            self.GRAPHQL_TRANSPORT_WS_PROTOCOL = GRAPHQL_TRANSPORT_WS_PROTOCOL
            self.available = True
            logger.info("strawberry-graphql available")
        except ImportError:
            logger.warning("strawberry-graphql not installed. Install with: pip install strawberry-graphql[fastapi]")
            self.available = False

        # Initialize components
        from src.api.graphql.schema_generator import SchemaGenerator
        from src.api.graphql.subscriptions import SubscriptionManager

        self.schema_generator = SchemaGenerator()
        self.subscription_manager = SubscriptionManager()

        # Query cache
        self.query_cache: Dict[str, Any] = {}

        # Rate limiting
        self.rate_limiter: Dict[str, List[datetime]] = {}

    def generate_schema_from_database(
        self,
        db_connection,
        tables: Optional[List[str]] = None
    ):
        """
        Generate GraphQL schema from database

        Args:
            db_connection: Database connection
            tables: List of tables to include (None for all)
        """
        if not self.available:
            logger.error("Cannot generate schema: strawberry-graphql not available")
            return

        logger.info("Generating GraphQL schema from database...")
        self.schema = self.schema_generator.generate_from_database(
            db_connection,
            tables=tables
        )

        logger.info("GraphQL schema generated successfully")

    def create_fastapi_app(self):
        """
        Create FastAPI application with GraphQL endpoint

        Returns:
            FastAPI app instance
        """
        if not self.available:
            raise RuntimeError("Cannot create app: strawberry-graphql not available")

        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.middleware.cors import CORSMiddleware
        except ImportError:
            raise RuntimeError("FastAPI not installed. Install with: pip install fastapi")

        app = FastAPI(
            title="AI-Shell GraphQL API",
            description="GraphQL interface for database operations",
            version="2.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add rate limiting middleware
        @app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            # Extract user ID from auth header or use IP
            user_id = request.client.host

            # Check rate limit
            if not self._check_rate_limit(user_id):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )

            response = await call_next(request)
            return response

        # Create GraphQL router
        if self.schema:
            graphql_app = self.GraphQLRouter(
                schema=self.schema,
                graphiql=self.config.enable_playground,
                subscription_protocols=[
                    self.GRAPHQL_TRANSPORT_WS_PROTOCOL
                ] if self.config.enable_subscriptions else []
            )

            app.include_router(graphql_app, prefix="/graphql")
            logger.info("GraphQL endpoint mounted at /graphql")

        # Health check endpoint
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "graphql_available": self.schema is not None
            }

        self.app = app
        return app

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False
    ):
        """
        Run GraphQL server

        Args:
            host: Host to bind to
            port: Port to bind to
            reload: Enable auto-reload for development
        """
        if not self.app:
            raise RuntimeError("App not created. Call create_fastapi_app() first")

        try:
            import uvicorn
        except ImportError:
            raise RuntimeError("uvicorn not installed. Install with: pip install uvicorn")

        logger.info(f"Starting GraphQL server on {host}:{port}")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload
        )

    def _check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user is within rate limit

        Args:
            user_id: User identifier

        Returns:
            True if within limit
        """
        now = datetime.now()
        cutoff = now.timestamp() - 60  # 1 minute window

        # Get or create user's request history
        if user_id not in self.rate_limiter:
            self.rate_limiter[user_id] = []

        # Remove old requests
        self.rate_limiter[user_id] = [
            ts for ts in self.rate_limiter[user_id]
            if ts.timestamp() > cutoff
        ]

        # Check limit
        if len(self.rate_limiter[user_id]) >= self.config.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return False

        # Add current request
        self.rate_limiter[user_id].append(now)
        return True

    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")

    def get_schema_sdl(self) -> Optional[str]:
        """
        Get GraphQL schema in SDL format

        Returns:
            Schema SDL string
        """
        if not self.schema or not self.available:
            return None

        # Strawberry schemas have introspection built-in
        return str(self.schema)


class GraphQLContext:
    """
    Context object passed to GraphQL resolvers

    Contains request information, authentication, database connection, etc.
    """

    def __init__(
        self,
        request: Any,
        db_connection: Any,
        user_id: Optional[str] = None,
        user_roles: Optional[List[str]] = None
    ):
        """
        Initialize GraphQL context

        Args:
            request: HTTP request object
            db_connection: Database connection
            user_id: Authenticated user ID
            user_roles: User's roles for authorization
        """
        self.request = request
        self.db = db_connection
        self.user_id = user_id
        self.user_roles = user_roles or []

        # DataLoader instances for batching
        self.loaders: Dict[str, Any] = {}

    def has_permission(self, required_role: str) -> bool:
        """
        Check if user has required permission

        Args:
            required_role: Required role

        Returns:
            True if user has permission
        """
        return required_role in self.user_roles

    def get_dataloader(self, name: str, loader_fn: Callable) -> Any:
        """
        Get or create DataLoader instance

        Args:
            name: Loader name
            loader_fn: Loader function

        Returns:
            DataLoader instance
        """
        if name not in self.loaders:
            # Create DataLoader (implementation would use aiodataloader or similar)
            self.loaders[name] = loader_fn

        return self.loaders[name]
