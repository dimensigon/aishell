"""
Agent Manager for AI-Shell

Comprehensive agent lifecycle management, task delegation, and coordination.
Provides registry, discovery, communication, and result aggregation for agents.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from src.agents.base import (
    BaseAgent,
    AgentCapability,
    AgentConfig,
    AgentState,
    TaskContext,
    TaskResult,
)

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents supported by the manager"""

    COMMAND = "command"
    RESEARCH = "research"
    CODE = "code"
    ANALYSIS = "analysis"
    DATABASE = "database"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommunicationType(Enum):
    """Types of inter-agent communication"""

    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFY = "notify"


@dataclass
class AgentInfo:
    """Information about a registered agent"""

    agent_id: str
    agent_type: AgentType
    agent_instance: BaseAgent
    capabilities: List[AgentCapability]
    status: AgentState
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ManagedTask:
    """Task managed by the agent manager"""

    task_id: str
    context: TaskContext
    status: TaskStatus
    assigned_agent: Optional[str] = None
    result: Optional[TaskResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int = 1
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None


@dataclass
class AgentMessage:
    """Message for inter-agent communication"""

    message_id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: CommunicationType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    correlation_id: Optional[str] = None


class AgentManager:
    """
    Central manager for agent lifecycle, coordination, and communication.

    Features:
    - Agent registration and discovery
    - Task delegation and routing
    - Inter-agent communication
    - Result aggregation
    - Context sharing
    - Performance monitoring
    - Error handling and recovery
    """

    def __init__(
        self,
        llm_manager: Optional[Any] = None,
        tool_registry: Optional[Any] = None,
        state_manager: Optional[Any] = None,
        performance_monitor: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
        max_concurrent_tasks: int = 10,
    ):
        """
        Initialize the agent manager

        Args:
            llm_manager: LLM manager for AI capabilities
            tool_registry: Tool registry for agent actions
            state_manager: State manager for persistence
            performance_monitor: Performance monitoring
            mcp_client: MCP client for protocol integration
            max_concurrent_tasks: Maximum concurrent tasks per agent
        """
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        self.state_manager = state_manager
        self.performance_monitor = performance_monitor
        self.mcp_client = mcp_client
        self.max_concurrent_tasks = max_concurrent_tasks

        # Agent registry
        self._agents: Dict[str, AgentInfo] = {}
        self._agents_by_type: Dict[AgentType, Set[str]] = {
            agent_type: set() for agent_type in AgentType
        }
        self._agents_by_capability: Dict[AgentCapability, Set[str]] = {
            cap: set() for cap in AgentCapability
        }

        # Task management
        self._tasks: Dict[str, ManagedTask] = {}
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._active_tasks: Dict[str, asyncio.Task] = {}

        # Communication
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._shared_context: Dict[str, Any] = {}

        # Monitoring
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []

        logger.info("AgentManager initialized")

    async def start(self) -> None:
        """Start the agent manager and worker tasks"""
        if self._running:
            logger.warning("AgentManager already running")
            return

        self._running = True

        # Start worker tasks
        num_workers = min(self.max_concurrent_tasks, 5)
        for i in range(num_workers):
            worker = asyncio.create_task(self._task_worker(f"worker-{i}"))
            self._worker_tasks.append(worker)

        # Start message processor
        message_processor = asyncio.create_task(self._process_messages())
        self._worker_tasks.append(message_processor)

        logger.info(f"AgentManager started with {num_workers} workers")

    async def stop(self) -> None:
        """Stop the agent manager and cleanup"""
        if not self._running:
            return

        logger.info("Stopping AgentManager...")
        self._running = False

        # Cancel all active tasks
        for task in self._active_tasks.values():
            task.cancel()

        # Wait for workers to complete
        for worker in self._worker_tasks:
            worker.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        # Cleanup agents
        for agent_info in self._agents.values():
            await self._cleanup_agent(agent_info.agent_id)

        logger.info("AgentManager stopped")

    # ========== Agent Lifecycle Management ==========

    async def create_agent(
        self,
        agent_type: Union[AgentType, str],
        agent_id: Optional[str] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        config: Optional[Dict[str, Any]] = None,
        agent_class: Optional[type] = None,
    ) -> str:
        """
        Create and register a new agent

        Args:
            agent_type: Type of agent to create
            agent_id: Optional custom agent ID
            capabilities: Agent capabilities
            config: Agent configuration
            agent_class: Custom agent class (for CUSTOM type)

        Returns:
            Agent ID
        """
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type)

        agent_id = agent_id or f"{agent_type.value}-{uuid.uuid4().hex[:8]}"

        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already exists")

        # Create agent instance
        if agent_class:
            agent_instance = agent_class(
                agent_id=agent_id,
                config=config or {},
                llm_manager=self.llm_manager,
                tool_registry=self.tool_registry,
                state_manager=self.state_manager,
            )
        else:
            # Import and create appropriate agent type
            agent_instance = await self._create_agent_instance(
                agent_type, agent_id, config
            )

        # Register agent
        capabilities = capabilities or []
        agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            agent_instance=agent_instance,
            capabilities=capabilities,
            status=AgentState.IDLE,
        )

        self._agents[agent_id] = agent_info
        self._agents_by_type[agent_type].add(agent_id)

        for cap in capabilities:
            self._agents_by_capability[cap].add(agent_id)

        logger.info(f"Created agent: {agent_id} (type={agent_type.value})")

        return agent_id

    async def _create_agent_instance(
        self, agent_type: AgentType, agent_id: str, config: Optional[Dict[str, Any]]
    ) -> BaseAgent:
        """Create agent instance based on type"""
        # Import agent classes dynamically
        if agent_type == AgentType.COMMAND:
            from src.agents.command_agent import CommandAgent

            return CommandAgent(
                agent_id=agent_id,
                config=config or {},
                llm_manager=self.llm_manager,
                tool_registry=self.tool_registry,
                state_manager=self.state_manager,
            )
        elif agent_type == AgentType.RESEARCH:
            from src.agents.research_agent import ResearchAgent

            return ResearchAgent(
                agent_id=agent_id,
                config=config or {},
                llm_manager=self.llm_manager,
                tool_registry=self.tool_registry,
                state_manager=self.state_manager,
            )
        elif agent_type == AgentType.CODE:
            from src.agents.code_agent import CodeAgent

            return CodeAgent(
                agent_id=agent_id,
                config=config or {},
                llm_manager=self.llm_manager,
                tool_registry=self.tool_registry,
                state_manager=self.state_manager,
            )
        elif agent_type == AgentType.ANALYSIS:
            from src.agents.analysis_agent import AnalysisAgent

            return AnalysisAgent(
                agent_id=agent_id,
                config=config or {},
                llm_manager=self.llm_manager,
                tool_registry=self.tool_registry,
                state_manager=self.state_manager,
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    async def destroy_agent(self, agent_id: str) -> bool:
        """
        Destroy and unregister an agent

        Args:
            agent_id: Agent to destroy

        Returns:
            True if destroyed successfully
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found")
            return False

        agent_info = self._agents[agent_id]

        # Cancel any active tasks
        for task_id, managed_task in list(self._tasks.items()):
            if managed_task.assigned_agent == agent_id:
                await self._cancel_task(task_id)

        # Cleanup and unregister
        await self._cleanup_agent(agent_id)

        # Remove from registries
        self._agents_by_type[agent_info.agent_type].discard(agent_id)
        for cap in agent_info.capabilities:
            self._agents_by_capability[cap].discard(agent_id)

        del self._agents[agent_id]

        logger.info(f"Destroyed agent: {agent_id}")
        return True

    async def _cleanup_agent(self, agent_id: str) -> None:
        """Cleanup agent resources"""
        if agent_id in self._agents:
            agent_info = self._agents[agent_id]
            # Perform any necessary cleanup
            logger.debug(f"Cleaning up agent: {agent_id}")

    async def start_agent(self, agent_id: str) -> bool:
        """
        Start an agent (mark as ready for tasks)

        Args:
            agent_id: Agent to start

        Returns:
            True if started successfully
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False

        agent_info = self._agents[agent_id]
        agent_info.status = AgentState.IDLE
        agent_info.last_active = datetime.now()

        logger.info(f"Started agent: {agent_id}")
        return True

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent (prevent new task assignments)

        Args:
            agent_id: Agent to stop

        Returns:
            True if stopped successfully
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False

        agent_info = self._agents[agent_id]
        agent_info.status = AgentState.PAUSED

        logger.info(f"Stopped agent: {agent_id}")
        return True

    # ========== Agent Discovery ==========

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information"""
        return self._agents.get(agent_id)

    def list_agents(
        self,
        agent_type: Optional[AgentType] = None,
        capability: Optional[AgentCapability] = None,
        status: Optional[AgentState] = None,
    ) -> List[AgentInfo]:
        """
        List agents matching criteria

        Args:
            agent_type: Filter by agent type
            capability: Filter by capability
            status: Filter by status

        Returns:
            List of matching agents
        """
        agents = list(self._agents.values())

        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]

        if capability:
            agent_ids = self._agents_by_capability.get(capability, set())
            agents = [a for a in agents if a.agent_id in agent_ids]

        if status:
            agents = [a for a in agents if a.status == status]

        return agents

    def find_agent_for_task(
        self, task_context: TaskContext
    ) -> Optional[str]:
        """
        Find best agent for a task based on capabilities and load

        Args:
            task_context: Task to assign

        Returns:
            Agent ID or None if no suitable agent found
        """
        # Simple strategy: find idle agent with required capabilities
        # Can be enhanced with load balancing, performance history, etc.

        required_capabilities = task_context.metadata.get("required_capabilities", [])

        # Find agents with all required capabilities
        candidate_agents = set(self._agents.keys())

        for cap in required_capabilities:
            if isinstance(cap, str):
                cap = AgentCapability(cap)
            capable_agents = self._agents_by_capability.get(cap, set())
            candidate_agents &= capable_agents

        # Filter by status (idle agents preferred)
        idle_agents = [
            aid
            for aid in candidate_agents
            if self._agents[aid].status == AgentState.IDLE
        ]

        if idle_agents:
            # Return agent with fewest completed tasks (basic load balancing)
            return min(
                idle_agents, key=lambda aid: self._agents[aid].tasks_completed
            )

        # If no idle agents, return any executing agent
        executing_agents = [
            aid
            for aid in candidate_agents
            if self._agents[aid].status == AgentState.EXECUTING
        ]

        if executing_agents:
            return min(
                executing_agents, key=lambda aid: self._agents[aid].tasks_completed
            )

        return None

    # ========== Task Management ==========

    async def submit_task(
        self,
        task_context: TaskContext,
        priority: int = 1,
        agent_id: Optional[str] = None,
    ) -> str:
        """
        Submit a task for execution

        Args:
            task_context: Task to execute
            priority: Task priority (higher = more urgent)
            agent_id: Optional specific agent to assign to

        Returns:
            Task ID
        """
        task_id = task_context.task_id

        if task_id in self._tasks:
            raise ValueError(f"Task {task_id} already exists")

        managed_task = ManagedTask(
            task_id=task_id,
            context=task_context,
            status=TaskStatus.PENDING,
            priority=priority,
        )

        if agent_id:
            if agent_id not in self._agents:
                raise ValueError(f"Agent {agent_id} not found")
            managed_task.assigned_agent = agent_id
            managed_task.status = TaskStatus.ASSIGNED

        self._tasks[task_id] = managed_task

        # Add to queue (negative priority for max-heap behavior)
        await self._task_queue.put((-priority, time.time(), task_id))

        logger.info(f"Submitted task: {task_id} (priority={priority})")

        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and details"""
        if task_id not in self._tasks:
            return None

        managed_task = self._tasks[task_id]

        return {
            "task_id": task_id,
            "status": managed_task.status.value,
            "assigned_agent": managed_task.assigned_agent,
            "created_at": managed_task.created_at.isoformat(),
            "started_at": (
                managed_task.started_at.isoformat()
                if managed_task.started_at
                else None
            ),
            "completed_at": (
                managed_task.completed_at.isoformat()
                if managed_task.completed_at
                else None
            ),
            "result": (
                {
                    "status": managed_task.result.status,
                    "output_data": managed_task.result.output_data,
                }
                if managed_task.result
                else None
            ),
            "error": managed_task.error,
        }

    async def _cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id not in self._tasks:
            return False

        managed_task = self._tasks[task_id]
        managed_task.status = TaskStatus.CANCELLED

        # Cancel active asyncio task if exists
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            del self._active_tasks[task_id]

        logger.info(f"Cancelled task: {task_id}")
        return True

    async def _task_worker(self, worker_id: str) -> None:
        """Worker task that processes tasks from the queue"""
        logger.info(f"Task worker {worker_id} started")

        while self._running:
            try:
                # Get next task from queue
                try:
                    _, _, task_id = await asyncio.wait_for(
                        self._task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                if task_id not in self._tasks:
                    continue

                managed_task = self._tasks[task_id]

                # Find agent if not assigned
                if not managed_task.assigned_agent:
                    agent_id = self.find_agent_for_task(managed_task.context)
                    if not agent_id:
                        # No suitable agent, requeue
                        await asyncio.sleep(1)
                        await self._task_queue.put(
                            (-managed_task.priority, time.time(), task_id)
                        )
                        continue
                    managed_task.assigned_agent = agent_id

                # Execute task
                await self._execute_task(managed_task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.info(f"Task worker {worker_id} stopped")

    async def _execute_task(self, managed_task: ManagedTask) -> None:
        """Execute a task with an agent"""
        task_id = managed_task.task_id
        agent_id = managed_task.assigned_agent

        if not agent_id or agent_id not in self._agents:
            logger.error(f"Invalid agent for task {task_id}")
            managed_task.status = TaskStatus.FAILED
            managed_task.error = "Invalid agent"
            return

        agent_info = self._agents[agent_id]
        agent = agent_info.agent_instance

        try:
            managed_task.status = TaskStatus.IN_PROGRESS
            managed_task.started_at = datetime.now()
            agent_info.status = AgentState.EXECUTING
            agent_info.last_active = datetime.now()

            # Track performance
            start_time = time.time()

            # Execute task
            result = await agent.run(managed_task.context)

            # Update metrics
            execution_time = time.time() - start_time

            if self.performance_monitor:
                self.performance_monitor.record_query(
                    query=f"agent_task:{task_id}",
                    execution_time=execution_time,
                    rows=1,
                )

            # Update task
            managed_task.result = result
            managed_task.status = TaskStatus.COMPLETED
            managed_task.completed_at = datetime.now()

            # Update agent
            agent_info.tasks_completed += 1
            agent_info.status = AgentState.IDLE

            logger.info(
                f"Task {task_id} completed by {agent_id} "
                f"in {execution_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)

            managed_task.status = TaskStatus.FAILED
            managed_task.error = str(e)
            managed_task.completed_at = datetime.now()

            agent_info.tasks_failed += 1
            agent_info.status = AgentState.IDLE

            # Retry if possible
            if managed_task.retry_count < managed_task.max_retries:
                managed_task.retry_count += 1
                managed_task.status = TaskStatus.PENDING
                await self._task_queue.put(
                    (-managed_task.priority, time.time(), task_id)
                )
                logger.info(
                    f"Retrying task {task_id} "
                    f"(attempt {managed_task.retry_count}/{managed_task.max_retries})"
                )

    # ========== Inter-Agent Communication ==========

    async def send_message(
        self,
        from_agent: str,
        to_agent: Optional[str],
        message_type: CommunicationType,
        payload: Dict[str, Any],
        requires_response: bool = False,
    ) -> str:
        """
        Send message between agents

        Args:
            from_agent: Sender agent ID
            to_agent: Receiver agent ID (None for broadcast)
            message_type: Type of message
            payload: Message data
            requires_response: Whether response is required

        Returns:
            Message ID
        """
        message_id = f"msg-{uuid.uuid4().hex[:8]}"

        message = AgentMessage(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            requires_response=requires_response,
        )

        await self._message_queue.put(message)

        logger.debug(
            f"Message {message_id} from {from_agent} to "
            f"{to_agent or 'broadcast'} ({message_type.value})"
        )

        return message_id

    def register_message_handler(
        self, agent_id: str, handler: Callable[[AgentMessage], None]
    ) -> None:
        """Register message handler for an agent"""
        if agent_id not in self._message_handlers:
            self._message_handlers[agent_id] = []
        self._message_handlers[agent_id].append(handler)

    async def _process_messages(self) -> None:
        """Process messages from the queue"""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(), timeout=1.0
                )

                # Deliver to target agent(s)
                if message.to_agent:
                    # Direct message
                    await self._deliver_message(message.to_agent, message)
                else:
                    # Broadcast
                    for agent_id in self._agents.keys():
                        if agent_id != message.from_agent:
                            await self._deliver_message(agent_id, message)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}", exc_info=True)

    async def _deliver_message(self, agent_id: str, message: AgentMessage) -> None:
        """Deliver message to agent handlers"""
        if agent_id not in self._message_handlers:
            return

        for handler in self._message_handlers[agent_id]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(
                    f"Handler error for agent {agent_id}: {e}", exc_info=True
                )

    # ========== Context Sharing ==========

    def set_shared_context(self, key: str, value: Any) -> None:
        """Set shared context value"""
        self._shared_context[key] = value
        logger.debug(f"Set shared context: {key}")

    def get_shared_context(self, key: str, default: Any = None) -> Any:
        """Get shared context value"""
        return self._shared_context.get(key, default)

    def update_shared_context(self, updates: Dict[str, Any]) -> None:
        """Update multiple context values"""
        self._shared_context.update(updates)
        logger.debug(f"Updated shared context with {len(updates)} keys")

    def clear_shared_context(self) -> None:
        """Clear all shared context"""
        self._shared_context.clear()
        logger.debug("Cleared shared context")

    # ========== Result Aggregation ==========

    async def aggregate_results(
        self, task_ids: List[str], strategy: str = "merge"
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple tasks

        Args:
            task_ids: List of task IDs to aggregate
            strategy: Aggregation strategy ('merge', 'list', 'reduce')

        Returns:
            Aggregated results
        """
        results = []

        for task_id in task_ids:
            if task_id in self._tasks:
                managed_task = self._tasks[task_id]
                if managed_task.result:
                    results.append(managed_task.result.output_data)

        if strategy == "merge":
            # Merge all dictionaries
            aggregated = {}
            for result in results:
                if isinstance(result, dict):
                    aggregated.update(result)
            return aggregated

        elif strategy == "list":
            # Return as list
            return {"results": results, "count": len(results)}

        elif strategy == "reduce":
            # Custom reduction (placeholder)
            return {
                "results": results,
                "count": len(results),
                "summary": "Results aggregated",
            }

        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")

    # ========== Status and Monitoring ==========

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        total_agents = len(self._agents)
        agents_by_status = {}
        for agent_info in self._agents.values():
            status = agent_info.status.value
            agents_by_status[status] = agents_by_status.get(status, 0) + 1

        total_tasks = len(self._tasks)
        tasks_by_status = {}
        for task in self._tasks.values():
            status = task.status.value
            tasks_by_status[status] = tasks_by_status.get(status, 0) + 1

        return {
            "agents": {
                "total": total_agents,
                "by_status": agents_by_status,
                "by_type": {
                    agent_type.value: len(agent_ids)
                    for agent_type, agent_ids in self._agents_by_type.items()
                    if agent_ids
                },
            },
            "tasks": {
                "total": total_tasks,
                "by_status": tasks_by_status,
                "queue_size": self._task_queue.qsize(),
                "active": len(self._active_tasks),
            },
            "communication": {
                "message_queue_size": self._message_queue.qsize(),
                "shared_context_keys": len(self._shared_context),
            },
            "running": self._running,
        }
