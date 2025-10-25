Database API Reference
======================

The Database API provides comprehensive database connectivity, query execution, and management capabilities.

Module Overview
---------------

.. automodule:: ai_shell.database
   :members:
   :undoc-members:
   :show-inheritance:

Database Manager
----------------

.. autoclass:: ai_shell.database.DatabaseManager
   :members:
   :undoc-members:
   :show-inheritance:

   Central manager for database connections and operations.

   .. rubric:: Methods

   .. automethod:: connect
   .. automethod:: disconnect
   .. automethod:: execute
   .. automethod:: query
   .. automethod:: transaction
   .. automethod:: get_connection
   .. automethod:: list_connections

   **Example:**

   .. code-block:: python

      from ai_shell.database import DatabaseManager

      manager = DatabaseManager()

      # Connect to multiple databases
      prod_conn = manager.connect(
          name="production",
          type="postgresql",
          host="prod.db.com",
          database="prod_db",
          username="admin",
          password="secret"
      )

      analytics_conn = manager.connect(
          name="analytics",
          type="mongodb",
          host="mongo.db.com",
          database="analytics"
      )

      # Use connections
      result = manager.execute(
          "SELECT * FROM users",
          connection="production"
      )

Connection Classes
------------------

BaseConnection
~~~~~~~~~~~~~~

.. autoclass:: ai_shell.database.connection.BaseConnection
   :members:
   :undoc-members:
   :show-inheritance:

   Abstract base class for all database connections.

   .. automethod:: connect
   .. automethod:: disconnect
   .. automethod:: execute
   .. automethod:: is_connected
   .. automethod:: ping

PostgreSQLConnection
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.database.connection.PostgreSQLConnection
   :members:
   :undoc-members:
   :show-inheritance:

   PostgreSQL database connection implementation.

   **Example:**

   .. code-block:: python

      from ai_shell.database.connection import PostgreSQLConnection

      conn = PostgreSQLConnection(
          host="localhost",
          port=5432,
          database="mydb",
          username="user",
          password="pass",
          ssl_mode="require"
      )

      await conn.connect()

      # Execute query
      result = await conn.execute("SELECT version()")
      print(result.rows[0][0])

      # Use connection pool
      async with conn.pool.acquire() as connection:
          result = await connection.fetch("SELECT * FROM users")

      await conn.disconnect()

MySQLConnection
~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.database.connection.MySQLConnection
   :members:
   :undoc-members:
   :show-inheritance:

   MySQL database connection implementation.

SQLiteConnection
~~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.database.connection.SQLiteConnection
   :members:
   :undoc-members:
   :show-inheritance:

   SQLite database connection implementation.

MongoDBConnection
~~~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.database.connection.MongoDBConnection
   :members:
   :undoc-members:
   :show-inheritance:

   MongoDB connection implementation.

   **Example:**

   .. code-block:: python

      from ai_shell.database.connection import MongoDBConnection

      conn = MongoDBConnection(
          host="localhost",
          port=27017,
          database="analytics"
      )

      await conn.connect()

      # MongoDB operations
      collection = conn.get_collection("users")
      users = await collection.find({"status": "active"}).to_list(100)

      # Aggregation
      pipeline = [
          {"$match": {"status": "active"}},
          {"$group": {"_id": "$country", "count": {"$sum": 1}}}
      ]
      results = await collection.aggregate(pipeline).to_list(None)

RedisConnection
~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.database.connection.RedisConnection
   :members:
   :undoc-members:
   :show-inheritance:

   Redis connection implementation.

Query Builder
-------------

.. autoclass:: ai_shell.database.query.QueryBuilder
   :members:
   :undoc-members:
   :show-inheritance:

   Fluent interface for building SQL queries.

   **Example:**

   .. code-block:: python

      from ai_shell.database import QueryBuilder

      # Build SELECT query
      query = (QueryBuilder()
          .select("id", "username", "email")
          .from_table("users")
          .where("status", "=", "active")
          .where("created_at", ">", "2024-01-01")
          .order_by("created_at", "DESC")
          .limit(10)
          .build())

      print(query.sql)
      # SELECT id, username, email FROM users
      # WHERE status = ? AND created_at > ?
      # ORDER BY created_at DESC LIMIT 10

      print(query.params)
      # ['active', '2024-01-01']

      # Build INSERT query
      insert = (QueryBuilder()
          .insert_into("users")
          .values({
              "username": "alice",
              "email": "alice@example.com",
              "status": "active"
          })
          .build())

      # Build UPDATE query
      update = (QueryBuilder()
          .update("users")
          .set({"status": "inactive"})
          .where("id", "=", 123)
          .build())

Query Analyzer
--------------

.. autoclass:: ai_shell.database.analyzer.QueryAnalyzer
   :members:
   :undoc-members:
   :show-inheritance:

   Analyzes and optimizes database queries.

   .. automethod:: analyze
   .. automethod:: explain
   .. automethod:: suggest_optimizations
   .. automethod:: identify_issues

   **Example:**

   .. code-block:: python

      from ai_shell.database import QueryAnalyzer

      analyzer = QueryAnalyzer(connection)

      query = "SELECT * FROM orders WHERE created_at > '2024-01-01'"

      # Get execution plan
      plan = await analyzer.explain(query)
      print(plan.tree)

      # Analyze performance
      analysis = await analyzer.analyze(query)
      print(f"Execution time: {analysis.duration}ms")
      print(f"Rows scanned: {analysis.rows_scanned}")
      print(f"Estimated cost: {analysis.cost}")

      # Get optimization suggestions
      suggestions = await analyzer.suggest_optimizations(query)
      for suggestion in suggestions:
          print(f"[{suggestion.priority}] {suggestion.description}")
          print(f"  SQL: {suggestion.sql}")
          print(f"  Impact: {suggestion.estimated_improvement}%")

Schema Manager
--------------

.. autoclass:: ai_shell.database.schema.SchemaManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages database schema operations.

   .. automethod:: get_tables
   .. automethod:: get_columns
   .. automethod:: get_indexes
   .. automethod:: get_foreign_keys
   .. automethod:: create_table
   .. automethod:: alter_table
   .. automethod:: drop_table

   **Example:**

   .. code-block:: python

      from ai_shell.database import SchemaManager
      from ai_shell.database.schema import Table, Column, Index

      schema = SchemaManager(connection)

      # Get schema information
      tables = await schema.get_tables()
      for table in tables:
          print(f"Table: {table.name}")
          columns = await schema.get_columns(table.name)
          for col in columns:
              print(f"  {col.name}: {col.type}")

      # Create table
      users_table = Table(
          name="users",
          columns=[
              Column("id", "BIGSERIAL", primary_key=True),
              Column("username", "VARCHAR(255)", nullable=False, unique=True),
              Column("email", "VARCHAR(255)", nullable=False),
              Column("created_at", "TIMESTAMP", default="NOW()"),
          ],
          indexes=[
              Index("idx_users_email", ["email"]),
              Index("idx_users_created", ["created_at"]),
          ]
      )

      await schema.create_table(users_table)

Migration Manager
-----------------

.. autoclass:: ai_shell.database.migration.MigrationManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages database migrations.

   .. automethod:: create_migration
   .. automethod:: apply_migrations
   .. automethod:: rollback_migration
   .. automethod:: get_migration_status

   **Example:**

   .. code-block:: python

      from ai_shell.database import MigrationManager

      manager = MigrationManager(connection, migrations_dir="./migrations")

      # Create new migration
      migration = manager.create_migration("add_users_table")

      # migrations/20250110_001_add_users_table.py will be created

      # Apply pending migrations
      applied = await manager.apply_migrations()
      print(f"Applied {len(applied)} migrations")

      # Check status
      status = await manager.get_migration_status()
      for mig in status:
          print(f"{mig.name}: {mig.status}")

      # Rollback last migration
      await manager.rollback_migration()

Connection Pool
---------------

.. autoclass:: ai_shell.database.pool.ConnectionPool
   :members:
   :undoc-members:
   :show-inheritance:

   Manages a pool of database connections.

   .. automethod:: acquire
   .. automethod:: release
   .. automethod:: close
   .. automethod:: get_stats

   **Example:**

   .. code-block:: python

      from ai_shell.database.pool import ConnectionPool

      pool = ConnectionPool(
          connection_factory=PostgreSQLConnection,
          min_size=5,
          max_size=20,
          timeout=30
      )

      await pool.initialize()

      # Use connection from pool
      async with pool.acquire() as conn:
          result = await conn.execute("SELECT * FROM users")

      # Get pool statistics
      stats = pool.get_stats()
      print(f"Active: {stats.active_connections}")
      print(f"Idle: {stats.idle_connections}")
      print(f"Total queries: {stats.total_queries}")

      await pool.close()

Transaction Manager
-------------------

.. autoclass:: ai_shell.database.transaction.TransactionManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages database transactions.

   **Example:**

   .. code-block:: python

      from ai_shell.database import TransactionManager

      tm = TransactionManager(connection)

      # Simple transaction
      async with tm.transaction():
          await connection.execute("INSERT INTO users ...")
          await connection.execute("UPDATE accounts ...")
          # Auto-commits on success, rolls back on exception

      # Savepoints
      async with tm.transaction() as txn:
          await connection.execute("INSERT INTO users ...")

          savepoint = await txn.savepoint()
          try:
              await connection.execute("RISKY OPERATION")
          except Exception:
              await txn.rollback_to(savepoint)

          await connection.execute("SAFE OPERATION")

Backup Manager
--------------

.. autoclass:: ai_shell.database.backup.BackupManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages database backups and restores.

   .. automethod:: create_backup
   .. automethod:: restore_backup
   .. automethod:: list_backups
   .. automethod:: delete_backup

   **Example:**

   .. code-block:: python

      from ai_shell.database import BackupManager

      backup_mgr = BackupManager(
          connection,
          backup_dir="/backups",
          compression=True
      )

      # Create backup
      backup = await backup_mgr.create_backup(
          name="daily_backup",
          full=True
      )
      print(f"Backup created: {backup.path}")
      print(f"Size: {backup.size_mb} MB")

      # List backups
      backups = await backup_mgr.list_backups()
      for b in backups:
          print(f"{b.name}: {b.created_at} ({b.size_mb} MB)")

      # Restore backup
      await backup_mgr.restore_backup(backup.name)

Data Types
----------

.. autoclass:: ai_shell.database.types.DatabaseType
.. autoclass:: ai_shell.database.types.ConnectionConfig
.. autoclass:: ai_shell.database.types.QueryResult
.. autoclass:: ai_shell.database.types.ExecutionPlan

Utilities
---------

.. autofunction:: ai_shell.database.utils.parse_dsn
.. autofunction:: ai_shell.database.utils.escape_identifier
.. autofunction:: ai_shell.database.utils.format_sql
.. autofunction:: ai_shell.database.utils.validate_connection

Examples
--------

Multi-Database Operations
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ai_shell.database import DatabaseManager

   manager = DatabaseManager()

   # Connect to multiple databases
   await manager.connect("prod_pg", type="postgresql", ...)
   await manager.connect("prod_mongo", type="mongodb", ...)
   await manager.connect("cache", type="redis", ...)

   # Query across databases
   pg_users = await manager.query("SELECT * FROM users", connection="prod_pg")
   mongo_events = await manager.query(
       {"user_id": {"$in": [u["id"] for u in pg_users]}},
       connection="prod_mongo"
   )

   # Cache results
   await manager.execute(
       "SET user:123 '{...}'",
       connection="cache"
   )

See Also
--------

* :doc:`core-api` - Core functionality
* :doc:`agents-api` - Database automation agents
* :doc:`enterprise-api` - High availability and clustering
