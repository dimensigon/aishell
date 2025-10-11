"""
Agent Chain - Sequential Agent Pipeline

Enables chaining multiple agents together where the output of one agent
becomes the input to the next, creating powerful sequential processing pipelines.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


@dataclass
class ChainLink:
    """Represents a single link in an agent chain"""
    agent_type: str
    transform: Optional[Callable[[Any], str]] = None
    validation: Optional[Callable[[Any], bool]] = None
    name: Optional[str] = None
    timeout: int = 120

    # Runtime fields
    link_id: str = field(default_factory=lambda: str(uuid4()))
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def get_name(self) -> str:
        """Get link name or generate from agent type"""
        return self.name or f"{self.agent_type}_link"


@dataclass
class ChainResult:
    """Result of agent chain execution"""
    chain_id: str
    chain_name: str
    success: bool
    links: List[ChainLink]
    final_output: Optional[Any]
    total_duration: float
    start_time: datetime
    end_time: datetime
    errors: List[str] = field(default_factory=list)

    def get_link_output(self, link_index: int) -> Optional[Any]:
        """Get output from specific link by index"""
        if 0 <= link_index < len(self.links):
            return self.links[link_index].output_data
        return None

    def get_link_by_name(self, name: str) -> Optional[ChainLink]:
        """Get link by name"""
        for link in self.links:
            if link.get_name() == name:
                return link
        return None


class AgentChain:
    """
    Sequential agent pipeline that chains multiple agents together.

    Each agent's output becomes the next agent's input, with optional
    transformation and validation between links.
    """

    def __init__(self, name: str = "agent_chain", initial_input: Any = None) -> None:
        self.name = name
        self.chain_id = str(uuid4())
        self.links: List[ChainLink] = []
        self.initial_input = initial_input
        self.context: Dict[str, Any] = {}

        logger.info(f"Initialized agent chain: {name} ({self.chain_id})")

    def add_link(
        self,
        agent_type: str,
        transform: Optional[Callable[[Any], str]] = None,
        validation: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
        timeout: int = 120
    ) -> 'AgentChain':
        """
        Add a link to the chain

        Args:
            agent_type: Type of agent to execute
            transform: Optional function to transform input before passing to agent
            validation: Optional function to validate output before proceeding
            name: Optional name for the link
            timeout: Timeout in seconds

        Returns:
            Self for method chaining
        """
        link = ChainLink(
            agent_type=agent_type,
            transform=transform,
            validation=validation,
            name=name,
            timeout=timeout
        )
        self.links.append(link)
        logger.debug(f"Added link '{link.get_name()}' to chain {self.name}")
        return self

    def then(
        self,
        agent_type: str,
        transform: Optional[Callable[[Any], str]] = None,
        validation: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
        timeout: int = 120
    ) -> 'AgentChain':
        """
        Alias for add_link() with fluent interface

        Example:
            chain.then("researcher").then("coder").then("tester")
        """
        return self.add_link(agent_type, transform, validation, name, timeout)

    def set_context(self, key: str, value: Any) -> None:
        """Set context variable available to all links"""
        self.context[key] = value

    async def execute(
        self,
        agent_executor: Callable[[str, str], Any],
        initial_input: Optional[Any] = None,
        stop_on_error: bool = True
    ) -> ChainResult:
        """
        Execute the agent chain

        Args:
            agent_executor: Async function that executes agent tasks
            initial_input: Optional input to override chain's initial_input
            stop_on_error: If True, stop chain on first error

        Returns:
            ChainResult with execution details
        """
        start_time = datetime.now()
        logger.info(f"Starting chain execution: {self.name} ({len(self.links)} links)")

        if not self.links:
            raise ValueError("Cannot execute empty chain")

        # Use provided input or fall back to instance initial_input
        current_input = initial_input if initial_input is not None else self.initial_input
        errors: List[str] = []

        for idx, link in enumerate(self.links):
            link_num = idx + 1
            logger.info(
                f"Executing link {link_num}/{len(self.links)}: "
                f"{link.get_name()} ({link.agent_type})"
            )

            link.start_time = datetime.now()
            link.input_data = current_input

            try:
                # Transform input if transformer provided
                if link.transform:
                    logger.debug(f"Transforming input for link {link_num}")
                    task_input = link.transform(current_input)
                else:
                    # Convert input to string for agent task
                    task_input = str(current_input) if current_input is not None else ""

                # Execute agent
                import asyncio
                output = await asyncio.wait_for(
                    agent_executor(link.agent_type, task_input),
                    timeout=link.timeout
                )

                link.output_data = output

                # Validate output if validator provided
                if link.validation:
                    logger.debug(f"Validating output for link {link_num}")
                    if not link.validation(output):
                        raise ValueError(f"Output validation failed for link {link_num}")

                link.success = True
                link.end_time = datetime.now()
                link.duration = (link.end_time - link.start_time).total_seconds()

                logger.info(
                    f"Link {link_num} completed successfully "
                    f"({link.duration:.2f}s)"
                )

                # Output becomes input for next link
                current_input = output

                # Store in context
                self.context[f"link_{idx}_output"] = output

            except asyncio.TimeoutError:
                error_msg = (
                    f"Link {link_num} ({link.get_name()}) timed out "
                    f"after {link.timeout}s"
                )
                logger.error(error_msg)
                link.error = error_msg
                link.end_time = datetime.now()
                link.duration = (link.end_time - link.start_time).total_seconds()
                errors.append(error_msg)

                if stop_on_error:
                    break

            except Exception as e:
                error_msg = f"Link {link_num} ({link.get_name()}) failed: {str(e)}"
                logger.error(error_msg)
                link.error = error_msg
                link.end_time = datetime.now()
                link.duration = (link.end_time - link.start_time).total_seconds()
                errors.append(error_msg)

                if stop_on_error:
                    break

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Determine success
        success = all(link.success for link in self.links) and not errors
        final_output = self.links[-1].output_data if self.links else None

        result = ChainResult(
            chain_id=self.chain_id,
            chain_name=self.name,
            success=success,
            links=self.links.copy(),
            final_output=final_output,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time,
            errors=errors
        )

        logger.info(
            f"Chain execution completed: {self.name} "
            f"({'success' if success else 'failed'}, {total_duration:.2f}s)"
        )

        return result

    def visualize(self) -> str:
        """Generate a text visualization of the chain"""
        lines = [f"Agent Chain: {self.name}"]
        lines.append("=" * 50)

        for idx, link in enumerate(self.links):
            arrow = "→" if idx < len(self.links) - 1 else "→ [END]"
            lines.append(f"\n{idx + 1}. {link.get_name()} ({link.agent_type})")
            if link.transform:
                lines.append("   └─ Transform: yes")
            if link.validation:
                lines.append("   └─ Validation: yes")
            lines.append(f"   {arrow}")

        return "\n".join(lines)

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of chain execution"""
        completed = sum(1 for link in self.links if link.success)
        failed = sum(1 for link in self.links if link.error is not None)
        total_time = sum(link.duration for link in self.links)

        return {
            "chain_name": self.name,
            "chain_id": self.chain_id,
            "total_links": len(self.links),
            "completed": completed,
            "failed": failed,
            "total_duration": total_time,
            "links": [
                {
                    "name": link.get_name(),
                    "agent_type": link.agent_type,
                    "success": link.success,
                    "duration": link.duration,
                    "error": link.error
                }
                for link in self.links
            ]
        }
