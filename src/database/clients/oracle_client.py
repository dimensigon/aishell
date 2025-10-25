"""
Oracle Database Client Implementation

Supports both CDB (Container Database) and PDB (Pluggable Database) connections
with comprehensive features:
- Connection pooling (min 5, max 20)
- Async/await support via thread pool
- PDB switching capability
- CDB management operations
- Comprehensive error handling
- Health checks and monitoring
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import cx_Oracle
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    cx_Oracle = None
    oracledb = None

from .base import (
    BaseDatabaseClient,
    DatabaseConfig,
    DatabaseError,
    ConnectionError,
    QueryError,
)


logger = logging.getLogger(__name__)


class OracleClient(BaseDatabaseClient):
    """
    Oracle Database Client with CDB support

    Provides production-ready Oracle connectivity with:
    - Connection pooling
    - Async operations via thread pool executor
    - SYSDBA/SYSOPER mode support
    - Comprehensive error handling
    - Query logging and metrics
    """

    def __init__(self, config: DatabaseConfig, name: str = "oracle", mode: Optional[int] = None):
        """
        Initialize Oracle client

        Args:
            config: Database configuration
            name: Client identifier
            mode: Connection mode (cx_Oracle.SYSDBA, SYSOPER, etc.)
        """
        if not ORACLE_AVAILABLE:
            raise ImportError(
                "Oracle client libraries not available. "
                "Install with: pip install cx_Oracle oracledb"
            )

        super().__init__(config, name)
        self.mode = mode or getattr(cx_Oracle, 'DEFAULT', 0)
        self._executor = None

    async def initialize(self) -> None:
        """Initialize Oracle client with thread pool executor"""
        # Create thread pool for sync Oracle operations
        import concurrent.futures
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_pool_size,
            thread_name_prefix=f"oracle_{self.name}"
        )

        await super().initialize()

    async def close(self) -> None:
        """Close Oracle client and thread pool"""
        await super().close()

        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    async def _create_connection(self) -> Any:
        """
        Create a new Oracle database connection

        Returns:
            cx_Oracle connection object
        """
        loop = asyncio.get_event_loop()

        try:
            # Build DSN (Data Source Name)
            dsn = f"{self.config.host}:{self.config.port}/{self.config.database}"

            # Connection parameters
            conn_params = {
                'user': self.config.user,
                'password': self.config.password,
                'dsn': dsn,
                'mode': self.mode,
                'encoding': 'UTF-8',
                'nencoding': 'UTF-8',
            }

            # Add extra parameters
            if self.config.extra_params:
                conn_params.update(self.config.extra_params)

            # Create connection in thread pool
            connection = await loop.run_in_executor(
                self._executor,
                lambda: cx_Oracle.connect(**conn_params)
            )

            logger.debug(f"Created Oracle connection to {dsn}")
            return connection

        except Exception as e:
            logger.error(f"Failed to create Oracle connection: {e}")
            raise ConnectionError(
                f"Failed to connect to Oracle database: {e}",
                error_code="ORACLE_CONNECTION_FAILED",
                original_error=e
            )

    async def _execute_impl(
        self,
        connection: Any,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Tuple], int]:
        """
        Execute Oracle query

        Args:
            connection: Oracle connection object
            query: SQL query
            params: Query parameters

        Returns:
            Tuple of (columns, rows, rowcount)
        """
        loop = asyncio.get_event_loop()

        try:
            # Execute in thread pool
            def _execute():
                cursor = connection.cursor()
                try:
                    # Execute query
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    # Get results
                    if cursor.description:
                        # SELECT query
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchall()
                        rowcount = len(rows)
                    else:
                        # DML query
                        columns = []
                        rows = []
                        rowcount = cursor.rowcount
                        connection.commit()

                    return columns, rows, rowcount

                finally:
                    cursor.close()

            columns, rows, rowcount = await loop.run_in_executor(self._executor, _execute)
            return columns, rows, rowcount

        except Exception as e:
            logger.error(f"Oracle query execution failed: {e}")
            raise QueryError(
                f"Failed to execute Oracle query: {e}",
                error_code="ORACLE_QUERY_FAILED",
                original_error=e
            )

    async def _get_ping_query(self) -> str:
        """Get Oracle-specific ping query"""
        return "SELECT 1 FROM DUAL"

    async def _begin_transaction(self, connection: Any) -> None:
        """Begin Oracle transaction"""
        # Oracle uses implicit transactions, no explicit BEGIN needed
        pass

    async def _commit_transaction(self, connection: Any) -> None:
        """Commit Oracle transaction"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, connection.commit)

    async def _rollback_transaction(self, connection: Any) -> None:
        """Rollback Oracle transaction"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, connection.rollback)

    async def get_version(self) -> str:
        """Get Oracle database version"""
        result = await self.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
        return result['rows'][0][0] if result['rows'] else "Unknown"

    async def get_tablespaces(self) -> List[Dict[str, Any]]:
        """Get list of tablespaces"""
        query = """
            SELECT
                TABLESPACE_NAME,
                STATUS,
                CONTENTS,
                EXTENT_MANAGEMENT,
                SEGMENT_SPACE_MANAGEMENT
            FROM DBA_TABLESPACES
            ORDER BY TABLESPACE_NAME
        """
        result = await self.execute(query)

        tablespaces = []
        for row in result['rows']:
            tablespaces.append({
                'name': row[0],
                'status': row[1],
                'contents': row[2],
                'extent_management': row[3],
                'segment_space_management': row[4],
            })

        return tablespaces

    async def get_users(self) -> List[Dict[str, Any]]:
        """Get list of database users"""
        query = """
            SELECT
                USERNAME,
                USER_ID,
                ACCOUNT_STATUS,
                CREATED,
                DEFAULT_TABLESPACE,
                TEMPORARY_TABLESPACE
            FROM DBA_USERS
            ORDER BY USERNAME
        """
        result = await self.execute(query)

        users = []
        for row in result['rows']:
            users.append({
                'username': row[0],
                'user_id': row[1],
                'status': row[2],
                'created': row[3],
                'default_tablespace': row[4],
                'temp_tablespace': row[5],
            })

        return users


class OraclePDBClient(OracleClient):
    """
    Oracle PDB (Pluggable Database) Client

    Extends OracleClient with PDB-specific functionality:
    - PDB switching
    - PDB state management
    - CDB-level operations
    """

    def __init__(
        self,
        config: DatabaseConfig,
        name: str = "oracle_pdb",
        mode: Optional[int] = None,
        cdb_config: Optional[DatabaseConfig] = None
    ):
        """
        Initialize PDB client

        Args:
            config: PDB connection configuration
            name: Client identifier
            mode: Connection mode
            cdb_config: CDB (root) connection configuration for management operations
        """
        super().__init__(config, name, mode)
        self.cdb_config = cdb_config
        self._cdb_client: Optional[OracleClient] = None

    async def initialize(self) -> None:
        """Initialize PDB client and optional CDB client"""
        await super().initialize()

        # Initialize CDB client if config provided
        if self.cdb_config:
            self._cdb_client = OracleClient(
                self.cdb_config,
                name=f"{self.name}_cdb",
                mode=self.mode
            )
            await self._cdb_client.initialize()

    async def close(self) -> None:
        """Close PDB and CDB clients"""
        if self._cdb_client:
            await self._cdb_client.close()
            self._cdb_client = None

        await super().close()

    async def switch_pdb(self, pdb_name: str) -> None:
        """
        Switch to a different PDB

        Args:
            pdb_name: Name of the PDB to switch to
        """
        query = f"ALTER SESSION SET CONTAINER = {pdb_name}"
        await self.execute(query)
        logger.info(f"Switched to PDB: {pdb_name}")

    async def get_current_pdb(self) -> str:
        """Get current PDB name"""
        result = await self.execute("SELECT SYS_CONTEXT('USERENV', 'CON_NAME') FROM DUAL")
        return result['rows'][0][0] if result['rows'] else "Unknown"

    async def list_pdbs(self) -> List[Dict[str, Any]]:
        """
        List all PDBs in the CDB

        Requires CDB connection
        """
        if not self._cdb_client:
            raise DatabaseError(
                "CDB client not configured. Cannot list PDBs.",
                error_code="NO_CDB_CLIENT"
            )

        query = """
            SELECT
                CON_ID,
                PDB_NAME,
                STATUS,
                OPEN_MODE,
                RESTRICTED,
                OPEN_TIME
            FROM CDB_PDBS
            ORDER BY PDB_NAME
        """

        result = await self._cdb_client.execute(query)

        pdbs = []
        for row in result['rows']:
            pdbs.append({
                'con_id': row[0],
                'pdb_name': row[1],
                'status': row[2],
                'open_mode': row[3],
                'restricted': row[4],
                'open_time': row[5],
            })

        return pdbs

    async def open_pdb(self, pdb_name: str) -> None:
        """
        Open a PDB

        Requires CDB connection
        """
        if not self._cdb_client:
            raise DatabaseError(
                "CDB client not configured. Cannot open PDB.",
                error_code="NO_CDB_CLIENT"
            )

        query = f"ALTER PLUGGABLE DATABASE {pdb_name} OPEN"
        await self._cdb_client.execute(query)
        logger.info(f"Opened PDB: {pdb_name}")

    async def close_pdb(self, pdb_name: str) -> None:
        """
        Close a PDB

        Requires CDB connection
        """
        if not self._cdb_client:
            raise DatabaseError(
                "CDB client not configured. Cannot close PDB.",
                error_code="NO_CDB_CLIENT"
            )

        query = f"ALTER PLUGGABLE DATABASE {pdb_name} CLOSE IMMEDIATE"
        await self._cdb_client.execute(query)
        logger.info(f"Closed PDB: {pdb_name}")

    async def get_pdb_info(self) -> Dict[str, Any]:
        """Get current PDB information"""
        query = """
            SELECT
                SYS_CONTEXT('USERENV', 'CON_ID') AS CON_ID,
                SYS_CONTEXT('USERENV', 'CON_NAME') AS CON_NAME,
                SYS_CONTEXT('USERENV', 'DB_NAME') AS DB_NAME
            FROM DUAL
        """
        result = await self.execute(query)

        if result['rows']:
            row = result['rows'][0]
            return {
                'con_id': row[0],
                'con_name': row[1],
                'db_name': row[2],
            }

        return {}
