# AgentManager Usage Guide

## Overview

The AgentManager provides comprehensive agent lifecycle management, task delegation, inter-agent communication, and result aggregation for AI-Shell's assistant mode.

## Features

- **Agent Lifecycle Management**: Create, start, stop, and destroy agents
- **Agent Registry**: Discover and query agents by type, capability, or status
- **Task Delegation**: Automatically route tasks to appropriate agents
- **Inter-Agent Communication**: Message passing and broadcast capabilities
- **Result Aggregation**: Combine results from multiple agents
- **Context Sharing**: Share data between agents
- **Performance Monitoring**: Track agent and task metrics

## Quick Start

### Basic Setup

```python
from src.agents.manager import AgentManager, AgentType
from src.agents.base import AgentCapability, TaskContext
from src.llm.manager import LocalLLMManager
from src.performance.monitor import PerformanceMonitor

# Initialize dependencies
llm_manager = LocalLLMManager()
llm_manager.initialize()

performance_monitor = PerformanceMonitor()

# Create agent manager
agent_manager = AgentManager(
    llm_manager=llm_manager,
    performance_monitor=performance_monitor,
    max_concurrent_tasks=10
)

# Start the manager
await agent_manager.start()
```

### Creating Agents

```python
# Create a command agent
command_agent_id = await agent_manager.create_agent(
    agent_type=AgentType.COMMAND,
    capabilities=[AgentCapability.FILE_READ],
    config={"allowed_commands": ["ls", "cat", "grep"]}
)

# Create a research agent
research_agent_id = await agent_manager.create_agent(
    agent_type=AgentType.RESEARCH,
    config={"max_results": 10}
)

# Create a code agent
code_agent_id = await agent_manager.create_agent(
    agent_type=AgentType.CODE,
    capabilities=[AgentCapability.FILE_WRITE],
    config={"languages": ["python", "javascript"]}
)

# Create an analysis agent
analysis_agent_id = await agent_manager.create_agent(
    agent_type=AgentType.ANALYSIS
)
```

### Submitting Tasks

```python
# Submit a task (auto-assigned to suitable agent)
task_context = TaskContext(
    task_id="task-001",
    task_description="List files in current directory",
    input_data={
        "command": "ls",
        "args": ["-la"],
        "timeout": 10
    },
    metadata={
        "required_capabilities": [AgentCapability.FILE_READ]
    }
)

task_id = await agent_manager.submit_task(task_context, priority=2)

# Submit a task to specific agent
task_context2 = TaskContext(
    task_id="task-002",
    task_description="Research Python best practices",
    input_data={
        "query": "Python async programming best practices",
        "type": "general",
        "depth": "deep"
    }
)

task_id2 = await agent_manager.submit_task(
    task_context2,
    priority=1,
    agent_id=research_agent_id
)
```

### Checking Task Status

```python
# Get task status
status = await agent_manager.get_task_status(task_id)

print(f"Task: {status['task_id']}")
print(f"Status: {status['status']}")
print(f"Agent: {status['assigned_agent']}")

if status['result']:
    print(f"Result: {status['result']['output_data']}")
```

### Agent Discovery

```python
# List all agents
all_agents = agent_manager.list_agents()

# List agents by type
command_agents = agent_manager.list_agents(agent_type=AgentType.COMMAND)

# List agents by capability
file_agents = agent_manager.list_agents(capability=AgentCapability.FILE_READ)

# List agents by status
idle_agents = agent_manager.list_agents(status=AgentState.IDLE)

# Get specific agent info
agent_info = agent_manager.get_agent(command_agent_id)
print(f"Agent: {agent_info.agent_id}")
print(f"Type: {agent_info.agent_type}")
print(f"Capabilities: {agent_info.capabilities}")
print(f"Status: {agent_info.status}")
print(f"Tasks completed: {agent_info.tasks_completed}")
```

### Inter-Agent Communication

```python
from src.agents.manager import CommunicationType

# Register message handler for an agent
received_messages = []

async def message_handler(message):
    received_messages.append(message)
    print(f"Received: {message.payload}")

agent_manager.register_message_handler(research_agent_id, message_handler)

# Send direct message
message_id = await agent_manager.send_message(
    from_agent=command_agent_id,
    to_agent=research_agent_id,
    message_type=CommunicationType.REQUEST,
    payload={"request": "Need information about Python", "data": "details"},
    requires_response=True
)

# Broadcast message to all agents
await agent_manager.send_message(
    from_agent="system",
    to_agent=None,  # Broadcast
    message_type=CommunicationType.BROADCAST,
    payload={"announcement": "System maintenance at 3 AM"}
)
```

### Context Sharing

```python
# Set shared context
agent_manager.set_shared_context("project_name", "AIShell")
agent_manager.set_shared_context("database_path", "/data/db.sqlite")

# Update multiple values
agent_manager.update_shared_context({
    "api_key": "xyz123",
    "environment": "production",
    "debug_mode": False
})

# Get shared context
project_name = agent_manager.get_shared_context("project_name")
api_key = agent_manager.get_shared_context("api_key", default="none")

# Clear context
agent_manager.clear_shared_context()
```

### Result Aggregation

```python
# Submit multiple tasks
task_ids = []
for i in range(5):
    task = TaskContext(
        task_id=f"analysis-{i}",
        task_description=f"Analyze dataset {i}",
        input_data={"data_source": f"dataset_{i}.csv"}
    )
    task_id = await agent_manager.submit_task(task)
    task_ids.append(task_id)

# Wait for tasks to complete (in real usage, use status polling)
await asyncio.sleep(5)

# Aggregate results - merge strategy
merged = await agent_manager.aggregate_results(task_ids, strategy="merge")
print(f"Merged results: {merged}")

# Aggregate results - list strategy
listed = await agent_manager.aggregate_results(task_ids, strategy="list")
print(f"Results count: {listed['count']}")
print(f"All results: {listed['results']}")
```

### Monitoring and Statistics

```python
# Get manager statistics
stats = agent_manager.get_stats()

print(f"Total agents: {stats['agents']['total']}")
print(f"Agents by type: {stats['agents']['by_type']}")
print(f"Agents by status: {stats['agents']['by_status']}")

print(f"Total tasks: {stats['tasks']['total']}")
print(f"Tasks by status: {stats['tasks']['by_status']}")
print(f"Queue size: {stats['tasks']['queue_size']}")

print(f"Message queue size: {stats['communication']['message_queue_size']}")
print(f"Shared context keys: {stats['communication']['shared_context_keys']}")
```

### Agent Lifecycle Management

```python
# Start an agent (mark as ready)
await agent_manager.start_agent(command_agent_id)

# Stop an agent (prevent new assignments)
await agent_manager.stop_agent(research_agent_id)

# Destroy an agent (cleanup and remove)
await agent_manager.destroy_agent(code_agent_id)

# Shutdown manager
await agent_manager.stop()
```

## Example: Complete Workflow

```python
import asyncio
from src.agents.manager import AgentManager, AgentType
from src.agents.base import AgentCapability, TaskContext

async def main():
    # Initialize manager
    manager = AgentManager()
    await manager.start()

    try:
        # Create agents
        cmd_agent = await manager.create_agent(
            agent_type=AgentType.COMMAND,
            capabilities=[AgentCapability.FILE_READ]
        )

        research_agent = await manager.create_agent(
            agent_type=AgentType.RESEARCH
        )

        code_agent = await manager.create_agent(
            agent_type=AgentType.CODE,
            capabilities=[AgentCapability.FILE_WRITE]
        )

        # Share context
        manager.set_shared_context("project", "MyProject")

        # Submit tasks
        task1 = TaskContext(
            task_id="research-task",
            task_description="Research API design patterns",
            input_data={
                "query": "RESTful API design best practices",
                "depth": "deep"
            }
        )

        task2 = TaskContext(
            task_id="code-task",
            task_description="Generate API endpoint code",
            input_data={
                "language": "python",
                "specification": "Create /users endpoint with GET and POST",
                "type": "generate"
            }
        )

        t1 = await manager.submit_task(task1, priority=2)
        t2 = await manager.submit_task(task2, priority=1)

        # Wait for completion
        await asyncio.sleep(3)

        # Check results
        status1 = await manager.get_task_status(t1)
        status2 = await manager.get_task_status(t2)

        print(f"Research Status: {status1['status']}")
        print(f"Code Status: {status2['status']}")

        # Get stats
        stats = manager.get_stats()
        print(f"Total agents: {stats['agents']['total']}")
        print(f"Total tasks: {stats['tasks']['total']}")

    finally:
        # Cleanup
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Agent Types

### CommandAgent
- Executes system commands safely
- Validates commands against allowlist
- Captures stdout/stderr
- Timeout management

### ResearchAgent
- Information gathering and synthesis
- Multi-source search
- Source credibility analysis
- Knowledge base integration

### CodeAgent
- Code generation from specifications
- Code refactoring and optimization
- Static analysis and quality checks
- Multi-language support

### AnalysisAgent
- Statistical analysis
- Pattern detection
- Trend analysis and forecasting
- Insight generation

## Best Practices

1. **Start the manager**: Always call `await manager.start()` before use
2. **Cleanup**: Always call `await manager.stop()` when done
3. **Use priorities**: Higher priority = more urgent (use wisely)
4. **Monitor status**: Poll task status for long-running operations
5. **Handle failures**: Implement retry logic for critical tasks
6. **Share context**: Use shared context for agent coordination
7. **Message handlers**: Register handlers before sending messages
8. **Capability matching**: Set required capabilities for automatic routing

## Integration with MCP

The AgentManager integrates seamlessly with MCP (Model Context Protocol) for enhanced coordination:

```python
from src.mcp_clients.client import MCPClientManager

# Initialize with MCP
mcp_client = MCPClientManager()
await mcp_client.connect()

agent_manager = AgentManager(
    llm_manager=llm_manager,
    mcp_client=mcp_client
)
```

## Performance Considerations

- **Concurrent tasks**: Limit `max_concurrent_tasks` based on system resources
- **Message queue**: Monitor queue size to prevent memory issues
- **Shared context**: Clear context periodically to prevent memory leaks
- **Task cleanup**: Implement task purging for completed tasks
- **Agent pooling**: Reuse agents instead of creating new ones frequently

## Troubleshooting

### Tasks not executing
- Check agent status (must be IDLE or EXECUTING)
- Verify required capabilities match available agents
- Check task queue size

### Messages not delivered
- Ensure message handler is registered before sending
- Verify recipient agent exists
- Check message queue processing

### High memory usage
- Clear completed tasks periodically
- Clear shared context when not needed
- Limit concurrent task count
- Monitor agent count

## See Also

- [BaseAgent Documentation](./base_agent.md)
- [Agent Types Documentation](./agent_types.md)
- [MCP Integration Guide](./mcp_integration.md)
