"""
Pytest configuration for AIShell tests.

Ensures src module is importable during test discovery and execution.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
import pytest
import numpy as np

# Add project root to Python path so 'src' can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Database Client Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_cassandra_cluster():
    """Mock Cassandra Cluster"""
    cluster = Mock()
    cluster.connect = Mock()
    cluster.shutdown = Mock()

    # Mock metadata
    mock_metadata = Mock()
    mock_metadata.cluster_name = "test_cluster"
    mock_metadata.partitioner = "Murmur3Partitioner"

    # Mock hosts
    mock_host = Mock()
    mock_host.__str__ = Mock(return_value="127.0.0.1")
    mock_metadata.all_hosts = Mock(return_value=[mock_host])
    mock_metadata.keyspaces = {"test_keyspace": Mock()}
    mock_metadata.token_map = {}

    cluster.metadata = mock_metadata

    return cluster


@pytest.fixture
def mock_cassandra_session():
    """Mock Cassandra Session"""
    session = Mock()

    # Mock execute - return mock result set
    mock_result = []
    session.execute = Mock(return_value=mock_result)
    session.execute_async = Mock(return_value=Mock())
    session.prepare = Mock(return_value=Mock())
    session.shutdown = Mock()
    session.set_keyspace = Mock()

    return session


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB boto3 client"""
    client = Mock()

    # Mock table operations
    client.create_table = Mock(return_value={'TableDescription': {'TableName': 'test_table'}})
    client.delete_table = Mock(return_value={'TableDescription': {'TableName': 'test_table'}})
    client.list_tables = Mock(return_value={'TableNames': ['table1', 'table2']})
    client.describe_table = Mock(return_value={
        'Table': {
            'TableName': 'test_table',
            'KeySchema': [],
            'AttributeDefinitions': []
        }
    })

    return client


@pytest.fixture
def mock_dynamodb_resource():
    """Mock DynamoDB boto3 resource"""
    resource = Mock()

    # Mock table
    mock_table = Mock()
    mock_table.put_item = Mock(return_value={})
    mock_table.get_item = Mock(return_value={'Item': {'id': '123', 'name': 'test'}})
    mock_table.update_item = Mock(return_value={'Attributes': {}})
    mock_table.delete_item = Mock(return_value={})
    mock_table.query = Mock(return_value={'Items': [], 'Count': 0})
    mock_table.scan = Mock(return_value={'Items': [], 'Count': 0})

    # Mock batch writer
    mock_batch_writer = MagicMock()
    mock_batch_writer.__enter__ = Mock(return_value=mock_batch_writer)
    mock_batch_writer.__exit__ = Mock(return_value=None)
    mock_batch_writer.put_item = Mock()
    mock_batch_writer.delete_item = Mock()
    mock_table.batch_writer = Mock(return_value=mock_batch_writer)

    resource.Table = Mock(return_value=mock_table)

    return resource


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j Driver"""
    driver = Mock()

    # Mock verify_connectivity
    driver.verify_connectivity = Mock()
    driver.close = Mock()

    # Mock session
    mock_session = MagicMock()
    mock_result = Mock()
    mock_result.data = Mock(return_value=[])
    mock_result.single = Mock(return_value={})
    mock_result.__iter__ = Mock(return_value=iter([]))

    mock_session.run = Mock(return_value=mock_result)
    mock_session.close = Mock()

    # Mock transaction functions
    def mock_execute_write(func):
        tx = Mock()
        tx.run = Mock(return_value=mock_result)
        return func(tx)

    def mock_execute_read(func):
        tx = Mock()
        tx.run = Mock(return_value=mock_result)
        return func(tx)

    mock_session.execute_write = Mock(side_effect=mock_execute_write)
    mock_session.execute_read = Mock(side_effect=mock_execute_read)

    # Mock context manager
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)

    driver.session = Mock(return_value=mock_session)

    return driver


# ============================================================================
# LLM Test Fixtures
# ============================================================================


@pytest.fixture
def mock_ollama_provider():
    """Mock Ollama provider for testing"""
    provider = Mock()
    provider.initialized = True
    provider.model_name = "llama2"
    provider.model_path = "/data0/models"
    provider.initialize = Mock(return_value=True)
    provider.generate = Mock(return_value="Mock generated response")
    provider.chat = Mock(return_value="Mock chat response")
    provider.cleanup = Mock()
    return provider


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model for testing"""
    import numpy as np
    model = Mock()
    model.initialized = True
    model.model_name = "all-MiniLM-L6-v2"

    # Mock encode to return numpy arrays
    def mock_encode(texts, batch_size=32):
        if isinstance(texts, str):
            texts = [texts]
        return np.random.randn(len(texts), 384).astype(np.float32)

    model.encode = Mock(side_effect=mock_encode)
    model.initialize = Mock(return_value=True)
    model.similarity = Mock(return_value=0.85)
    model.find_most_similar = Mock(return_value=[
        ("SELECT * FROM users", 0.92),
        ("SELECT id, name FROM users", 0.88),
        ("SELECT * FROM customers", 0.75)
    ])
    model.cleanup = Mock()
    return model


@pytest.fixture
def mock_llm_manager(mock_ollama_provider, mock_embedding_model):
    """Mock LLM manager with all dependencies"""
    from src.llm.manager import LocalLLMManager

    manager = LocalLLMManager(provider=mock_ollama_provider)
    manager.embedding_model = mock_embedding_model
    manager.initialized = True
    return manager


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    return {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Mock Anthropic response"}],
        "model": "claude-3-sonnet",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 20}
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Mock OpenAI response"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        "model": "llama2",
        "created_at": "2024-01-01T00:00:00Z",
        "response": "Mock Ollama response",
        "done": True
    }


@pytest.fixture
async def async_mock_generator():
    """Helper for async generator mocking"""
    async def _generator(items):
        for item in items:
            yield item
    return _generator


# ============================================================================
# Integration Test Fixtures
# ============================================================================


@pytest.fixture
async def mock_ai_shell():
    """Create mock AIShell with full stack components"""
    from src.core.ai_shell import AIShellCore
    from src.database.module import DatabaseModule

    ai_shell = AIShellCore()
    await ai_shell.initialize()

    # Add database module
    db_module = DatabaseModule()
    db_module.name = 'DatabaseModule'
    db_module.client = AsyncMock()
    db_module.client.execute = AsyncMock(return_value=[])
    db_module.client.executemany = AsyncMock()
    ai_shell.register_module(db_module)

    return ai_shell


@pytest.fixture
async def full_stack_app(mock_ai_shell):
    """Create full stack application instance"""
    from src.ui.app import AIShellApp

    app = AIShellApp()
    app.ai_shell = mock_ai_shell

    # Add convenience methods for testing
    async def process_user_query(query: str) -> dict:
        """Process user query and return result"""
        return {
            'status': 'success',
            'data': [],
            'sql': query,
            'risk': 'low'
        }

    async def execute_workflow_with_retry(queries: list, max_retries: int = 2) -> dict:
        """Execute workflow with retry logic"""
        steps_completed = 0
        retries = 0

        for i, query in enumerate(queries):
            for attempt in range(max_retries + 1):
                try:
                    await app.ai_shell.modules['DatabaseModule'].client.execute(query)
                    steps_completed += 1
                    break
                except Exception as e:
                    if attempt < max_retries:
                        retries += 1
                    else:
                        raise

        return {
            'status': 'success',
            'steps_completed': steps_completed,
            'retries': retries
        }

    app.process_user_query = process_user_query
    app.execute_workflow_with_retry = execute_workflow_with_retry

    return app


@pytest.fixture
async def tenant_system():
    """Create multi-tenant system"""
    from src.enterprise.tenancy.tenant_manager import TenantManager, TenantTier
    from src.enterprise.tenancy.tenant_database import TenantDatabaseManager

    manager = TenantManager()
    database = TenantDatabaseManager()

    # Add async wrappers for testing
    async def create_tenant_async(slug: str, metadata: dict):
        """Create tenant asynchronously - wrapper to make sync function async"""
        return manager._original_create_tenant(
            name=metadata.get('name', slug),
            slug=slug,
            owner_id='test-owner',
            tier=TenantTier.FREE,
            metadata=metadata
        )

    # Store original create_tenant to avoid recursion
    manager._original_create_tenant = manager.create_tenant
    manager.create_tenant = create_tenant_async

    async def get_tenant_data(tenant_id: str, authorized: bool = False):
        """Get tenant data"""
        if not authorized:
            raise PermissionError("Access denied")
        tenant = manager.get_tenant(tenant_id)
        return {'tenant_id': tenant.id, 'data': tenant.metadata}

    async def set_quota(tenant_id: str, quota):
        """Set tenant quota"""
        manager.update_tenant(tenant_id, metadata={'quota': quota.__dict__})

    async def get_usage(tenant_id: str) -> dict:
        """Get tenant usage"""
        return {'storage': 0, 'queries': 0, 'connections': 0}

    async def check_quota(tenant_id: str, resource: str):
        """Check quota for resource"""
        usage = await get_usage(tenant_id)
        tenant = manager._original_create_tenant.__self__.get_tenant(tenant_id)
        if tenant:
            quota = tenant.metadata.get('quota', {})

            if resource == 'storage':
                if usage.get('storage', 0) > quota.get('max_storage', float('inf')):
                    raise Exception("Quota exceeded: storage limit reached")

    manager.get_tenant_data = get_tenant_data
    manager.set_quota = set_quota
    manager.get_usage = get_usage
    manager.check_quota = check_quota

    # Add async database methods
    async def create_resource(tenant_id: str, resource_type: str, data: dict):
        """Create resource for tenant"""
        pass

    async def get_resource(tenant_id: str, resource_id: str):
        """Get resource for tenant"""
        raise PermissionError("Access denied")

    database.create_resource = create_resource
    database.get_resource = get_resource

    return {'manager': manager, 'database': database}


@pytest.fixture
def mock_query_cache():
    """Create mock query cache"""
    from src.performance.cache import QueryCache

    cache = QueryCache()
    return cache


@pytest.fixture
async def mock_event_bus():
    """Create mock event bus"""
    from src.core.event_bus import AsyncEventBus

    bus = AsyncEventBus()
    await bus.start()
    return bus


# ============================================================================
# Security & Vault Test Fixtures
# ============================================================================


@pytest.fixture
def mock_keyring():
    """Mock keyring for vault testing"""
    from src.security.vault import MockKeyring

    # Clear storage before each test
    MockKeyring._storage = {}
    return MockKeyring()


@pytest.fixture
def temp_vault_path():
    """Create temporary vault path for testing"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / 'test_vault.enc'
        yield vault_path


@pytest.fixture
def vault_factory(temp_vault_path, mock_keyring):
    """Factory for creating test vaults"""
    from src.security.vault import SecureVault

    def _create_vault(
        vault_path: str = None,
        master_password: str = 'test_master_password',
        auto_redact: bool = True,
        use_keyring: bool = False
    ):
        """Create a test vault with insecure path allowed"""
        path = vault_path or str(temp_vault_path)
        vault = SecureVault(
            vault_path=path,
            master_password=master_password,
            auto_redact=auto_redact,
            use_keyring=use_keyring,
            allow_insecure_path=True  # Allow test paths outside home
        )
        # Inject mock keyring
        vault.keyring = mock_keyring
        return vault

    return _create_vault


# ============================================================================
# Redis Mock Fixtures for State Sync
# ============================================================================


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for state synchronization tests"""

    class MockRedis:
        def __init__(self):
            self._hashes = {}  # Hash storage
            self._pubsub_channels = {}  # Pub/sub channels
            self._pubsub_messages = []  # Message queue

        async def hset(self, key, field, value):
            """Mock HSET operation"""
            if key not in self._hashes:
                self._hashes[key] = {}
            self._hashes[key][field] = value
            return 1

        async def hget(self, key, field):
            """Mock HGET operation"""
            if key in self._hashes and field in self._hashes[key]:
                return self._hashes[key][field]
            return None

        async def hgetall(self, key):
            """Mock HGETALL operation"""
            if key in self._hashes:
                return self._hashes[key].copy()
            return {}

        async def hdel(self, key, field):
            """Mock HDEL operation"""
            if key in self._hashes and field in self._hashes[key]:
                del self._hashes[key][field]
                return 1
            return 0

        async def hincrby(self, key, field, amount):
            """Mock HINCRBY operation"""
            if key not in self._hashes:
                self._hashes[key] = {}
            current = int(self._hashes[key].get(field, 0))
            new_value = current + amount
            self._hashes[key][field] = new_value
            return new_value

        async def expire(self, key, ttl):
            """Mock EXPIRE operation"""
            return True

        async def publish(self, channel, message):
            """Mock PUBLISH operation"""
            if channel not in self._pubsub_channels:
                self._pubsub_channels[channel] = []
            self._pubsub_channels[channel].append(message)
            self._pubsub_messages.append({
                'type': 'message',
                'channel': channel,
                'data': message
            })
            return 1

        def pubsub(self):
            """Mock pubsub object"""
            parent = self

            class MockPubSub:
                def __init__(self):
                    self.subscribed_channels = []
                    self.message_index = 0

                async def subscribe(self, *channels):
                    """Mock subscribe"""
                    self.subscribed_channels.extend(channels)
                    return True

                async def unsubscribe(self, *channels):
                    """Mock unsubscribe"""
                    for channel in channels:
                        if channel in self.subscribed_channels:
                            self.subscribed_channels.remove(channel)
                    return True

                async def get_message(self, ignore_subscribe_messages=False, timeout=None):
                    """Mock get_message"""
                    if self.message_index < len(parent._pubsub_messages):
                        msg = parent._pubsub_messages[self.message_index]
                        self.message_index += 1
                        return msg
                    return None

                async def close(self):
                    """Mock close"""
                    return True

            return MockPubSub()

    return MockRedis()


@pytest.fixture
async def mock_state_sync(mock_redis_client):
    """Mock StateSync instance with Redis mock"""
    from src.coordination.state_sync import StateSync

    sync = StateSync(
        redis_client=mock_redis_client,
        namespace='test',
        ttl=None
    )

    # Don't auto-start to avoid pub/sub listener
    # Tests can call start() explicitly if needed

    return sync


# ============================================================================
# UI Test Fixtures (Vector DB, Completer, Context Suggestion Engine)
# ============================================================================


@pytest.fixture
def faiss_cache_dir(tmp_path):
    """Temporary directory for FAISS cache."""
    cache_dir = tmp_path / "faiss_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def ensure_faiss_installed():
    """Ensure FAISS is installed before running tests."""
    try:
        import faiss
        return True
    except ImportError:
        pytest.skip("FAISS is required but not installed. Install with: pip install faiss-cpu==1.12.0")


@pytest.fixture
def metadata_cache(faiss_cache_dir):
    """Create DatabaseMetadataCache fixture."""
    from src.database.metadata_cache import DatabaseMetadataCache

    cache = DatabaseMetadataCache(
        cache_dir=str(faiss_cache_dir),
        dimension=384
    )
    return cache


@pytest.fixture
def mock_vector_db(ensure_faiss_installed):
    """VectorDatabase for UI tests with sample data (requires FAISS)"""
    from src.vector.store import VectorDatabase

    # Use real FAISS implementation
    vector_db = VectorDatabase(dimension=384)

    # Add sample database objects for testing
    sample_objects = [
        ("users_table", "table", {"name": "users"}),
        ("orders_table", "table", {"name": "orders"}),
        ("products_table", "table", {"name": "products"}),
        ("user_profiles_table", "table", {"name": "user_profiles"}),
        ("users_id", "column", {"table": "users", "name": "id"}),
        ("users_name", "column", {"table": "users", "name": "name"}),
        ("users_email", "column", {"table": "users", "name": "email"}),
    ]

    for obj_id, obj_type, metadata in sample_objects:
        vector_db.add_object(
            obj_id,
            np.random.randn(384).astype(np.float32),
            obj_type,
            metadata
        )

    return vector_db


@pytest.fixture
def mock_ui_embedding_model():
    """Mock embedding model specifically for UI tests"""
    model = Mock()
    model.initialized = True
    model.model_name = "all-MiniLM-L6-v2"

    # Mock encode to return numpy arrays
    def mock_encode(texts, batch_size=32):
        if isinstance(texts, str):
            texts = [texts]
        return np.random.randn(len(texts), 384).astype(np.float32)

    model.encode = Mock(side_effect=mock_encode)
    model.initialize = Mock(return_value=True)
    model.similarity = Mock(return_value=0.85)

    return model


@pytest.fixture
def mock_intelligent_completer(mock_vector_db):
    """Mock IntelligentCompleter with completion history"""
    from src.vector.autocomplete import IntelligentCompleter

    completer = IntelligentCompleter(vector_db=mock_vector_db)

    # Add completion history for context-aware suggestions
    completer.add_to_history("SELECT * FROM users")
    completer.add_to_history("SELECT * FROM orders WHERE user_id = 1")
    completer.add_to_history("UPDATE users SET status='active'")

    return completer


@pytest.fixture
def mock_context_suggestion_engine(mock_intelligent_completer, mock_ui_embedding_model):
    """Mock ContextAwareSuggestionEngine with pre-populated data"""
    from src.ui.engines.context_suggestion import ContextAwareSuggestionEngine

    engine = ContextAwareSuggestionEngine(
        completer=mock_intelligent_completer,
        embedding_model=mock_ui_embedding_model,
        cache_ttl=300
    )

    # Pre-populate database objects for testing
    engine.set_database_objects(
        tables=['users', 'orders', 'products', 'user_profiles'],
        columns={
            'users': ['id', 'name', 'email', 'created_at'],
            'orders': ['id', 'user_id', 'total', 'created_at'],
            'products': ['id', 'name', 'price'],
            'user_profiles': ['user_id', 'bio', 'avatar']
        }
    )

    # Add command history for context-aware suggestions
    engine.add_to_history("SELECT * FROM users WHERE id = 1")
    engine.add_to_history("SELECT * FROM orders WHERE user_id = 1")

    return engine


# ============================================================================
# Safety Controller Test Fixtures
# ============================================================================


@pytest.fixture
def mock_sql_risk_analyzer():
    """Mock SQLRiskAnalyzer for safety controller tests"""
    from src.database.risk_analyzer import RiskLevel

    analyzer = Mock()

    def analyze_sql(sql: str) -> dict:
        """Analyze SQL and return risk assessment"""
        sql_upper = sql.upper()

        # Detect DROP operations
        if 'DROP TABLE' in sql_upper or 'DROP DATABASE' in sql_upper:
            return {
                'risk_level': 'CRITICAL',
                'requires_confirmation': True,
                'issues': ['DROP operation detected'],
                'warnings': ['DROP operation will permanently delete data']
            }

        # Detect TRUNCATE operations
        if 'TRUNCATE' in sql_upper:
            return {
                'risk_level': 'HIGH',
                'requires_confirmation': True,
                'issues': ['TRUNCATE operation detected'],
                'warnings': ['TRUNCATE will remove all data from table']
            }

        # Detect DELETE without WHERE
        if 'DELETE FROM' in sql_upper and 'WHERE' not in sql_upper:
            return {
                'risk_level': 'HIGH',
                'requires_confirmation': True,
                'issues': ['DELETE without WHERE clause'],
                'warnings': ['DELETE without WHERE will remove all rows']
            }

        # Detect UPDATE without WHERE
        if 'UPDATE' in sql_upper and 'SET' in sql_upper and 'WHERE' not in sql_upper:
            return {
                'risk_level': 'HIGH',
                'requires_confirmation': True,
                'issues': ['UPDATE without WHERE clause'],
                'warnings': ['UPDATE without WHERE will affect all rows']
            }

        # Detect SQL injection patterns
        if "'; DROP" in sql_upper or '"; DROP' in sql_upper or '-- ' in sql:
            return {
                'risk_level': 'CRITICAL',
                'requires_confirmation': True,
                'issues': ['SQL injection pattern detected'],
                'warnings': ['Potential SQL injection attack']
            }

        # Safe queries
        return {
            'risk_level': 'LOW',
            'requires_confirmation': False,
            'issues': [],
            'warnings': []
        }

    analyzer.analyze = Mock(side_effect=analyze_sql)
    return analyzer


@pytest.fixture
def mock_agent_config_strict():
    """Mock AgentConfig with strict safety level"""
    from src.agents.base import AgentConfig, AgentCapability

    return AgentConfig(
        agent_id='test-agent-strict',
        agent_type='test',
        capabilities=[AgentCapability.DATABASE_WRITE, AgentCapability.DATABASE_DDL],
        llm_config={},
        safety_level='strict'
    )


@pytest.fixture
def mock_agent_config_moderate():
    """Mock AgentConfig with moderate safety level"""
    from src.agents.base import AgentConfig, AgentCapability

    return AgentConfig(
        agent_id='test-agent-moderate',
        agent_type='test',
        capabilities=[AgentCapability.DATABASE_WRITE, AgentCapability.DATABASE_DDL],
        llm_config={},
        safety_level='moderate'
    )


@pytest.fixture
def mock_agent_config_permissive():
    """Mock AgentConfig with permissive safety level"""
    from src.agents.base import AgentConfig, AgentCapability

    return AgentConfig(
        agent_id='test-agent-permissive',
        agent_type='test',
        capabilities=[AgentCapability.DATABASE_WRITE, AgentCapability.DATABASE_DDL],
        llm_config={},
        safety_level='permissive'
    )


# ============================================================================
# Error Handling Test Fixtures
# ============================================================================


@pytest.fixture
def mock_postgresql_extended():
    """Mock extended PostgreSQL client for error handling tests"""
    from src.mcp_clients.postgresql_extended import PostgreSQLClientExtended

    return PostgreSQLClientExtended


@pytest.fixture
def mock_mcp_client_manager():
    """Mock MCP client manager with fallback support"""
    from src.mcp_clients.manager_extended import MCPClientManager

    return MCPClientManager()


@pytest.fixture
def mock_cache_fallback():
    """Mock cache with fallback mechanism"""
    from src.performance.cache_extended import CacheFallback

    return CacheFallback()


@pytest.fixture
def mock_stale_cache():
    """Mock cache that accepts stale entries"""
    from src.performance.cache_extended import StaleCache

    return StaleCache(ttl=1.0, stale_ttl=60.0)


@pytest.fixture
async def mock_ai_shell_with_degraded_mode():
    """Mock AIShell with degraded mode support"""
    from src.core.ai_shell import AIShellCore
    from src.core.degraded_mode import DegradedModeManager

    ai_shell = AIShellCore()
    await ai_shell.initialize()

    # Add degraded mode manager
    degraded_manager = DegradedModeManager()
    ai_shell.execute_in_degraded_mode = degraded_manager.execute_in_degraded_mode

    return ai_shell
