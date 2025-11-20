# FAISS-Based Database Dictionary Caching System - Architecture Design

**Version:** 1.0
**Date:** 2025-11-20
**Status:** Design Phase
**Author:** System Architecture Designer

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Data Model](#data-model)
4. [API Design](#api-design)
5. [Integration Strategy](#integration-strategy)
6. [Performance Considerations](#performance-considerations)
7. [Migration Plan](#migration-plan)
8. [Security Considerations](#security-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Architecture Decision Records](#architecture-decision-records)

---

## Executive Summary

### Purpose

The FAISS-based Database Dictionary Caching System provides intelligent, semantic search capabilities for database metadata across all MCP-connected databases. This system eliminates repetitive metadata queries by maintaining a persistent, searchable cache of database schemas, enabling fast AI-powered database operations.

### Key Benefits

- **Performance**: 10-100x faster metadata queries through semantic caching
- **Intelligence**: Natural language database object discovery
- **Scalability**: Support for multiple concurrent MCP database connections
- **Persistence**: Cross-session cache with automatic invalidation
- **Integration**: Seamless integration with existing AIShell architecture

### Design Principles

1. **FAISS-First**: FAISS is a hard dependency, no mock fallback
2. **MCP-Native**: Designed for MCP multi-database environment
3. **Semantic Search**: Natural language queries over exact matches
4. **Auto-Synchronization**: Automatic cache updates on schema changes
5. **Zero-Configuration**: Works out-of-the-box with intelligent defaults

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AIShell Main                             │
│                    (src/main.py)                                 │
└───────────────────┬─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────────┐    ┌──────────────────────┐
│  DatabaseModule  │    │ EnhancedConnection   │
│                  │    │     Manager          │
│ (db/module.py)   │    │ (mcp_clients/        │
└────────┬─────────┘    │  enhanced_manager)   │
         │              └──────────┬───────────┘
         │                         │
         │              ┌──────────┴────────────┐
         │              │                       │
         │              ▼                       ▼
         │      ┌──────────────┐      ┌──────────────┐
         │      │ PostgreSQL   │      │  MySQL MCP   │
         │      │   MCP        │      │  Connection  │
         │      └──────────────┘      └──────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│            DatabaseMetadataCache (NEW)                           │
│               (src/database/metadata_cache.py)                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Metadata   │  │    FAISS     │  │  Embedding   │          │
│  │  Extractor   │→ │ VectorStore  │← │  Generator   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         │                  ▼                  │                  │
│         │          ┌──────────────┐           │                  │
│         └─────────→│ Persistence  │←──────────┘                  │
│                    │   Manager    │                              │
│                    └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Persistent Storage Layer                       │
│                                                                   │
│  ~/.aishell/cache/                                               │
│    ├── db_metadata.faiss      (FAISS index)                     │
│    ├── db_metadata.json       (Metadata + mappings)             │
│    └── db_metadata.lock       (Version control)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture (C4 Model - Container Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                  DatabaseMetadataCache                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  PUBLIC API                                                       │
│  ├─ index_database(connection_id)                               │
│  ├─ search_tables(query, limit, threshold)                      │
│  ├─ search_columns(query, table_filter, limit)                  │
│  ├─ get_table_schema(table_name)                                │
│  ├─ get_foreign_keys(table_name)                                │
│  ├─ invalidate_cache(connection_id)                             │
│  └─ get_cache_stats()                                            │
│                                                                   │
│  INTERNAL COMPONENTS                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ MetadataExtractor                                          │  │
│  │ - extract_tables(connection)                               │  │
│  │ - extract_columns(connection, table)                       │  │
│  │ - extract_indexes(connection, table)                       │  │
│  │ - extract_constraints(connection, table)                   │  │
│  │ - extract_foreign_keys(connection, table)                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ EmbeddingGenerator                                         │  │
│  │ - generate_table_embedding(table_metadata)                 │  │
│  │ - generate_column_embedding(column_metadata)               │  │
│  │ - generate_composite_embedding(metadata_dict)              │  │
│  │ - batch_generate(metadata_list)                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ FAISSVectorStore (Enhanced from vector/store.py)          │  │
│  │ - add_object(id, vector, type, metadata)                   │  │
│  │ - search_similar(vector, k, type_filter, threshold)        │  │
│  │ - delete_by_connection(connection_id)                      │  │
│  │ - save_index(path)                                         │  │
│  │ - load_index(path)                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ CacheInvalidationManager                                   │  │
│  │ - track_schema_version(connection_id, version_hash)        │  │
│  │ - detect_schema_changes(connection_id)                     │  │
│  │ - invalidate_connection(connection_id)                     │  │
│  │ - schedule_refresh(connection_id, interval)                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ PersistenceManager                                         │  │
│  │ - save_cache()                                             │  │
│  │ - load_cache()                                             │  │
│  │ - verify_integrity()                                       │  │
│  │ - migrate_version(old_version, new_version)               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagrams

#### Indexing Flow

```
User/System
    │
    │ (1) index_database(connection_id)
    ▼
DatabaseMetadataCache
    │
    │ (2) Get MCP connection
    ▼
EnhancedConnectionManager
    │
    │ (3) Return connection client
    ▼
DatabaseMetadataCache::MetadataExtractor
    │
    ├─(4a) Extract tables ────────────┐
    ├─(4b) Extract columns ───────────┤
    ├─(4c) Extract indexes ───────────┤
    ├─(4d) Extract constraints ───────┤
    └─(4e) Extract foreign keys ──────┤
                                       │
    ┌──────────────────────────────────┘
    │ (5) Raw metadata objects
    ▼
DatabaseMetadataCache::EmbeddingGenerator
    │
    │ (6) Generate embeddings for each object
    │     - Table: "Table users in public schema. Stores user accounts..."
    │     - Column: "Column users.email. Type varchar(255). Unique index..."
    ▼
FAISSVectorStore
    │
    │ (7) Add vectors to FAISS index
    │     - object_id: "conn1:table:users"
    │     - vector: [0.234, -0.567, ...]
    │     - metadata: {connection_id, schema, name, type, ...}
    ▼
PersistenceManager
    │
    │ (8) Save to disk
    │     - db_metadata.faiss (FAISS index)
    │     - db_metadata.json (Metadata mappings)
    ▼
Complete
```

#### Search Flow

```
User Query: "find all email columns"
    │
    │ (1) search_columns("find all email columns")
    ▼
DatabaseMetadataCache
    │
    │ (2) Generate query embedding
    ▼
EmbeddingGenerator
    │
    │ (3) Embedding: [0.123, -0.456, ...]
    ▼
FAISSVectorStore
    │
    │ (4) FAISS semantic search
    │     - k=20 candidates
    │     - threshold=0.6
    ▼
    │ (5) Results with distances
    │     - conn1:column:users.email (distance: 0.12)
    │     - conn1:column:customers.email (distance: 0.15)
    │     - conn2:column:orders.customer_email (distance: 0.21)
    ▼
DatabaseMetadataCache
    │
    │ (6) Apply filters, sort by relevance
    │ (7) Enrich with full metadata
    ▼
Return to User
    │
    │ [
    │   {
    │     "table": "users",
    │     "column": "email",
    │     "type": "varchar(255)",
    │     "constraints": ["UNIQUE", "NOT NULL"],
    │     "relevance": 0.88
    │   },
    │   ...
    │ ]
```

---

## Data Model

### Metadata Schema

#### Table Metadata

```python
@dataclass
class TableMetadata:
    """Comprehensive table metadata"""
    connection_id: str           # MCP connection identifier
    schema_name: str             # Database schema (e.g., 'public', 'dbo')
    table_name: str              # Table name
    table_type: str              # 'TABLE', 'VIEW', 'MATERIALIZED_VIEW'
    row_count: Optional[int]     # Approximate row count
    size_bytes: Optional[int]    # Table size in bytes

    # Descriptive information
    description: Optional[str]   # Table comment/description

    # Temporal metadata
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    last_analyzed: Optional[datetime]

    # Indexing metadata
    indexed_at: datetime         # When cached
    version_hash: str            # Schema version hash for invalidation

    # Semantic representation
    semantic_text: str           # Text used for embedding generation
    embedding_vector: np.ndarray # 384-dim FAISS vector

    # Relationships
    columns: List['ColumnMetadata']
    indexes: List['IndexMetadata']
    constraints: List['ConstraintMetadata']
    foreign_keys: List['ForeignKeyMetadata']
```

#### Column Metadata

```python
@dataclass
class ColumnMetadata:
    """Comprehensive column metadata"""
    connection_id: str
    schema_name: str
    table_name: str
    column_name: str

    # Type information
    data_type: str               # e.g., 'integer', 'varchar(255)', 'timestamp'
    is_nullable: bool
    default_value: Optional[str]

    # Constraints
    is_primary_key: bool
    is_foreign_key: bool
    is_unique: bool

    # Statistics
    distinct_count: Optional[int]
    null_count: Optional[int]

    # Descriptive
    description: Optional[str]

    # Indexing metadata
    indexed_at: datetime
    version_hash: str

    # Semantic
    semantic_text: str
    embedding_vector: np.ndarray

    # Ordinal position
    ordinal_position: int
```

#### Index Metadata

```python
@dataclass
class IndexMetadata:
    """Database index metadata"""
    connection_id: str
    schema_name: str
    table_name: str
    index_name: str

    # Index properties
    index_type: str              # 'BTREE', 'HASH', 'GIN', 'GIST', etc.
    is_unique: bool
    is_primary: bool

    # Columns in index
    column_names: List[str]

    # Statistics
    size_bytes: Optional[int]

    # Semantic
    semantic_text: str
    embedding_vector: np.ndarray
```

#### Constraint Metadata

```python
@dataclass
class ConstraintMetadata:
    """Database constraint metadata"""
    connection_id: str
    schema_name: str
    table_name: str
    constraint_name: str
    constraint_type: str         # 'PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK'

    # Constraint details
    column_names: List[str]
    check_clause: Optional[str]  # For CHECK constraints

    # Semantic
    semantic_text: str
    embedding_vector: np.ndarray
```

#### Foreign Key Metadata

```python
@dataclass
class ForeignKeyMetadata:
    """Foreign key relationship metadata"""
    connection_id: str
    schema_name: str
    table_name: str
    constraint_name: str

    # Source columns
    column_names: List[str]

    # Target reference
    referenced_schema: str
    referenced_table: str
    referenced_columns: List[str]

    # Referential actions
    on_delete: str               # 'CASCADE', 'SET NULL', 'RESTRICT', etc.
    on_update: str

    # Semantic
    semantic_text: str
    embedding_vector: np.ndarray
```

### Vector Index Structure

#### FAISS Index Configuration

```python
class FAISSIndexConfig:
    """FAISS index configuration for database metadata"""

    # Index type: IndexFlatL2 for exact search with L2 distance
    # For large databases (>1M objects), consider IndexIVFFlat
    index_type: str = "IndexFlatL2"

    # Embedding dimension (sentence-transformers/all-MiniLM-L6-v2)
    dimension: int = 384

    # Index parameters
    metric: str = "L2"           # L2 distance for normalized vectors
    normalize_vectors: bool = True  # Normalize to unit length

    # For IVF indices (if needed for scale)
    nlist: int = 100             # Number of clusters
    nprobe: int = 10             # Number of clusters to search
```

#### Object Type Registry

```python
class MetadataObjectType(Enum):
    """Types of database objects in cache"""
    TABLE = "table"
    COLUMN = "column"
    INDEX = "index"
    CONSTRAINT = "constraint"
    FOREIGN_KEY = "foreign_key"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"
    FUNCTION = "function"          # Future: stored procedures
    TRIGGER = "trigger"            # Future: triggers
```

### Embedding Generation Strategy

#### Text Representation for Embeddings

```python
def generate_semantic_text(metadata_obj) -> str:
    """
    Generate semantic text representation for embedding.

    The text combines multiple signals for better semantic search:
    - Object name and type
    - Schema/namespace
    - Description/comments
    - Data types and constraints
    - Relationships
    """

    # Example for Table:
    # "Table users in public schema. Stores user account information.
    #  Contains columns: id (integer primary key), email (varchar unique),
    #  name (varchar), created_at (timestamp).
    #  Has foreign keys to: roles, organizations."

    # Example for Column:
    # "Column email in users table. Type varchar(255). Unique constraint.
    #  Not null. Used for user authentication. Indexed."

    # Example for Foreign Key:
    # "Foreign key from orders.customer_id to customers.id.
    #  Cascade on delete. Many-to-one relationship."
```

### Cache Persistence Format

#### On-Disk Structure

```
~/.aishell/cache/
├── db_metadata/
│   ├── faiss_index.bin          # FAISS index binary
│   ├── metadata.json            # All metadata objects
│   ├── version.json             # Schema version tracking
│   └── connections.json         # Connection-to-objects mapping
```

#### Metadata JSON Format

```json
{
  "version": "1.0",
  "created_at": "2025-11-20T10:00:00Z",
  "updated_at": "2025-11-20T15:30:00Z",

  "connections": {
    "conn1": {
      "connection_id": "conn1",
      "connection_type": "postgresql",
      "host": "localhost",
      "database": "myapp",
      "indexed_at": "2025-11-20T15:30:00Z",
      "version_hash": "abc123def456",
      "object_count": 150
    }
  },

  "objects": {
    "conn1:table:users": {
      "id": "conn1:table:users",
      "type": "table",
      "connection_id": "conn1",
      "schema_name": "public",
      "table_name": "users",
      "row_count": 10000,
      "indexed_at": "2025-11-20T15:30:00Z",
      "semantic_text": "Table users in public schema...",
      "faiss_index": 42,
      "metadata": {
        "description": "User accounts",
        "columns": ["id", "email", "name", "created_at"],
        "indexes": ["users_pkey", "users_email_idx"],
        "foreign_keys": []
      }
    }
  },

  "index_mapping": {
    "0": "conn1:table:users",
    "1": "conn1:column:users.id",
    "2": "conn1:column:users.email"
  }
}
```

---

## API Design

### Public Interface

```python
class DatabaseMetadataCache:
    """
    FAISS-based semantic cache for database metadata.

    Provides fast, intelligent search across all MCP-connected databases.
    """

    def __init__(
        self,
        mcp_manager: EnhancedConnectionManager,
        cache_dir: str = "~/.aishell/cache/db_metadata",
        embedding_model: str = "all-MiniLM-L6-v2",
        auto_refresh_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize database metadata cache.

        Args:
            mcp_manager: MCP connection manager instance
            cache_dir: Directory for persistent cache storage
            embedding_model: Sentence transformer model name
            auto_refresh_interval: Seconds between automatic refreshes
        """

    # --- Indexing Operations ---

    async def index_database(
        self,
        connection_id: str,
        incremental: bool = True,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        Index or re-index a database connection.

        Args:
            connection_id: MCP connection identifier
            incremental: Only index new/changed objects
            background: Run indexing in background task

        Returns:
            Indexing statistics and status

        Example:
            >>> stats = await cache.index_database("postgres_prod")
            >>> print(stats)
            {
                'connection_id': 'postgres_prod',
                'objects_indexed': 250,
                'objects_updated': 12,
                'objects_deleted': 3,
                'duration_seconds': 4.2,
                'status': 'completed'
            }
        """

    async def index_all_databases(
        self,
        parallel: bool = True,
        max_concurrent: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """
        Index all connected databases.

        Args:
            parallel: Index databases in parallel
            max_concurrent: Max parallel indexing tasks

        Returns:
            Per-connection indexing statistics
        """

    # --- Search Operations ---

    async def search_tables(
        self,
        query: str,
        connection_id: Optional[str] = None,
        schema_filter: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.6
    ) -> List[TableSearchResult]:
        """
        Semantic search for database tables.

        Args:
            query: Natural language or keyword query
            connection_id: Filter by specific connection
            schema_filter: Filter by schema name
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of table search results with relevance scores

        Example:
            >>> results = await cache.search_tables(
            ...     "tables storing user information",
            ...     limit=5
            ... )
            >>> for result in results:
            ...     print(f"{result.table_name}: {result.relevance:.2f}")
            users: 0.89
            user_profiles: 0.82
            customer_accounts: 0.75
        """

    async def search_columns(
        self,
        query: str,
        table_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        connection_id: Optional[str] = None,
        limit: int = 20,
        threshold: float = 0.5
    ) -> List[ColumnSearchResult]:
        """
        Semantic search for database columns.

        Args:
            query: Natural language or keyword query
            table_filter: Filter by table name (supports wildcards)
            type_filter: Filter by data type (e.g., 'varchar', 'integer')
            connection_id: Filter by specific connection
            limit: Maximum results to return
            threshold: Minimum similarity score

        Returns:
            List of column search results with relevance scores

        Example:
            >>> results = await cache.search_columns(
            ...     "email address columns",
            ...     limit=10
            ... )
            >>> for result in results:
            ...     print(f"{result.full_name}: {result.data_type}")
            users.email: varchar(255)
            customers.contact_email: varchar(320)
            orders.customer_email: varchar(255)
        """

    async def search_relationships(
        self,
        query: str,
        source_table: Optional[str] = None,
        target_table: Optional[str] = None,
        connection_id: Optional[str] = None,
        limit: int = 10
    ) -> List[ForeignKeySearchResult]:
        """
        Search for foreign key relationships.

        Args:
            query: Natural language description of relationship
            source_table: Filter by source table
            target_table: Filter by target table
            connection_id: Filter by connection
            limit: Maximum results

        Returns:
            List of foreign key relationships

        Example:
            >>> results = await cache.search_relationships(
            ...     "orders to customers relationship"
            ... )
            >>> for fk in results:
            ...     print(f"{fk.source_table}.{fk.source_column} -> "
            ...           f"{fk.target_table}.{fk.target_column}")
        """

    # --- Metadata Retrieval ---

    async def get_table_schema(
        self,
        table_name: str,
        connection_id: str,
        schema_name: str = "public"
    ) -> Optional[TableMetadata]:
        """
        Get complete schema for a specific table.

        Args:
            table_name: Table name
            connection_id: Connection identifier
            schema_name: Schema name (default: 'public')

        Returns:
            Complete table metadata with all columns, indexes, etc.

        Example:
            >>> schema = await cache.get_table_schema("users", "postgres_prod")
            >>> print(f"Columns: {len(schema.columns)}")
            >>> print(f"Indexes: {len(schema.indexes)}")
        """

    async def get_foreign_keys(
        self,
        table_name: str,
        connection_id: str,
        schema_name: str = "public",
        direction: str = "both"  # 'incoming', 'outgoing', 'both'
    ) -> List[ForeignKeyMetadata]:
        """
        Get all foreign keys for a table.

        Args:
            table_name: Table name
            connection_id: Connection identifier
            schema_name: Schema name
            direction: 'incoming' (references TO this table),
                      'outgoing' (references FROM this table),
                      'both'

        Returns:
            List of foreign key relationships
        """

    # --- Cache Management ---

    async def invalidate_cache(
        self,
        connection_id: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> None:
        """
        Invalidate cache for connection or specific table.

        Args:
            connection_id: Connection to invalidate (None = all)
            table_name: Specific table to invalidate (None = all in connection)
        """

    async def refresh_cache(
        self,
        connection_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Refresh cache by detecting and applying changes.

        Args:
            connection_id: Connection to refresh (None = all)
            force: Force full re-index even if no changes detected

        Returns:
            Refresh statistics
        """

    def get_cache_stats(self) -> CacheStatistics:
        """
        Get cache statistics.

        Returns:
            Statistics about cached objects, memory usage, etc.

        Example:
            >>> stats = cache.get_cache_stats()
            >>> print(stats)
            CacheStatistics(
                total_objects=1250,
                total_connections=3,
                tables=150,
                columns=800,
                indexes=200,
                foreign_keys=100,
                memory_mb=45.2,
                last_refresh='2025-11-20T15:30:00Z'
            )
        """

    # --- Context Manager ---

    async def __aenter__(self):
        """Async context manager entry"""
        await self.load_cache()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.save_cache()
```

### Search Result Models

```python
@dataclass
class TableSearchResult:
    """Table search result with relevance"""
    connection_id: str
    schema_name: str
    table_name: str
    table_type: str
    description: Optional[str]

    # Search metadata
    relevance: float             # 0-1 similarity score
    distance: float              # FAISS distance

    # Quick stats
    column_count: int
    row_count: Optional[int]
    size_mb: Optional[float]

    # Full metadata (lazy loaded)
    _full_metadata: Optional[TableMetadata] = None

    async def get_full_metadata(self) -> TableMetadata:
        """Load complete table metadata"""

@dataclass
class ColumnSearchResult:
    """Column search result with relevance"""
    connection_id: str
    schema_name: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool

    # Search metadata
    relevance: float
    distance: float

    # Constraints
    is_primary_key: bool
    is_foreign_key: bool
    is_unique: bool

    @property
    def full_name(self) -> str:
        """Fully qualified column name"""
        return f"{self.schema_name}.{self.table_name}.{self.column_name}"
```

### Cache Statistics Model

```python
@dataclass
class CacheStatistics:
    """Cache statistics and health metrics"""

    # Object counts
    total_objects: int
    total_connections: int
    tables: int
    columns: int
    indexes: int
    constraints: int
    foreign_keys: int

    # By connection
    objects_by_connection: Dict[str, int]

    # Memory usage
    memory_mb: float
    faiss_index_size_mb: float
    metadata_size_mb: float

    # Temporal
    created_at: datetime
    last_refresh: datetime
    last_query: Optional[datetime]

    # Performance
    total_searches: int
    avg_search_time_ms: float
    cache_hit_rate: float        # For get_table_schema calls

    # Health
    is_stale: bool               # Any connection not refreshed in 24h
    stale_connections: List[str]
```

---

## Integration Strategy

### Phase 1: Core Integration

#### 1.1 Enhance VectorDatabase (src/vector/store.py)

**Changes Required:**

1. **Remove Mock Fallback**
   ```python
   # BEFORE:
   try:
       import faiss
       FAISS_AVAILABLE = True
   except ImportError:
       FAISS_AVAILABLE = False
       # Use mock...

   # AFTER:
   import faiss  # Hard requirement
   ```

2. **Add Batch Operations**
   ```python
   def add_batch(
       self,
       objects: List[Tuple[str, np.ndarray, str, Dict[str, Any]]]
   ) -> None:
       """Efficiently add multiple objects"""
   ```

3. **Add Connection Filtering**
   ```python
   def delete_by_filter(
       self,
       filter_func: Callable[[VectorEntry], bool]
   ) -> int:
       """Delete entries matching filter"""
   ```

4. **Add Persistence**
   ```python
   def save_to_disk(self, index_path: str, metadata_path: str) -> None:
       """Save FAISS index and metadata to disk"""

   def load_from_disk(self, index_path: str, metadata_path: str) -> None:
       """Load FAISS index and metadata from disk"""
   ```

#### 1.2 Create DatabaseMetadataCache (src/database/metadata_cache.py)

New file implementing the complete API shown above.

#### 1.3 Update DatabaseModule (src/database/module.py)

**Integration Points:**

```python
class DatabaseModule:
    def __init__(
        self,
        db_path: Optional[str] = None,
        history_file: Optional[str] = None,
        auto_confirm: bool = False,
        mcp_manager: Optional[EnhancedConnectionManager] = None,  # NEW
        enable_metadata_cache: bool = True,  # NEW
    ):
        # ... existing code ...

        # NEW: Initialize metadata cache
        if enable_metadata_cache and mcp_manager:
            self.metadata_cache = DatabaseMetadataCache(
                mcp_manager=mcp_manager,
                cache_dir="~/.aishell/cache/db_metadata"
            )
        else:
            self.metadata_cache = None

    async def initialize_cache(self) -> None:
        """Initialize metadata cache for all connections"""
        if self.metadata_cache:
            await self.metadata_cache.index_all_databases()

    async def search_tables(self, query: str, **kwargs):
        """Delegate to metadata cache"""
        if self.metadata_cache:
            return await self.metadata_cache.search_tables(query, **kwargs)
        else:
            raise RuntimeError("Metadata cache not enabled")
```

#### 1.4 Update AIShell Main (src/main.py)

**Initialization Flow:**

```python
class AIShell:
    async def initialize(self) -> None:
        # ... existing initialization ...

        # Initialize enhanced MCP client manager
        self.mcp_manager = EnhancedConnectionManager(
            max_connections=self.config.get('mcp.max_connections', 20)
        )

        # Initialize database module WITH metadata cache
        db_path = self.db_path_override or self.config.get('database.path', None)
        self.db_module = DatabaseModule(
            db_path=db_path,
            auto_confirm=self.config.get('database.auto_confirm', False),
            mcp_manager=self.mcp_manager,  # NEW
            enable_metadata_cache=True      # NEW
        )

        # Initialize metadata cache
        logger.info("Initializing database metadata cache...")
        await self.db_module.initialize_cache()
        logger.info("Metadata cache initialized")
```

### Phase 2: Interactive Mode Commands

#### 2.1 Add Metadata Cache Commands

```python
# In interactive_mode() function:

if user_input == 'db cache stats':
    """Show metadata cache statistics"""
    if self.db_module and self.db_module.metadata_cache:
        stats = self.db_module.metadata_cache.get_cache_stats()
        print(f"\nMetadata Cache Statistics:")
        print(f"  Total Objects: {stats.total_objects}")
        print(f"  Tables: {stats.tables}")
        print(f"  Columns: {stats.columns}")
        print(f"  Memory: {stats.memory_mb:.1f} MB")
        print(f"  Last Refresh: {stats.last_refresh}")

if user_input.startswith('db search tables '):
    """Search for tables by semantic query"""
    query = user_input[17:].strip()
    results = await self.db_module.search_tables(query, limit=10)
    print(f"\nTable Search Results for: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.schema_name}.{result.table_name}")
        print(f"     Relevance: {result.relevance:.0%}")
        if result.description:
            print(f"     {result.description}")

if user_input.startswith('db search columns '):
    """Search for columns by semantic query"""
    query = user_input[18:].strip()
    results = await self.db_module.metadata_cache.search_columns(query, limit=15)
    print(f"\nColumn Search Results for: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.full_name}")
        print(f"     Type: {result.data_type}, Relevance: {result.relevance:.0%}")

if user_input.startswith('db describe '):
    """Describe table schema using cache"""
    table_name = user_input[12:].strip()
    # Parse connection_id if provided: "db describe conn1:users"
    if ':' in table_name:
        connection_id, table_name = table_name.split(':', 1)
    else:
        # Use first available connection
        connection_id = list(self.mcp_manager._connections.keys())[0]

    schema = await self.db_module.metadata_cache.get_table_schema(
        table_name=table_name,
        connection_id=connection_id
    )

    if schema:
        print(f"\nTable: {schema.schema_name}.{schema.table_name}")
        print(f"Columns ({len(schema.columns)}):")
        for col in schema.columns:
            constraints = []
            if col.is_primary_key:
                constraints.append("PK")
            if col.is_foreign_key:
                constraints.append("FK")
            if col.is_unique:
                constraints.append("UNIQUE")
            if not col.is_nullable:
                constraints.append("NOT NULL")

            constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
            print(f"  - {col.column_name}: {col.data_type}{constraint_str}")

if user_input == 'db refresh cache':
    """Manually refresh metadata cache"""
    print("Refreshing metadata cache...")
    stats = await self.db_module.metadata_cache.refresh_cache(force=True)
    print(f"Refresh complete: {stats}")
```

#### 2.2 Update Help Command

```python
print("Database Metadata Commands:")
print("  db cache stats          - Show cache statistics")
print("  db search tables <q>    - Semantic search for tables")
print("  db search columns <q>   - Semantic search for columns")
print("  db describe <table>     - Show table schema from cache")
print("  db refresh cache        - Manually refresh cache")
print("  db relationships <t>    - Show foreign key relationships")
```

### Phase 3: CLI Mode Support

#### 3.1 Add CLI Commands

```python
# In argparse setup:

db_parser = subparsers.add_parser('db', help='Database metadata commands')
db_subparsers = db_parser.add_subparsers(dest='db_command')

# Cache initialization
db_init = db_subparsers.add_parser('init-cache', help='Initialize metadata cache')
db_init.add_argument('--connection-id', help='Specific connection to index')
db_init.add_argument('--background', action='store_true', help='Run in background')

# Search commands
db_search_tables = db_subparsers.add_parser('search-tables', help='Search tables')
db_search_tables.add_argument('query', type=str, help='Search query')
db_search_tables.add_argument('--limit', type=int, default=10)
db_search_tables.add_argument('--json', action='store_true', help='JSON output')

db_search_columns = db_subparsers.add_parser('search-columns', help='Search columns')
db_search_columns.add_argument('query', type=str, help='Search query')
db_search_columns.add_argument('--table', help='Filter by table')
db_search_columns.add_argument('--limit', type=int, default=20)
```

---

## Performance Considerations

### Expected Cache Size

#### Small Database (10-50 tables)

- **Objects**: ~500-2,500
  - Tables: 50
  - Columns: 400 (avg 8 columns/table)
  - Indexes: 50

- **FAISS Index Size**: ~1-5 MB
  - 2,500 vectors × 384 dimensions × 4 bytes = ~3.7 MB

- **Metadata JSON**: ~500 KB - 2 MB

- **Total Disk**: ~2-7 MB

#### Medium Database (100-500 tables)

- **Objects**: ~10,000-50,000
  - Tables: 500
  - Columns: 4,000
  - Indexes: 500
  - Foreign Keys: 1,000

- **FAISS Index Size**: ~20-80 MB

- **Metadata JSON**: ~5-20 MB

- **Total Disk**: ~25-100 MB

#### Large Database (1,000+ tables)

- **Objects**: ~100,000+
  - Tables: 1,000
  - Columns: 10,000
  - Indexes: 2,000
  - Foreign Keys: 3,000

- **FAISS Index Size**: ~150-400 MB

- **Metadata JSON**: ~30-100 MB

- **Total Disk**: ~180-500 MB

### Query Performance

#### Semantic Search Latency

- **Small cache** (< 10K objects):
  - Cold query: 10-50 ms
  - Warm query: 5-20 ms

- **Medium cache** (10K-100K objects):
  - Cold query: 50-150 ms
  - Warm query: 20-80 ms

- **Large cache** (> 100K objects):
  - Cold query: 100-300 ms
  - Warm query: 50-150 ms
  - Consider IVF index: 20-100 ms

#### Indexing Performance

- **Per-table indexing**: 100-500 ms
  - Metadata extraction: 50-200 ms
  - Embedding generation: 30-200 ms (batch processing)
  - FAISS insertion: 10-50 ms

- **Full database indexing** (100 tables):
  - Sequential: 10-50 seconds
  - Parallel (3 workers): 5-20 seconds

### Memory Usage

- **In-Memory Cache**:
  - FAISS index: Same as disk size
  - Metadata objects: 2-3× metadata JSON size
  - Embedding model: ~100 MB (sentence-transformers)

- **Total Runtime Memory**:
  - Small cache: ~150 MB
  - Medium cache: ~300 MB
  - Large cache: ~800 MB

### Optimization Strategies

#### 1. Lazy Loading

```python
class TableSearchResult:
    _full_metadata: Optional[TableMetadata] = None

    async def get_full_metadata(self) -> TableMetadata:
        """Load full metadata only when needed"""
        if not self._full_metadata:
            self._full_metadata = await cache.get_table_schema(...)
        return self._full_metadata
```

#### 2. Batch Embedding Generation

```python
# SLOW: One-by-one
for table in tables:
    embedding = model.encode(table.semantic_text)
    cache.add(embedding)

# FAST: Batch processing
texts = [table.semantic_text for table in tables]
embeddings = model.encode(texts, batch_size=32)  # 3-5× faster
cache.add_batch(embeddings)
```

#### 3. Incremental Indexing

```python
async def index_database(self, connection_id: str, incremental: bool = True):
    if incremental:
        # Only index objects that changed
        current_hash = await compute_schema_hash(connection_id)
        cached_hash = self.get_cached_hash(connection_id)

        if current_hash == cached_hash:
            logger.info(f"No changes detected for {connection_id}")
            return

        # Detect specific changes
        changes = await detect_schema_changes(connection_id)

        # Update only changed objects
        for obj in changes.added:
            await self.index_object(obj)

        for obj in changes.modified:
            await self.update_object(obj)

        for obj_id in changes.deleted:
            await self.delete_object(obj_id)
```

#### 4. Connection Pooling for Metadata Extraction

```python
async def index_all_databases(self, parallel: bool = True, max_concurrent: int = 3):
    if parallel:
        # Use semaphore to limit concurrent connections
        semaphore = asyncio.Semaphore(max_concurrent)

        async def index_with_limit(conn_id):
            async with semaphore:
                return await self.index_database(conn_id)

        tasks = [index_with_limit(conn_id) for conn_id in connection_ids]
        results = await asyncio.gather(*tasks)
    else:
        # Sequential indexing
        results = []
        for conn_id in connection_ids:
            result = await self.index_database(conn_id)
            results.append(result)
```

#### 5. FAISS Index Selection by Scale

```python
def create_faiss_index(self, expected_size: int) -> faiss.Index:
    """Select optimal FAISS index based on expected size"""

    if expected_size < 10_000:
        # Exact search for small datasets
        return faiss.IndexFlatL2(self.dimension)

    elif expected_size < 100_000:
        # IVF with moderate clusters
        quantizer = faiss.IndexFlatL2(self.dimension)
        index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        return index

    else:
        # IVF with more clusters for large datasets
        quantizer = faiss.IndexFlatL2(self.dimension)
        index = faiss.IndexIVFFlat(quantizer, self.dimension, 1000)
        return index
```

---

## Migration Plan

### Step 1: Prerequisites (Week 1)

#### 1.1 Update Dependencies

**pyproject.toml:**

```toml
[tool.poetry.dependencies]
python = "^3.9"
faiss-cpu = "^1.8.0"  # Change from optional to required
sentence-transformers = "^2.2.0"  # For embeddings
numpy = "^1.24.0"
```

**Remove fallback logic:**

```bash
# Find all references to FAISS_AVAILABLE
grep -r "FAISS_AVAILABLE" src/

# Remove mock implementations
rm -f src/vector/mock_faiss.py  # If exists
```

#### 1.2 Create Test Infrastructure

```python
# tests/fixtures/test_databases.py
import pytest
from src.mcp_clients.enhanced_manager import EnhancedConnectionManager
from src.mcp_clients.base import ConnectionConfig

@pytest.fixture
async def test_mcp_manager():
    """Create MCP manager with test database"""
    manager = EnhancedConnectionManager(max_connections=5)

    # Create test SQLite connection
    config = ConnectionConfig(
        host="localhost",
        port=0,
        database=":memory:",
        username="test",
        password="test"
    )

    await manager.create_connection("test_db", "sqlite", config)

    yield manager

    await manager.close_all()

@pytest.fixture
async def populated_test_db(test_mcp_manager):
    """Create test database with sample schema"""
    conn = test_mcp_manager.get_connection("test_db")

    # Create test schema
    await conn.execute_ddl("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await conn.execute_ddl("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount DECIMAL(10,2),
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    yield conn
```

### Step 2: Core Implementation (Week 2-3)

#### 2.1 Enhance VectorDatabase

- Remove mock fallback
- Add batch operations
- Add persistence methods
- Add connection-based filtering

**Testing:**

```bash
pytest tests/vector/test_store.py -v
# All tests must pass without mock
```

#### 2.2 Implement DatabaseMetadataCache

- Create metadata extraction logic
- Implement embedding generation
- Build FAISS integration
- Add persistence layer

**Testing:**

```bash
pytest tests/database/test_metadata_cache.py -v
# Test all API methods
```

#### 2.3 Integration with DatabaseModule

- Add metadata cache as optional component
- Create async initialization
- Add search methods

**Testing:**

```bash
pytest tests/database/test_module_integration.py -v
```

### Step 3: Main Integration (Week 4)

#### 3.1 Update AIShell Initialization

- Integrate metadata cache in init flow
- Add error handling
- Add configuration options

#### 3.2 Add Interactive Commands

- Implement cache commands
- Update help system
- Add command completions

#### 3.3 Add CLI Commands

- Create db subcommand
- Add argparse definitions
- Implement handlers

**Testing:**

```bash
# Test interactive mode
python -m src.main --mock

# Test CLI commands
python -m src.main db init-cache
python -m src.main db search-tables "user tables"
```

### Step 4: Documentation & Polish (Week 5)

#### 4.1 User Documentation

Create **docs/features/database-metadata-cache.md**:

- Feature overview
- Usage examples
- Configuration options
- Performance tuning
- Troubleshooting

#### 4.2 API Documentation

Update API docs with:

- DatabaseMetadataCache class
- Search result models
- Configuration options

#### 4.3 Migration Guide

For existing users:

```markdown
# Migrating to FAISS-Required Version

## Breaking Changes

1. FAISS is now required (was optional)
2. Mock mode removed from vector store

## Migration Steps

1. Install FAISS:
   ```bash
   pip install faiss-cpu
   # or for GPU:
   pip install faiss-gpu
   ```

2. Initialize cache on first run:
   ```bash
   ai-shell db init-cache
   ```

3. Verify cache:
   ```bash
   ai-shell db cache stats
   ```
```

### Step 5: Performance Validation (Week 6)

#### 5.1 Benchmark Suite

```python
# tests/benchmarks/test_metadata_cache_performance.py

async def test_indexing_performance_small_db():
    """Benchmark indexing for small database (50 tables)"""
    # Should complete in < 10 seconds

async def test_indexing_performance_large_db():
    """Benchmark indexing for large database (1000 tables)"""
    # Should complete in < 60 seconds with parallel=True

async def test_search_latency():
    """Benchmark search query latency"""
    # Should return results in < 100ms for 10K objects

async def test_memory_usage():
    """Measure memory footprint"""
    # Should use < 500MB for 50K objects
```

#### 5.2 Load Testing

```python
async def test_concurrent_searches():
    """Test 100 concurrent search queries"""
    # All queries should complete without errors

async def test_cache_refresh_under_load():
    """Test cache refresh while handling queries"""
    # Should not block query operations
```

### Backward Compatibility

#### Configuration Compatibility

Old config (still works):

```yaml
vector:
  enabled: false  # Ignored, always enabled now
```

New config (recommended):

```yaml
database:
  metadata_cache:
    enabled: true
    cache_dir: ~/.aishell/cache/db_metadata
    auto_refresh_interval: 3600
    embedding_model: all-MiniLM-L6-v2
```

#### Graceful Degradation

If FAISS import fails (shouldn't happen), provide clear error:

```python
try:
    import faiss
except ImportError as e:
    logger.error(
        "FAISS is required for AIShell but not installed. "
        "Install with: pip install faiss-cpu"
    )
    sys.exit(1)
```

---

## Security Considerations

### Data Privacy

#### 1. Sensitive Data in Embeddings

**Risk**: Embeddings might encode sensitive information from column names, descriptions.

**Mitigation**:

```python
class SensitiveDataFilter:
    """Filter sensitive data before embedding"""

    SENSITIVE_PATTERNS = [
        r'password',
        r'ssn',
        r'credit[_-]?card',
        r'api[_-]?key',
        r'secret'
    ]

    def sanitize_metadata(self, text: str) -> str:
        """Remove or redact sensitive information"""
        for pattern in self.SENSITIVE_PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        return text
```

#### 2. Cache File Permissions

**Risk**: Cache files contain database structure information.

**Mitigation**:

```python
def save_cache(self, path: str):
    """Save cache with restricted permissions"""

    # Write with owner-only permissions
    with open(path, 'wb') as f:
        os.chmod(path, 0o600)  # rw-------
        pickle.dump(data, f)
```

#### 3. Connection Credentials

**Risk**: Connection metadata might expose connection details.

**Mitigation**:

```python
@dataclass
class ConnectionMetadata:
    connection_id: str
    connection_type: str
    # DO NOT STORE:
    # - host
    # - port
    # - username
    # - password
```

### Access Control

#### 1. Connection-Based Filtering

```python
async def search_tables(
    self,
    query: str,
    connection_id: Optional[str] = None,
    user_permissions: Optional[List[str]] = None  # NEW
):
    """Filter results by user permissions"""

    results = await self._search_internal(query, connection_id)

    if user_permissions:
        # Filter results based on user's allowed connections
        results = [
            r for r in results
            if r.connection_id in user_permissions
        ]

    return results
```

#### 2. Audit Logging

```python
class AuditLogger:
    """Log cache operations for security auditing"""

    async def log_search(
        self,
        user: str,
        query: str,
        connection_id: str,
        results_count: int
    ):
        """Log search operation"""
        logger.info(
            f"AUDIT: user={user} action=search "
            f"connection={connection_id} query={query} "
            f"results={results_count}"
        )
```

---

## Testing Strategy

### Unit Tests

#### Vector Store Tests

```python
# tests/vector/test_store_enhanced.py

async def test_faiss_required():
    """Verify FAISS import is required"""
    # Should not fall back to mock

async def test_batch_add_performance():
    """Test batch add is faster than individual adds"""

async def test_persistence():
    """Test save/load round-trip"""

async def test_connection_filtering():
    """Test filtering by connection_id"""
```

#### Metadata Cache Tests

```python
# tests/database/test_metadata_cache.py

async def test_index_database():
    """Test indexing a single database"""

async def test_search_tables_semantic():
    """Test semantic table search"""

async def test_search_columns_filtered():
    """Test column search with filters"""

async def test_cache_invalidation():
    """Test cache invalidation on schema change"""

async def test_foreign_key_discovery():
    """Test relationship search"""
```

### Integration Tests

```python
# tests/integration/test_mcp_metadata_cache.py

async def test_multiple_connections():
    """Test cache with multiple MCP connections"""

async def test_concurrent_indexing():
    """Test parallel database indexing"""

async def test_cache_persistence_across_sessions():
    """Test cache survives restart"""

async def test_incremental_updates():
    """Test incremental indexing after schema changes"""
```

### Performance Tests

```python
# tests/benchmarks/test_metadata_performance.py

async def test_indexing_100_tables():
    """Benchmark indexing 100 tables"""
    # Target: < 30 seconds

async def test_search_latency_1000_objects():
    """Benchmark search with 1000 objects"""
    # Target: < 50ms

async def test_memory_usage_10k_objects():
    """Measure memory with 10K objects"""
    # Target: < 300MB
```

### End-to-End Tests

```python
# tests/e2e/test_metadata_cache_cli.py

async def test_cli_init_cache(tmp_path):
    """Test 'ai-shell db init-cache' command"""

async def test_cli_search_tables():
    """Test 'ai-shell db search-tables' command"""

async def test_interactive_mode_search():
    """Test search in interactive mode"""
```

---

## Architecture Decision Records

### ADR-001: FAISS as Hard Requirement

**Status**: Accepted

**Context**:
- Current implementation has mock fallback for FAISS
- Mock provides no semantic search capability
- FAISS is lightweight (10-50MB) and widely supported

**Decision**:
Make FAISS a hard requirement, remove mock implementation.

**Consequences**:
- Positive: Simpler code, guaranteed semantic search
- Positive: Better testing (no mock path)
- Negative: Additional dependency for users
- Mitigation: FAISS-CPU is cross-platform and easy to install

**Alternatives Considered**:
1. Keep mock fallback → Rejected: No value without semantic search
2. Use different vector DB (Annoy, HNSWLIB) → Rejected: FAISS is industry standard

---

### ADR-002: Sentence Transformers for Embeddings

**Status**: Accepted

**Context**:
- Need to convert metadata text to vectors
- Options: OpenAI embeddings, Sentence Transformers, custom model

**Decision**:
Use Sentence Transformers with `all-MiniLM-L6-v2` model (384 dimensions).

**Rationale**:
- Local execution (no API calls)
- High quality embeddings
- Small model size (~80MB)
- Fast inference (< 50ms per batch)

**Consequences**:
- Positive: No external API dependencies
- Positive: Predictable performance
- Negative: Model download on first use
- Negative: 384-dim vectors (vs 1536 for OpenAI)

---

### ADR-003: Eager Metadata Extraction vs Lazy

**Status**: Accepted

**Context**:
- Should we extract all metadata upfront or on-demand?

**Decision**:
Eager extraction during indexing, lazy loading for detailed metadata.

**Rationale**:
- Indexing: Extract all metadata for complete cache
- Searching: Return lightweight results, load details on-demand
- Balance: Good performance without excessive memory

**Implementation**:
```python
# Eager: All metadata extracted during index_database()
await cache.index_database("conn1")  # Extracts everything

# Lazy: Details loaded only when requested
result = await cache.search_tables("users")[0]
full_metadata = await result.get_full_metadata()  # Loads details
```

---

### ADR-004: Cache Invalidation Strategy

**Status**: Accepted

**Context**:
- Database schemas can change
- Need to detect changes and update cache

**Decision**:
Hybrid approach:
1. Schema version hashing for change detection
2. Periodic automatic refresh (default: 1 hour)
3. Manual invalidation API

**Rationale**:
- Hash-based detection is fast and reliable
- Periodic refresh catches changes without monitoring
- Manual API for explicit control

**Implementation**:
```python
# Schema hash includes:
# - Table names and row counts
# - Column names and types
# - Index definitions
# - Constraint definitions

version_hash = hashlib.sha256(
    json.dumps(schema_summary, sort_keys=True).encode()
).hexdigest()
```

---

### ADR-005: Persistence Format

**Status**: Accepted

**Context**:
- Need to persist cache across sessions
- Options: SQLite, JSON, Pickle, Custom binary

**Decision**:
Hybrid approach:
- FAISS index → Native FAISS binary format (`.faiss`)
- Metadata → JSON (`.json`)
- Mappings → JSON (`.json`)

**Rationale**:
- FAISS binary: Optimized for FAISS loading
- JSON: Human-readable, debuggable, versionable
- No pickle: Security concerns, Python version lock-in

**Structure**:
```
~/.aishell/cache/db_metadata/
├── faiss_index.bin          # FAISS native format
├── metadata.json            # All metadata objects
├── version.json             # Schema version tracking
└── connections.json         # Connection-to-objects mapping
```

---

### ADR-006: Embedding Text Format

**Status**: Accepted

**Context**:
- How to structure text for embedding generation?
- Need to balance context and specificity

**Decision**:
Structured template-based text with hierarchical information.

**Template**:
```python
# Table:
"Table {table_name} in {schema} schema. {description}. "
"Contains columns: {column_list}. "
"Has indexes: {index_list}. "
"Foreign keys: {fk_summary}."

# Column:
"Column {table}.{column} in {schema} schema. "
"Type {data_type}. {constraints}. "
"{description}. {usage_context}."
```

**Rationale**:
- Provides rich context for semantic search
- Includes relationships for better relevance
- Natural language structure works well with sentence transformers

---

## Summary

This architecture design provides a comprehensive blueprint for implementing a FAISS-based database dictionary caching system in AIShell. Key highlights:

### Technical Decisions

1. **FAISS Hard Requirement**: Removes complexity, ensures semantic search
2. **Sentence Transformers**: Local, fast, high-quality embeddings
3. **Hybrid Persistence**: FAISS binary + JSON for balance of performance and debuggability
4. **Eager Indexing, Lazy Details**: Optimizes for common use cases

### Performance Targets

- **Indexing**: 100 tables in < 30 seconds
- **Search**: < 100ms for 10K objects
- **Memory**: < 300MB for typical database

### Integration Points

- **DatabaseModule**: Primary integration for search APIs
- **AIShell Main**: Initialization and lifecycle management
- **Interactive Mode**: Rich command set for exploration
- **CLI Mode**: Scriptable commands for automation

### Migration Path

- **Week 1**: Prerequisites and infrastructure
- **Week 2-3**: Core implementation
- **Week 4**: Integration and commands
- **Week 5**: Documentation
- **Week 6**: Performance validation

This design ensures AIShell can intelligently cache and search database metadata across all MCP-connected databases, providing fast, semantic search capabilities that enhance the AI-powered database management experience.
