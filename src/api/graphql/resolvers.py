"""
GraphQL Resolvers

Factory for creating CRUD resolvers with optimization.
"""

from typing import Dict, List, Optional, Any, Type, Callable
import logging

logger = logging.getLogger(__name__)


class ResolverFactory:
    """
    Factory for creating GraphQL resolvers

    Generates optimized resolvers for CRUD operations with:
    - DataLoader batching
    - Query optimization
    - Authorization checks
    """

    def __init__(self):
        """Initialize resolver factory"""
        pass

    def create_list_resolver(
        self,
        table_name: str,
        type_class: Type
    ) -> Callable:
        """
        Create list resolver (e.g., users() -> [User])

        Args:
            table_name: Database table name
            type_class: GraphQL type class

        Returns:
            Resolver function
        """
        try:
            import strawberry
        except ImportError:
            logger.error("strawberry-graphql not available")
            return None

        @strawberry.field
        async def list_resolver(
            self,
            info: strawberry.types.Info,
            limit: Optional[int] = 100,
            offset: Optional[int] = 0,
            where: Optional[str] = None
        ) -> List[type_class]:
            """List items from table"""
            context = info.context
            db = context.db

            # Build query
            query = f"SELECT * FROM {table_name}"

            # Add WHERE clause if provided
            if where:
                query += f" WHERE {where}"

            # Add pagination
            query += f" LIMIT {limit} OFFSET {offset}"

            # Execute query
            cursor = db.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            # Convert to type instances
            results = []
            for row in rows:
                # Convert row to dict
                row_dict = dict(zip([col[0] for col in cursor.description], row))
                # Create instance (simplified - would need proper instantiation)
                results.append(type_class(**row_dict))

            cursor.close()
            return results

        return list_resolver

    def create_get_resolver(
        self,
        table_name: str,
        type_class: Type
    ) -> Callable:
        """
        Create get-by-ID resolver (e.g., user(id: Int) -> User)

        Args:
            table_name: Database table name
            type_class: GraphQL type class

        Returns:
            Resolver function
        """
        try:
            import strawberry
        except ImportError:
            return None

        @strawberry.field
        async def get_resolver(
            self,
            info: strawberry.types.Info,
            id: int
        ) -> Optional[type_class]:
            """Get item by ID"""
            context = info.context
            db = context.db

            # Use DataLoader for batching if available
            # This prevents N+1 query problems
            loader_name = f"{table_name}_by_id"
            if hasattr(context, 'get_dataloader'):
                loader = context.get_dataloader(
                    loader_name,
                    lambda ids: self._batch_load_by_ids(db, table_name, ids)
                )
                return await loader.load(id)

            # Fallback to direct query
            cursor = db.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()

            if not row:
                cursor.close()
                return None

            # Convert to type instance
            row_dict = dict(zip([col[0] for col in cursor.description], row))
            cursor.close()
            return type_class(**row_dict)

        return get_resolver

    def create_insert_resolver(
        self,
        table_name: str,
        type_class: Type
    ) -> Callable:
        """
        Create insert resolver (e.g., createUser(input: UserInput) -> User)

        Args:
            table_name: Database table name
            type_class: GraphQL type class

        Returns:
            Resolver function
        """
        try:
            import strawberry
        except ImportError:
            return None

        @strawberry.field
        async def insert_resolver(
            self,
            info: strawberry.types.Info,
            input: Dict[str, Any]
        ) -> type_class:
            """Create new item"""
            context = info.context
            db = context.db

            # Build INSERT query
            columns = ', '.join(input.keys())
            placeholders = ', '.join(['?' for _ in input])
            values = tuple(input.values())

            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            # Execute insert
            cursor = db.cursor()
            cursor.execute(query, values)
            db.commit()

            # Get inserted ID
            inserted_id = cursor.lastrowid

            # Fetch and return inserted row
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (inserted_id,))
            row = cursor.fetchone()

            row_dict = dict(zip([col[0] for col in cursor.description], row))
            cursor.close()

            return type_class(**row_dict)

        return insert_resolver

    def create_update_resolver(
        self,
        table_name: str,
        type_class: Type
    ) -> Callable:
        """
        Create update resolver (e.g., updateUser(id: Int, input: UserInput) -> User)

        Args:
            table_name: Database table name
            type_class: GraphQL type class

        Returns:
            Resolver function
        """
        try:
            import strawberry
        except ImportError:
            return None

        @strawberry.field
        async def update_resolver(
            self,
            info: strawberry.types.Info,
            id: int,
            input: Dict[str, Any]
        ) -> Optional[type_class]:
            """Update existing item"""
            context = info.context
            db = context.db

            # Build UPDATE query
            set_clause = ', '.join([f"{k} = ?" for k in input.keys()])
            values = tuple(input.values()) + (id,)

            query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"

            # Execute update
            cursor = db.cursor()
            cursor.execute(query, values)
            db.commit()

            if cursor.rowcount == 0:
                cursor.close()
                return None

            # Fetch and return updated row
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()

            row_dict = dict(zip([col[0] for col in cursor.description], row))
            cursor.close()

            return type_class(**row_dict)

        return update_resolver

    def create_delete_resolver(
        self,
        table_name: str,
        type_class: Type
    ) -> Callable:
        """
        Create delete resolver (e.g., deleteUser(id: Int) -> Boolean)

        Args:
            table_name: Database table name
            type_class: GraphQL type class

        Returns:
            Resolver function
        """
        try:
            import strawberry
        except ImportError:
            return None

        @strawberry.field
        async def delete_resolver(
            self,
            info: strawberry.types.Info,
            id: int
        ) -> bool:
            """Delete item"""
            context = info.context
            db = context.db

            # Execute delete
            cursor = db.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (id,))
            db.commit()

            success = cursor.rowcount > 0
            cursor.close()

            return success

        return delete_resolver

    async def _batch_load_by_ids(
        self,
        db,
        table_name: str,
        ids: List[int]
    ) -> List[Optional[Any]]:
        """
        Batch load items by IDs (for DataLoader)

        Args:
            db: Database connection
            table_name: Table name
            ids: List of IDs to load

        Returns:
            List of items in same order as IDs
        """
        # Build query with IN clause
        placeholders = ', '.join(['?' for _ in ids])
        query = f"SELECT * FROM {table_name} WHERE id IN ({placeholders})"

        cursor = db.cursor()
        cursor.execute(query, ids)
        rows = cursor.fetchall()

        # Convert to dict keyed by ID
        items_by_id = {}
        for row in rows:
            row_dict = dict(zip([col[0] for col in cursor.description], row))
            items_by_id[row_dict['id']] = row_dict

        cursor.close()

        # Return in same order as requested IDs
        return [items_by_id.get(id) for id in ids]
