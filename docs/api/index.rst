AI-Shell API Documentation
===========================

Welcome to AI-Shell's comprehensive API documentation. This documentation covers all modules, classes, and functions available in the AI-Shell framework.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   core
   agents
   mcp_clients
   coordination
   enterprise
   api_reference

Quick Start
-----------

.. code-block:: python

   from aishell import AIShell
   
   # Initialize AI-Shell
   shell = AIShell()
   
   # Connect to database
   shell.connect('postgresql://localhost/mydb')
   
   # Execute AI-powered query
   result = shell.query("show me users from last month")

Core Modules
------------

.. automodule:: aishell.core
   :members:
   :undoc-members:
   :show-inheritance:

AI Agents
---------

.. automodule:: aishell.agents
   :members:
   :undoc-members:
   :show-inheritance:

MCP Clients
-----------

.. automodule:: aishell.mcp_clients
   :members:
   :undoc-members:
   :show-inheritance:

Coordination System
-------------------

.. automodule:: aishell.coordination
   :members:
   :undoc-members:
   :show-inheritance:

Enterprise Features
-------------------

.. automodule:: aishell.enterprise
   :members:
   :undoc-members:
   :show-inheritance:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
