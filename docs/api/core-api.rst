Core API Reference
==================

The Core API provides the fundamental building blocks for AI-Shell functionality.

Module Overview
---------------

.. automodule:: ai_shell.core
   :members:
   :undoc-members:
   :show-inheritance:

AIShell Class
-------------

The main entry point for AI-Shell functionality.

.. autoclass:: ai_shell.core.AIShell
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: __init__
   .. automethod:: connect
   .. automethod:: query
   .. automethod:: execute
   .. automethod:: disconnect
   .. automethod:: health_check

   **Example Usage:**

   .. code-block:: python

      from ai_shell import AIShell

      # Initialize with default configuration
      shell = AIShell()

      # Initialize with custom config
      shell = AIShell(config_path="/path/to/config.yaml")

      # Check health
      health = shell.health_check()
      print(f"Status: {health['status']}")

Session Management
------------------

.. autoclass:: ai_shell.core.Session
   :members:
   :undoc-members:
   :show-inheritance:

   Manages user sessions and state.

   .. rubric:: Attributes

   .. autoattribute:: user
   .. autoattribute:: created_at
   .. autoattribute:: last_activity
   .. autoattribute:: context

   .. rubric:: Methods

   .. automethod:: start
   .. automethod:: end
   .. automethod:: update_activity
   .. automethod:: set_context
   .. automethod:: get_context

Context Manager
---------------

.. autoclass:: ai_shell.core.Context
   :members:
   :undoc-members:
   :show-inheritance:

   Provides context for operations and maintains state.

   **Example:**

   .. code-block:: python

      from ai_shell.core import Context

      with Context(database="production") as ctx:
          ctx.set("table", "users")
          result = shell.query("select * from users", context=ctx)

Base Classes
------------

BaseCommand
~~~~~~~~~~~

.. autoclass:: ai_shell.core.base.BaseCommand
   :members:
   :undoc-members:
   :show-inheritance:

   Abstract base class for all commands.

   .. automethod:: execute
   .. automethod:: validate
   .. automethod:: rollback

BaseExecutor
~~~~~~~~~~~~

.. autoclass:: ai_shell.core.base.BaseExecutor
   :members:
   :undoc-members:
   :show-inheritance:

   Abstract base class for command executors.

Result Classes
--------------

QueryResult
~~~~~~~~~~~

.. autoclass:: ai_shell.core.result.QueryResult
   :members:
   :undoc-members:
   :show-inheritance:

   Represents the result of a query execution.

   .. rubric:: Attributes

   .. autoattribute:: rows
   .. autoattribute:: columns
   .. autoattribute:: row_count
   .. autoattribute:: execution_time
   .. autoattribute:: metadata

   .. rubric:: Methods

   .. automethod:: to_dict
   .. automethod:: to_dataframe
   .. automethod:: to_csv
   .. automethod:: to_json

   **Example:**

   .. code-block:: python

      result = shell.query("SELECT * FROM users LIMIT 10")

      # Access rows
      for row in result.rows:
          print(row)

      # Convert to DataFrame
      df = result.to_dataframe()

      # Export to CSV
      result.to_csv("users.csv")

ExecutionResult
~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.core.result.ExecutionResult
   :members:
   :undoc-members:
   :show-inheritance:

   Generic result container for command executions.

Error Classes
-------------

AIShellError
~~~~~~~~~~~~

.. autoexception:: ai_shell.core.errors.AIShellError
   :members:
   :show-inheritance:

   Base exception class for all AI-Shell errors.

DatabaseError
~~~~~~~~~~~~~

.. autoexception:: ai_shell.core.errors.DatabaseError
   :members:
   :show-inheritance:

   Raised for database-related errors.

ConnectionError
~~~~~~~~~~~~~~~

.. autoexception:: ai_shell.core.errors.ConnectionError
   :members:
   :show-inheritance:

   Raised when database connection fails.

QueryError
~~~~~~~~~~

.. autoexception:: ai_shell.core.errors.QueryError
   :members:
   :show-inheritance:

   Raised when query execution fails.

ConfigurationError
~~~~~~~~~~~~~~~~~~

.. autoexception:: ai_shell.core.errors.ConfigurationError
   :members:
   :show-inheritance:

   Raised for configuration-related errors.

Utility Functions
-----------------

.. autofunction:: ai_shell.core.utils.parse_connection_string
.. autofunction:: ai_shell.core.utils.validate_query
.. autofunction:: ai_shell.core.utils.format_result
.. autofunction:: ai_shell.core.utils.sanitize_input

Constants
---------

.. autodata:: ai_shell.core.constants.DEFAULT_TIMEOUT
.. autodata:: ai_shell.core.constants.MAX_RETRIES
.. autodata:: ai_shell.core.constants.SUPPORTED_DATABASES
.. autodata:: ai_shell.core.constants.VERSION

Type Definitions
----------------

.. autoclass:: ai_shell.core.types.DatabaseType
   :members:
   :undoc-members:

.. autoclass:: ai_shell.core.types.ConnectionOptions
   :members:
   :undoc-members:

.. autoclass:: ai_shell.core.types.QueryOptions
   :members:
   :undoc-members:

Examples
--------

Basic Query Execution
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ai_shell import AIShell

   shell = AIShell()
   shell.connect("postgresql://localhost/mydb")

   # Execute SQL directly
   result = shell.execute("SELECT COUNT(*) FROM users")
   print(f"Total users: {result.rows[0][0]}")

   # Natural language query
   result = shell.query("how many users signed up today?")
   print(result.to_json())

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from ai_shell import AIShell
   from ai_shell.core.errors import DatabaseError, QueryError

   shell = AIShell()

   try:
       shell.connect("postgresql://localhost/mydb")
       result = shell.query("invalid query")
   except ConnectionError as e:
       print(f"Failed to connect: {e}")
   except QueryError as e:
       print(f"Query failed: {e}")
   except DatabaseError as e:
       print(f"Database error: {e}")
   finally:
       shell.disconnect()

Context Management
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ai_shell import AIShell
   from ai_shell.core import Context

   shell = AIShell()

   # Using context for multi-database operations
   prod_context = Context(database="production", readonly=True)
   dev_context = Context(database="development", readonly=False)

   # Read from production
   with prod_context:
       users = shell.query("select * from users")

   # Write to development
   with dev_context:
       shell.execute(f"INSERT INTO users VALUES {users.rows[0]}")

See Also
--------

* :doc:`database-api` - Database connection and operations
* :doc:`agents-api` - Agent framework
* :doc:`cli-api` - Command-line interface

.. note::
   All examples assume proper configuration and authentication are in place.
   See :doc:`config-api` for configuration details.
