Agents API Reference
====================

The Agents API provides a powerful framework for building automated database tasks and workflows.

Module Overview
---------------

.. automodule:: ai_shell.agents
   :members:
   :undoc-members:
   :show-inheritance:

Agent Base Classes
------------------

BaseAgent
~~~~~~~~~

.. autoclass:: ai_shell.agents.BaseAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Abstract base class for all agents.

   .. rubric:: Lifecycle Methods

   .. automethod:: __init__
   .. automethod:: on_start
   .. automethod:: execute
   .. automethod:: on_stop
   .. automethod:: on_error

   .. rubric:: Utility Methods

   .. automethod:: log
   .. automethod:: send_alert
   .. automethod:: store_metrics

   **Example:**

   .. code-block:: python

      from ai_shell.agents import BaseAgent, AgentConfig

      class MyAgent(BaseAgent):
          """Custom agent implementation"""

          def __init__(self, config: AgentConfig):
              super().__init__(config)
              self.counter = 0

          async def on_start(self):
              """Called when agent starts"""
              self.log("Agent starting...")
              await self.initialize_resources()

          async def execute(self, task):
              """Main execution logic"""
              self.log(f"Processing task: {task}")
              result = await self.process_task(task)
              self.counter += 1
              return result

          async def on_stop(self):
              """Called when agent stops"""
              self.log(f"Agent stopping. Processed {self.counter} tasks")
              await self.cleanup_resources()

          async def on_error(self, error):
              """Called on error"""
              self.log(f"Error occurred: {error}", level="ERROR")
              await self.send_alert(
                  severity="high",
                  message=str(error)
              )

StatefulAgent
~~~~~~~~~~~~~

.. autoclass:: ai_shell.agents.StatefulAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Agent with persistent state management.

   .. automethod:: load_state
   .. automethod:: save_state
   .. automethod:: clear_state

   **Example:**

   .. code-block:: python

      from ai_shell.agents import StatefulAgent

      class MonitorAgent(StatefulAgent):
          """Monitoring agent with state"""

          async def execute(self):
              # Load previous state
              last_metrics = await self.load_state("metrics")

              # Collect current metrics
              current_metrics = await self.collect_metrics()

              # Compare
              if self.has_anomaly(last_metrics, current_metrics):
                  await self.send_alert("Anomaly detected!")

              # Save state
              await self.save_state("metrics", current_metrics)

AIAgent
~~~~~~~

.. autoclass:: ai_shell.agents.AIAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Agent with AI capabilities for intelligent decision-making.

   .. automethod:: ai_complete
   .. automethod:: ai_decide
   .. automethod:: ai_analyze

   **Example:**

   .. code-block:: python

      from ai_shell.agents import AIAgent

      class IntelligentOptimizer(AIAgent):
          """AI-powered database optimizer"""

          async def optimize_database(self):
              # Gather context
              context = await self.gather_context()

              # Use AI to decide
              decision = await self.ai_decide(
                  prompt=f"Analyze and optimize: {context}",
                  schema={
                      "type": "object",
                      "properties": {
                          "actions": {"type": "array"},
                          "reasoning": {"type": "string"}
                      }
                  }
              )

              # Execute AI recommendations
              for action in decision["actions"]:
                  await self.execute_action(action)

Agent Manager
-------------

.. autoclass:: ai_shell.agents.AgentManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages agent lifecycle and orchestration.

   .. automethod:: register_agent
   .. automethod:: start_agent
   .. automethod:: stop_agent
   .. automethod:: get_agent_status
   .. automethod:: list_agents

   **Example:**

   .. code-block:: python

      from ai_shell.agents import AgentManager, AgentConfig

      manager = AgentManager()

      # Register agent
      config = AgentConfig(
          name="query_optimizer",
          agent_class="QueryOptimizerAgent",
          config={"threshold_ms": 1000},
          enabled=True
      )

      agent_id = await manager.register_agent(config)

      # Start agent
      await manager.start_agent(agent_id)

      # Check status
      status = await manager.get_agent_status(agent_id)
      print(f"Agent status: {status.state}")
      print(f"Tasks processed: {status.tasks_processed}")

      # List all agents
      agents = await manager.list_agents()
      for agent in agents:
          print(f"{agent.name}: {agent.state}")

Agent Coordinator
-----------------

.. autoclass:: ai_shell.agents.AgentCoordinator
   :members:
   :undoc-members:
   :show-inheritance:

   Coordinates multiple agents for complex workflows.

   .. automethod:: spawn_agent
   .. automethod:: execute_parallel
   .. automethod:: execute_sequence
   .. automethod:: wait_for_completion

   **Example:**

   .. code-block:: python

      from ai_shell.agents import AgentCoordinator

      class MigrationCoordinator(AgentCoordinator):
          """Coordinates database migration"""

          async def execute_migration(self, source, target):
              # Spawn specialized agents
              schema_agent = await self.spawn_agent("schema_migrator")
              data_agent = await self.spawn_agent("data_migrator")
              validator = await self.spawn_agent("validator")

              # Execute in sequence
              schema_result = await schema_agent.migrate(source, target)

              if schema_result.success:
                  # Parallel data migration
                  tables = schema_result.tables
                  tasks = [
                      data_agent.migrate_table(table, source, target)
                      for table in tables
                  ]
                  results = await self.execute_parallel(tasks, max_workers=5)

                  # Validate
                  validation = await validator.validate(source, target, results)

                  return validation

Triggers and Scheduling
-----------------------

Decorators
~~~~~~~~~~

.. autodecorator:: ai_shell.agents.trigger

   Decorator for defining agent triggers.

   **Examples:**

   .. code-block:: python

      from ai_shell.agents import BaseAgent, trigger

      class EventDrivenAgent(BaseAgent):

          @trigger(event="query_completed")
          async def on_query_completed(self, event):
              """Triggered when query completes"""
              if event["duration_ms"] > 1000:
                  await self.analyze_slow_query(event)

          @trigger(schedule="*/5 * * * *")  # Every 5 minutes
          async def periodic_check(self):
              """Runs every 5 minutes"""
              await self.perform_health_check()

          @trigger(event="high_cpu", condition="cpu > 80")
          async def on_high_cpu(self, event):
              """Triggered when CPU exceeds 80%"""
              await self.optimize_resources()

          @trigger(schedule="0 2 * * *")  # Daily at 2 AM
          async def daily_maintenance(self):
              """Daily maintenance tasks"""
              await self.vacuum_tables()
              await self.update_statistics()

Scheduler
~~~~~~~~~

.. autoclass:: ai_shell.agents.scheduler.Scheduler
   :members:
   :undoc-members:
   :show-inheritance:

   Manages scheduled agent tasks.

Built-in Agents
---------------

QueryOptimizerAgent
~~~~~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.agents.builtin.QueryOptimizerAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Monitors and optimizes slow queries.

   **Configuration:**

   .. code-block:: yaml

      name: query_optimizer
      config:
        threshold_ms: 1000
        auto_apply: false
        notification_channels: [email, slack]

DatabaseHealthAgent
~~~~~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.agents.builtin.DatabaseHealthAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Monitors database health and performance.

BackupAgent
~~~~~~~~~~~

.. autoclass:: ai_shell.agents.builtin.BackupAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Automates database backups.

SchemaValidatorAgent
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ai_shell.agents.builtin.SchemaValidatorAgent
   :members:
   :undoc-members:
   :show-inheritance:

   Validates schema changes and migrations.

Configuration
-------------

AgentConfig
~~~~~~~~~~~

.. autoclass:: ai_shell.agents.config.AgentConfig
   :members:
   :undoc-members:

   Configuration for agent initialization.

   **Example:**

   .. code-block:: python

      from ai_shell.agents import AgentConfig

      config = AgentConfig(
          name="my_agent",
          agent_class="MyAgent",
          enabled=True,
          config={
              "threshold": 100,
              "auto_fix": True
          },
          resources={
              "max_memory_mb": 512,
              "max_cpu_percent": 50
          },
          triggers=[
              {"type": "schedule", "schedule": "*/5 * * * *"},
              {"type": "event", "event": "slow_query"}
          ]
      )

Agent Communication
-------------------

Message Bus
~~~~~~~~~~~

.. autoclass:: ai_shell.agents.messaging.MessageBus
   :members:
   :undoc-members:
   :show-inheritance:

   Enables inter-agent communication.

   **Example:**

   .. code-block:: python

      from ai_shell.agents.messaging import MessageBus

      bus = MessageBus()

      # Agent A publishes
      await bus.publish("optimization_complete", {
          "table": "users",
          "improvement": "45%"
      })

      # Agent B subscribes
      async def handle_optimization(message):
          print(f"Optimization: {message.data}")

      await bus.subscribe("optimization_complete", handle_optimization)

Monitoring and Metrics
----------------------

AgentMetrics
~~~~~~~~~~~~

.. autoclass:: ai_shell.agents.metrics.AgentMetrics
   :members:
   :undoc-members:
   :show-inheritance:

   Tracks agent performance metrics.

   **Example:**

   .. code-block:: python

      from ai_shell.agents import BaseAgent

      class MonitoredAgent(BaseAgent):
          async def execute(self, task):
              with self.metrics.timer("task_execution"):
                  result = await self.process_task(task)

              self.metrics.increment("tasks_processed")
              self.metrics.gauge("queue_size", self.queue.size())

              return result

      # Get metrics
      metrics = agent.metrics.get_all()
      print(f"Tasks processed: {metrics['tasks_processed']}")
      print(f"Avg execution time: {metrics['task_execution_avg']}ms")

Error Handling
--------------

.. autoclass:: ai_shell.agents.errors.AgentError
   :show-inheritance:

.. autoclass:: ai_shell.agents.errors.AgentTimeoutError
   :show-inheritance:

.. autoclass:: ai_shell.agents.errors.AgentConfigurationError
   :show-inheritance:

Testing
-------

AgentTestCase
~~~~~~~~~~~~~

.. autoclass:: ai_shell.agents.testing.AgentTestCase
   :members:
   :undoc-members:
   :show-inheritance:

   Base class for agent unit tests.

   **Example:**

   .. code-block:: python

      import pytest
      from ai_shell.agents.testing import AgentTestCase
      from myagents import QueryOptimizerAgent

      class TestQueryOptimizer(AgentTestCase):
          async def setup_method(self):
              self.agent = await self.create_agent(
                  QueryOptimizerAgent,
                  config={"threshold_ms": 1000}
              )

          @pytest.mark.asyncio
          async def test_slow_query_detection(self):
              event = {
                  "sql": "SELECT * FROM users",
                  "duration_ms": 2000
              }

              await self.agent.on_query_completed(event)

              # Verify analysis was performed
              analyses = await self.agent.get_recent_analyses()
              assert len(analyses) == 1
              assert analyses[0]["duration"] == 2000

Examples
--------

Complete Agent Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ai_shell.agents import BaseAgent, AgentConfig, trigger
   from ai_shell.database import DatabaseManager

   class AutoScalingAgent(BaseAgent):
       """Automatically scales database resources"""

       def __init__(self, config: AgentConfig):
           super().__init__(config)
           self.db = DatabaseManager()
           self.scale_threshold = config.get("scale_threshold", 80)

       async def on_start(self):
           await self.db.connect()
           self.log("Auto-scaling agent started")

       @trigger(schedule="*/1 * * * *")  # Every minute
       async def check_resources(self):
           metrics = await self.db.get_resource_metrics()

           cpu_usage = metrics["cpu_percent"]
           memory_usage = metrics["memory_percent"]

           if cpu_usage > self.scale_threshold:
               await self.scale_up("cpu_high")
           elif memory_usage > self.scale_threshold:
               await self.scale_up("memory_high")
           elif cpu_usage < 30 and memory_usage < 30:
               await self.scale_down("underutilized")

       async def scale_up(self, reason):
           self.log(f"Scaling up: {reason}")
           await self.db.increase_resources()
           await self.send_alert(
               severity="info",
               message=f"Scaled up database: {reason}"
           )

       async def scale_down(self, reason):
           self.log(f"Scaling down: {reason}")
           await self.db.decrease_resources()

       async def on_stop(self):
           await self.db.disconnect()
           self.log("Auto-scaling agent stopped")

Multi-Agent Workflow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ai_shell.agents import AgentCoordinator

   class ETLCoordinator(AgentCoordinator):
       """Coordinates Extract-Transform-Load workflow"""

       async def execute_etl(self, source, target):
           # Spawn agents
           extractor = await self.spawn_agent("data_extractor")
           transformer = await self.spawn_agent("data_transformer")
           loader = await self.spawn_agent("data_loader")
           validator = await self.spawn_agent("data_validator")

           # Extract
           extracted_data = await extractor.extract(source)

           # Transform (parallel processing)
           batches = self.create_batches(extracted_data, size=1000)
           transform_tasks = [
               transformer.transform(batch)
               for batch in batches
           ]
           transformed_data = await self.execute_parallel(
               transform_tasks,
               max_workers=10
           )

           # Load
           load_result = await loader.load(transformed_data, target)

           # Validate
           validation = await validator.validate(source, target)

           return {
               "extracted": len(extracted_data),
               "transformed": len(transformed_data),
               "loaded": load_result.row_count,
               "validation": validation.status
           }

See Also
--------

* :doc:`core-api` - Core functionality
* :doc:`database-api` - Database operations
* :doc:`ai-api` - AI integration
* :doc:`monitoring-api` - Monitoring and observability
