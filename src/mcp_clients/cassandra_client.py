"""
Apache Cassandra MCP Client

Provides integration with Apache Cassandra distributed NoSQL database,
supporting CQL queries, async operations, and cluster management.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)


class CassandraClient:
    """
    MCP client for Apache Cassandra database operations.

    Supports:
    - CQL query execution
    - Prepared statements
    - Batch operations
    - Async queries
    - Cluster management
    """

    def __init__(
        self,
        contact_points: List[str],
        port: int = 9042,
        keyspace: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        protocol_version: int = 4,
        **kwargs
    ):
        """
        Initialize Cassandra client

        Args:
            contact_points: List of Cassandra node addresses
            port: Cassandra port (default: 9042)
            keyspace: Default keyspace
            username: Authentication username
            password: Authentication password
            protocol_version: CQL protocol version
            **kwargs: Additional driver options
        """
        self.contact_points = contact_points
        self.port = port
        self.keyspace = keyspace
        self.username = username
        self.password = password
        self.protocol_version = protocol_version
        self.driver_options = kwargs

        self.cluster = None
        self.session = None
        self.prepared_statements: Dict[str, Any] = {}

        logger.info(
            f"Initialized Cassandra client "
            f"(nodes={','.join(contact_points)}, keyspace={keyspace})"
        )

    async def connect(self) -> None:
        """Establish connection to Cassandra cluster"""
        try:
            # Import here to make cassandra-driver optional
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider

            auth_provider = None
            if self.username and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.username,
                    password=self.password
                )

            self.cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port,
                auth_provider=auth_provider,
                protocol_version=self.protocol_version,
                **self.driver_options
            )

            if self.cluster:
                self.session = self.cluster.connect(self.keyspace)
                logger.info("Connected to Cassandra cluster")

        except ImportError:
            raise ImportError(
                "cassandra-driver not installed. "
                "Install with: pip install cassandra-driver"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Cassandra cluster"""
        if self.session:
            self.session.shutdown()
            logger.debug("Closed Cassandra session")

        if self.cluster:
            self.cluster.shutdown()
            logger.info("Disconnected from Cassandra cluster")

    async def execute(
        self,
        query: str,
        parameters: Optional[Tuple] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Execute CQL query

        Args:
            query: CQL query string
            parameters: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Query result
        """
        if not self.session:
            raise RuntimeError("Not connected to Cassandra")

        try:
            if parameters:
                result = self.session.execute(query, parameters, timeout=timeout)
            else:
                result = self.session.execute(query, timeout=timeout)

            logger.debug(f"Executed query: {query[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def execute_async(
        self,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> Any:
        """
        Execute CQL query asynchronously

        Args:
            query: CQL query string
            parameters: Query parameters

        Returns:
            Future result
        """
        if not self.session:
            raise RuntimeError("Not connected to Cassandra")

        try:
            if parameters:
                future = self.session.execute_async(query, parameters)
            else:
                future = self.session.execute_async(query)

            logger.debug(f"Executing async query: {query[:100]}...")
            return future

        except Exception as e:
            logger.error(f"Async query execution failed: {e}")
            raise

    async def prepare(self, query: str) -> Any:
        """
        Prepare CQL statement for repeated execution

        Args:
            query: CQL query string

        Returns:
            Prepared statement
        """
        if not self.session:
            raise RuntimeError("Not connected to Cassandra")

        if query in self.prepared_statements:
            return self.prepared_statements[query]

        try:
            prepared = self.session.prepare(query)
            self.prepared_statements[query] = prepared
            logger.debug(f"Prepared statement: {query[:100]}...")
            return prepared

        except Exception as e:
            logger.error(f"Statement preparation failed: {e}")
            raise

    async def execute_prepared(
        self,
        query: str,
        parameters: Tuple,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Execute prepared statement

        Args:
            query: CQL query string (will be prepared if not cached)
            parameters: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Query result
        """
        prepared = await self.prepare(query)
        return await self.execute(prepared, parameters, timeout)

    async def batch_execute(
        self,
        queries: List[Tuple[str, Optional[Tuple]]],
        consistency_level: Optional[str] = None
    ) -> None:
        """
        Execute batch of queries

        Args:
            queries: List of (query, parameters) tuples
            consistency_level: Batch consistency level
        """
        if not self.session:
            raise RuntimeError("Not connected to Cassandra")

        try:
            from cassandra.query import BatchStatement, ConsistencyLevel

            batch = BatchStatement()

            if consistency_level:
                batch.consistency_level = getattr(
                    ConsistencyLevel,
                    consistency_level.upper()
                )

            for query, params in queries:
                if params:
                    batch.add(query, params)
                else:
                    batch.add(query)

            self.session.execute(batch)
            logger.info(f"Executed batch of {len(queries)} queries")

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise

    async def create_keyspace(
        self,
        keyspace: str,
        replication_strategy: str = "SimpleStrategy",
        replication_factor: int = 1
    ) -> None:
        """
        Create keyspace

        Args:
            keyspace: Keyspace name
            replication_strategy: Replication strategy
            replication_factor: Replication factor
        """
        query = f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH replication = {{
            'class': '{replication_strategy}',
            'replication_factor': {replication_factor}
        }}
        """
        await self.execute(query)
        logger.info(f"Created keyspace: {keyspace}")

    async def drop_keyspace(self, keyspace: str) -> None:
        """Drop keyspace"""
        query = f"DROP KEYSPACE IF EXISTS {keyspace}"
        await self.execute(query)
        logger.info(f"Dropped keyspace: {keyspace}")

    async def use_keyspace(self, keyspace: str) -> None:
        """Switch to keyspace"""
        if not self.session:
            raise RuntimeError("Not connected to Cassandra")

        self.session.set_keyspace(keyspace)
        self.keyspace = keyspace
        logger.info(f"Switched to keyspace: {keyspace}")

    async def get_cluster_metadata(self) -> Dict[str, Any]:
        """Get cluster metadata"""
        if not self.cluster:
            raise RuntimeError("Not connected to Cassandra")

        metadata = self.cluster.metadata

        return {
            "cluster_name": metadata.cluster_name,
            "partitioner": metadata.partitioner,
            "hosts": [str(host) for host in metadata.all_hosts()],
            "keyspaces": list(metadata.keyspaces.keys()),
            "token_map": len(metadata.token_map) if metadata.token_map else 0
        }

    async def get_keyspace_info(self, keyspace: str) -> Dict[str, Any]:
        """Get keyspace information"""
        if not self.cluster:
            raise RuntimeError("Not connected to Cassandra")

        ks_meta = self.cluster.metadata.keyspaces.get(keyspace)
        if not ks_meta:
            raise ValueError(f"Keyspace '{keyspace}' not found")

        return {
            "name": ks_meta.name,
            "replication_strategy": ks_meta.replication_strategy.name,
            "replication_factor": ks_meta.replication_strategy.replication_factor
            if hasattr(ks_meta.replication_strategy, 'replication_factor') else None,
            "durable_writes": ks_meta.durable_writes,
            "tables": list(ks_meta.tables.keys())
        }

    async def get_table_info(
        self,
        keyspace: str,
        table: str
    ) -> Dict[str, Any]:
        """Get table information"""
        if not self.cluster:
            raise RuntimeError("Not connected to Cassandra")

        ks_meta = self.cluster.metadata.keyspaces.get(keyspace)
        if not ks_meta:
            raise ValueError(f"Keyspace '{keyspace}' not found")

        table_meta = ks_meta.tables.get(table)
        if not table_meta:
            raise ValueError(f"Table '{table}' not found in keyspace '{keyspace}'")

        return {
            "name": table_meta.name,
            "columns": [
                {
                    "name": col.name,
                    "type": str(col.cql_type)
                }
                for col in table_meta.columns.values()
            ],
            "partition_key": [col.name for col in table_meta.partition_key],
            "clustering_key": [col.name for col in table_meta.clustering_key],
            "indexes": list(table_meta.indexes.keys())
        }

    def __enter__(self):
        """Context manager entry"""
        import asyncio
        asyncio.create_task(self.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        import asyncio
        asyncio.create_task(self.disconnect())
