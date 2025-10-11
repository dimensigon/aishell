"""
GraphQL Schema Generator

Automatically generates GraphQL schema from database structure.
"""

from typing import Dict, List, Optional, Any, Type
import logging
import sqlite3

logger = logging.getLogger(__name__)


class SchemaGenerator:
    """
    Generates GraphQL schema from database metadata

    Supports automatic type generation, relationships, and CRUD operations.
    """

    def __init__(self):
        """Initialize schema generator"""
        self.type_mappings = {
            'INTEGER': 'Int',
            'BIGINT': 'Int',
            'SMALLINT': 'Int',
            'REAL': 'Float',
            'FLOAT': 'Float',
            'DOUBLE': 'Float',
            'DECIMAL': 'Float',
            'NUMERIC': 'Float',
            'TEXT': 'String',
            'VARCHAR': 'String',
            'CHAR': 'String',
            'BLOB': 'String',
            'BOOLEAN': 'Boolean',
            'BOOL': 'Boolean',
            'DATE': 'String',
            'DATETIME': 'String',
            'TIMESTAMP': 'String',
            'TIME': 'String'
        }

    def generate_from_database(
        self,
        db_connection,
        tables: Optional[List[str]] = None
    ):
        """
        Generate GraphQL schema from database

        Args:
            db_connection: Database connection
            tables: List of tables to include (None for all)

        Returns:
            Strawberry GraphQL schema
        """
        try:
            import strawberry
        except ImportError:
            logger.error("strawberry-graphql not available")
            return None

        # Get database metadata
        table_info = self._extract_table_metadata(db_connection, tables)

        # Generate GraphQL types
        types = {}
        for table_name, columns in table_info.items():
            types[table_name] = self._create_graphql_type(
                strawberry,
                table_name,
                columns
            )

        # Generate Query type
        query_type = self._create_query_type(strawberry, types, table_info)

        # Generate Mutation type
        mutation_type = self._create_mutation_type(strawberry, types, table_info)

        # Create schema
        schema = strawberry.Schema(
            query=query_type,
            mutation=mutation_type
        )

        logger.info(f"Generated GraphQL schema with {len(types)} types")
        return schema

    def _extract_table_metadata(
        self,
        db_connection,
        tables: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract table metadata from database

        Args:
            db_connection: Database connection
            tables: Tables to include

        Returns:
            Dictionary mapping table names to column info
        """
        table_info = {}
        cursor = db_connection.cursor()

        # Get list of tables
        if isinstance(db_connection, sqlite3.Connection):
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor.fetchall()]
        else:
            # Generic approach for other databases
            all_tables = tables or []

        # Filter tables if specified
        tables_to_process = tables if tables else all_tables

        # Get column info for each table
        for table_name in tables_to_process:
            if isinstance(db_connection, sqlite3.Connection):
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[1],
                        'type': row[2],
                        'not_null': bool(row[3]),
                        'default': row[4],
                        'primary_key': bool(row[5])
                    })
                table_info[table_name] = columns
            else:
                # Would need database-specific implementation
                pass

        cursor.close()
        return table_info

    def _create_graphql_type(
        self,
        strawberry,
        table_name: str,
        columns: List[Dict[str, Any]]
    ) -> Type:
        """
        Create GraphQL type from table metadata

        Args:
            strawberry: Strawberry module
            table_name: Table name
            columns: Column metadata

        Returns:
            Strawberry type class
        """
        # Build field annotations
        annotations = {}
        for col in columns:
            graphql_type = self._map_sql_to_graphql_type(col['type'])

            # Make field optional if nullable
            if col['not_null'] and not col['primary_key']:
                annotations[col['name']] = graphql_type
            else:
                annotations[col['name']] = Optional[graphql_type]

        # Create type class dynamically
        type_name = self._to_pascal_case(table_name)
        type_class = type(
            type_name,
            (),
            {
                '__annotations__': annotations,
                '__strawberry_type__': True
            }
        )

        return strawberry.type(type_class)

    def _create_query_type(
        self,
        strawberry,
        types: Dict[str, Type],
        table_info: Dict[str, List[Dict]]
    ) -> Type:
        """
        Create Query type with resolvers

        Args:
            strawberry: Strawberry module
            types: Generated GraphQL types
            table_info: Table metadata

        Returns:
            Query type class
        """
        from src.api.graphql.resolvers import ResolverFactory

        resolver_factory = ResolverFactory()

        # Build query methods
        query_methods = {}

        for table_name, type_class in types.items():
            # List query (e.g., users() -> [User])
            list_name = self._to_camel_case(table_name)
            query_methods[list_name] = resolver_factory.create_list_resolver(
                table_name,
                type_class
            )

            # Get by ID query (e.g., user(id: Int) -> User)
            singular_name = self._singularize(list_name)
            query_methods[singular_name] = resolver_factory.create_get_resolver(
                table_name,
                type_class
            )

        # Create Query class
        @strawberry.type
        class Query:
            pass

        # Add methods to Query class
        for method_name, method in query_methods.items():
            setattr(Query, method_name, method)

        return Query

    def _create_mutation_type(
        self,
        strawberry,
        types: Dict[str, Type],
        table_info: Dict[str, List[Dict]]
    ) -> Type:
        """
        Create Mutation type with resolvers

        Args:
            strawberry: Strawberry module
            types: Generated GraphQL types
            table_info: Table metadata

        Returns:
            Mutation type class
        """
        from src.api.graphql.resolvers import ResolverFactory

        resolver_factory = ResolverFactory()

        # Build mutation methods
        mutation_methods = {}

        for table_name, type_class in types.items():
            singular = self._singularize(self._to_camel_case(table_name))

            # Create mutation
            mutation_methods[f'create{self._to_pascal_case(singular)}'] = \
                resolver_factory.create_insert_resolver(table_name, type_class)

            # Update mutation
            mutation_methods[f'update{self._to_pascal_case(singular)}'] = \
                resolver_factory.create_update_resolver(table_name, type_class)

            # Delete mutation
            mutation_methods[f'delete{self._to_pascal_case(singular)}'] = \
                resolver_factory.create_delete_resolver(table_name, type_class)

        # Create Mutation class
        @strawberry.type
        class Mutation:
            pass

        # Add methods to Mutation class
        for method_name, method in mutation_methods.items():
            setattr(Mutation, method_name, method)

        return Mutation

    def _map_sql_to_graphql_type(self, sql_type: str) -> str:
        """Map SQL type to GraphQL type"""
        sql_type_upper = sql_type.upper().split('(')[0]  # Remove size constraints
        return self.type_mappings.get(sql_type_upper, 'String')

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.capitalize() for word in snake_str.split('_'))

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])

    def _singularize(self, word: str) -> str:
        """Simple singularization (remove trailing 's')"""
        if word.endswith('ies'):
            return word[:-3] + 'y'
        elif word.endswith('ses') or word.endswith('shes') or word.endswith('ches'):
            return word[:-2]
        elif word.endswith('s') and not word.endswith('ss'):
            return word[:-1]
        return word
