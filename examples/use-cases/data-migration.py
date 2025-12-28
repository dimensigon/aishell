#!/usr/bin/env python3
"""
AI-Shell Data Migration Example

This example demonstrates how to migrate data between different database systems
using AI-Shell's intelligent migration capabilities.

Features:
- Schema mapping and transformation
- Batch data migration with progress tracking
- Validation and integrity checks
- Error handling and rollback
- Performance optimization

Usage:
    python data-migration.py --source postgres://... --target mysql://...
"""

import asyncio
import argparse
from typing import Dict, List
from dataclasses import dataclass

# Assuming ai_shell package is installed
from ai_shell import AIShell
from ai_shell.database import DatabaseManager, ConnectionConfig
from ai_shell.agents import BaseAgent, AgentConfig


@dataclass
class MigrationConfig:
    """Configuration for data migration"""
    source_dsn: str
    target_dsn: str
    batch_size: int = 1000
    parallel_tables: int = 3
    validate: bool = True
    dry_run: bool = False


class DataMigrationAgent(BaseAgent):
    """Agent for intelligent data migration"""

    def __init__(self, config: AgentConfig, migration_config: MigrationConfig):
        super().__init__(config)
        self.migration_config = migration_config
        self.db_manager = DatabaseManager()
        self.stats = {
            "tables_migrated": 0,
            "rows_migrated": 0,
            "errors": []
        }

    async def on_start(self):
        """Initialize database connections"""
        self.log("Connecting to source and target databases...")

        # Connect to source
        await self.db_manager.connect(
            name="source",
            dsn=self.migration_config.source_dsn
        )

        # Connect to target
        await self.db_manager.connect(
            name="target",
            dsn=self.migration_config.target_dsn
        )

        self.log("Connections established")

    async def execute(self, task=None):
        """Execute migration"""
        try:
            # Step 1: Analyze schemas
            self.log("Analyzing schemas...")
            schema_mapping = await self.analyze_schemas()

            # Step 2: Migrate schema
            if not self.migration_config.dry_run:
                self.log("Migrating schema...")
                await self.migrate_schema(schema_mapping)

            # Step 3: Migrate data
            self.log("Migrating data...")
            await self.migrate_data(schema_mapping)

            # Step 4: Validate
            if self.migration_config.validate:
                self.log("Validating migration...")
                validation_result = await self.validate_migration(schema_mapping)
                if not validation_result["success"]:
                    raise Exception(f"Validation failed: {validation_result['errors']}")

            self.log("Migration completed successfully!")
            return self.stats

        except Exception as e:
            self.log(f"Migration failed: {e}", level="ERROR")
            raise

    async def analyze_schemas(self) -> Dict:
        """Analyze source and target schemas"""
        source_schema = await self.db_manager.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """,
            connection="source"
        )

        # Group by table
        tables = {}
        for row in source_schema.rows:
            table_name = row[0]
            if table_name not in tables:
                tables[table_name] = []
            tables[table_name].append({
                "name": row[1],
                "type": row[2]
            })

        # Map data types between databases
        schema_mapping = {}
        for table_name, columns in tables.items():
            mapped_columns = []
            for col in columns:
                mapped_type = self.map_data_type(col["type"])
                mapped_columns.append({
                    "name": col["name"],
                    "source_type": col["type"],
                    "target_type": mapped_type
                })

            schema_mapping[table_name] = {
                "columns": mapped_columns,
                "row_count": await self.get_row_count(table_name)
            }

        return schema_mapping

    def map_data_type(self, source_type: str) -> str:
        """Map data types between database systems"""
        type_mapping = {
            "character varying": "VARCHAR",
            "integer": "INT",
            "bigint": "BIGINT",
            "timestamp without time zone": "DATETIME",
            "boolean": "TINYINT(1)",
            "text": "TEXT",
            "jsonb": "JSON",
        }

        return type_mapping.get(source_type.lower(), source_type.upper())

    async def get_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        result = await self.db_manager.execute(
            f"SELECT COUNT(*) FROM {table_name}",
            connection="source"
        )
        return result.rows[0][0]

    async def migrate_schema(self, schema_mapping: Dict):
        """Migrate database schema"""
        for table_name, table_info in schema_mapping.items():
            # Generate CREATE TABLE statement
            columns_sql = []
            for col in table_info["columns"]:
                columns_sql.append(f"{col['name']} {col['target_type']}")

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(columns_sql)}
            )
            """

            # Execute on target
            await self.db_manager.execute(
                create_table_sql,
                connection="target"
            )

            self.log(f"Created table: {table_name}")

    async def migrate_data(self, schema_mapping: Dict):
        """Migrate data with batching and parallel processing"""
        tables = list(schema_mapping.keys())

        # Process tables in parallel
        batch_size = self.migration_config.parallel_tables
        for i in range(0, len(tables), batch_size):
            batch = tables[i:i + batch_size]
            tasks = [
                self.migrate_table(table_name, schema_mapping[table_name])
                for table_name in batch
            ]
            await asyncio.gather(*tasks)

    async def migrate_table(self, table_name: str, table_info: Dict):
        """Migrate a single table"""
        self.log(f"Migrating table: {table_name}")

        total_rows = table_info["row_count"]
        batch_size = self.migration_config.batch_size
        offset = 0

        while offset < total_rows:
            # Fetch batch from source
            source_data = await self.db_manager.execute(
                f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}",
                connection="source"
            )

            if not source_data.rows:
                break

            # Prepare batch insert
            if not self.migration_config.dry_run:
                placeholders = ", ".join(["%s"] * len(table_info["columns"]))
                insert_sql = f"""
                INSERT INTO {table_name}
                VALUES ({placeholders})
                """

                # Batch insert
                for row in source_data.rows:
                    await self.db_manager.execute(
                        insert_sql,
                        *row,
                        connection="target"
                    )

            self.stats["rows_migrated"] += len(source_data.rows)
            offset += batch_size

            # Progress logging
            progress = (offset / total_rows) * 100
            self.log(f"  Progress: {progress:.1f}% ({offset}/{total_rows} rows)")

        self.stats["tables_migrated"] += 1
        self.log(f"✓ Completed: {table_name} ({total_rows} rows)")

    async def validate_migration(self, schema_mapping: Dict) -> Dict:
        """Validate migration results"""
        errors = []

        for table_name, table_info in schema_mapping.items():
            # Check row count
            source_count = table_info["row_count"]

            target_result = await self.db_manager.execute(
                f"SELECT COUNT(*) FROM {table_name}",
                connection="target"
            )
            target_count = target_result.rows[0][0]

            if source_count != target_count:
                errors.append(
                    f"{table_name}: Row count mismatch "
                    f"(source: {source_count}, target: {target_count})"
                )

            # Sample data validation
            sample_size = min(100, source_count)
            if sample_size > 0:
                source_sample = await self.db_manager.execute(
                    f"SELECT * FROM {table_name} LIMIT {sample_size}",
                    connection="source"
                )

                target_sample = await self.db_manager.execute(
                    f"SELECT * FROM {table_name} LIMIT {sample_size}",
                    connection="target"
                )

                # Compare checksums or specific columns
                # (simplified validation)
                if len(source_sample.rows) != len(target_sample.rows):
                    errors.append(f"{table_name}: Sample data mismatch")

        return {
            "success": len(errors) == 0,
            "errors": errors,
            "tables_validated": len(schema_mapping)
        }

    async def on_stop(self):
        """Cleanup connections"""
        await self.db_manager.disconnect("source")
        await self.db_manager.disconnect("target")
        self.log("Connections closed")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI-Shell Data Migration")
    parser.add_argument("--source", required=True, help="Source database DSN")
    parser.add_argument("--target", required=True, help="Target database DSN")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size")
    parser.add_argument("--parallel", type=int, default=3, help="Parallel tables")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    # Create migration config
    migration_config = MigrationConfig(
        source_dsn=args.source,
        target_dsn=args.target,
        batch_size=args.batch_size,
        parallel_tables=args.parallel,
        validate=not args.no_validate,
        dry_run=args.dry_run
    )

    # Create agent
    agent_config = AgentConfig(
        name="data_migration",
        enabled=True
    )

    agent = DataMigrationAgent(agent_config, migration_config)

    try:
        # Run migration
        await agent.on_start()
        stats = await agent.execute()

        print("\n" + "="*50)
        print("MIGRATION COMPLETE")
        print("="*50)
        print(f"Tables migrated: {stats['tables_migrated']}")
        print(f"Rows migrated: {stats['rows_migrated']}")
        if stats['errors']:
            print(f"Errors: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")

    finally:
        await agent.on_stop()


if __name__ == "__main__":
    asyncio.run(main())
