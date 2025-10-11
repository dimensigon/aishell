"""
Neo4j Graph Database MCP Client

Provides integration with Neo4j graph database, supporting Cypher queries,
graph operations, and relationship management.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    MCP client for Neo4j graph database operations.

    Supports:
    - Cypher query execution
    - Node operations
    - Relationship management
    - Graph algorithms
    - Transactions
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str = "neo4j",
        encrypted: bool = True,
        **kwargs
    ):
        """
        Initialize Neo4j client

        Args:
            uri: Neo4j connection URI
            username: Authentication username
            password: Authentication password
            database: Database name
            encrypted: Use encryption
            **kwargs: Additional driver options
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.encrypted = encrypted
        self.driver_options = kwargs

        self.driver = None

        logger.info(f"Initialized Neo4j client (uri={uri}, database={database})")

    async def connect(self) -> None:
        """Establish connection to Neo4j"""
        try:
            from neo4j import GraphDatabase

            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                encrypted=self.encrypted,
                **self.driver_options
            )

            # Verify connectivity
            if self.driver:
                self.driver.verify_connectivity()
                logger.info("Connected to Neo4j")

        except ImportError:
            raise ImportError(
                "neo4j driver not installed. Install with: pip install neo4j"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Neo4j"""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database to execute against

        Returns:
            List of result records
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")

        db = database or self.database

        try:
            with self.driver.session(database=db) as session:
                result = session.run(query, parameters or {})
                records = [dict(record) for record in result]

            logger.debug(
                f"Executed query: {query[:100]}... "
                f"(returned {len(records)} records)"
            )
            return records

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute write query in write transaction

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database to execute against

        Returns:
            List of result records
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")

        db = database or self.database

        def _execute_write(tx):
            result = tx.run(query, parameters or {})
            return [dict(record) for record in result]

        try:
            with self.driver.session(database=db) as session:
                records = session.execute_write(_execute_write)

            logger.debug(f"Executed write query: {query[:100]}...")
            return records

        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            raise

    async def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute read query in read transaction

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database to execute against

        Returns:
            List of result records
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")

        db = database or self.database

        def _execute_read(tx):
            result = tx.run(query, parameters or {})
            return [dict(record) for record in result]

        try:
            with self.driver.session(database=db) as session:
                records = session.execute_read(_execute_read)

            logger.debug(f"Executed read query: {query[:100]}...")
            return records

        except Exception as e:
            logger.error(f"Read query execution failed: {e}")
            raise

    async def create_node(
        self,
        labels: Union[str, List[str]],
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create node with labels and properties

        Args:
            labels: Node label(s)
            properties: Node properties

        Returns:
            Created node data
        """
        if isinstance(labels, str):
            labels = [labels]

        label_str = ":".join(labels)
        query = f"CREATE (n:{label_str} $props) RETURN n"

        results = await self.execute_write(query, {"props": properties})
        logger.info(f"Created node with labels {label_str}")

        return results[0]['n'] if results else {}

    async def get_node(
        self,
        label: str,
        property_key: str,
        property_value: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Get node by label and property

        Args:
            label: Node label
            property_key: Property key to match
            property_value: Property value to match

        Returns:
            Node data or None
        """
        query = f"MATCH (n:{label} {{{property_key}: $value}}) RETURN n LIMIT 1"
        results = await self.execute_read(query, {"value": property_value})

        if results:
            logger.debug(f"Found node {label} with {property_key}={property_value}")
            node_data = results[0].get('n')
            return dict(node_data) if node_data else None

        logger.debug(f"Node not found: {label} with {property_key}={property_value}")
        return None

    async def update_node(
        self,
        label: str,
        match_property: str,
        match_value: Any,
        update_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update node properties

        Args:
            label: Node label
            match_property: Property to match node
            match_value: Value to match
            update_properties: Properties to update

        Returns:
            Updated node data
        """
        query = f"""
        MATCH (n:{label} {{{match_property}: $match_value}})
        SET n += $props
        RETURN n
        """

        results = await self.execute_write(
            query,
            {"match_value": match_value, "props": update_properties}
        )

        logger.info(f"Updated node {label} with {match_property}={match_value}")
        return results[0]['n'] if results else {}

    async def delete_node(
        self,
        label: str,
        property_key: str,
        property_value: Any,
        detach: bool = True
    ) -> int:
        """
        Delete node

        Args:
            label: Node label
            property_key: Property key to match
            property_value: Property value to match
            detach: Also delete relationships

        Returns:
            Number of nodes deleted
        """
        detach_str = "DETACH " if detach else ""
        query = f"""
        MATCH (n:{label} {{{property_key}: $value}})
        {detach_str}DELETE n
        RETURN count(n) as deleted
        """

        results = await self.execute_write(query, {"value": property_value})
        deleted = results[0]['deleted'] if results else 0

        logger.info(
            f"Deleted {deleted} node(s) {label} with {property_key}={property_value}"
        )
        return deleted

    async def create_relationship(
        self,
        from_label: str,
        from_property: str,
        from_value: Any,
        to_label: str,
        to_property: str,
        to_value: Any,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create relationship between nodes

        Args:
            from_label: Source node label
            from_property: Source node property key
            from_value: Source node property value
            to_label: Target node label
            to_property: Target node property key
            to_value: Target node property value
            relationship_type: Relationship type
            properties: Relationship properties

        Returns:
            Created relationship data
        """
        query = f"""
        MATCH (a:{from_label} {{{from_property}: $from_value}})
        MATCH (b:{to_label} {{{to_property}: $to_value}})
        CREATE (a)-[r:{relationship_type}]->(b)
        SET r = $props
        RETURN r
        """

        results = await self.execute_write(
            query,
            {
                "from_value": from_value,
                "to_value": to_value,
                "props": properties or {}
            }
        )

        logger.info(f"Created relationship {relationship_type}")
        return results[0]['r'] if results else {}

    async def get_relationships(
        self,
        label: str,
        property_key: str,
        property_value: Any,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Get node relationships

        Args:
            label: Node label
            property_key: Node property key
            property_value: Node property value
            direction: Direction ('incoming', 'outgoing', 'both')

        Returns:
            List of relationships
        """
        if direction == "incoming":
            pattern = "(n)<-[r]-"
        elif direction == "outgoing":
            pattern = "(n)-[r]->"
        else:
            pattern = "(n)-[r]-"

        query = f"""
        MATCH {pattern}(m)
        WHERE n:{label} AND n.{property_key} = $value
        RETURN r, labels(m) as target_labels, m as target_node
        """

        results = await self.execute_read(query, {"value": property_value})
        logger.debug(f"Found {len(results)} relationships")
        return results

    async def execute_graph_algorithm(
        self,
        algorithm: str,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute graph algorithm

        Args:
            algorithm: Algorithm name (e.g., 'pageRank', 'shortestPath')
            parameters: Algorithm parameters

        Returns:
            Algorithm results
        """
        # This is a placeholder - actual implementation depends on GDS library
        logger.warning(
            f"Graph algorithm execution requires Neo4j GDS library: {algorithm}"
        )
        raise NotImplementedError(
            "Graph algorithms require Neo4j Graph Data Science library"
        )

    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        query = """
        CALL dbms.components() YIELD name, versions, edition
        RETURN name, versions, edition
        """

        results = await self.execute_query(query)
        return results[0] if results else {}

    async def get_node_count(self, label: Optional[str] = None) -> int:
        """Get count of nodes"""
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) as count"
        else:
            query = "MATCH (n) RETURN count(n) as count"

        results = await self.execute_read(query)
        return results[0]['count'] if results else 0

    async def get_relationship_count(
        self,
        relationship_type: Optional[str] = None
    ) -> int:
        """Get count of relationships"""
        if relationship_type:
            query = f"MATCH ()-[r:{relationship_type}]-() RETURN count(r) as count"
        else:
            query = "MATCH ()-[r]-() RETURN count(r) as count"

        results = await self.execute_read(query)
        return results[0]['count'] if results else 0

    def __enter__(self):
        """Context manager entry"""
        import asyncio
        asyncio.create_task(self.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        import asyncio
        asyncio.create_task(self.disconnect())
