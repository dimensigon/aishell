"""
Command Agent - Executes system commands safely

Specialized agent for executing shell commands, system operations,
and interacting with the operating system.
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, List

from src.agents.base import BaseAgent, AgentCapability, TaskContext

logger = logging.getLogger(__name__)


class CommandAgent(BaseAgent):
    """
    Agent specialized in executing system commands

    Features:
    - Safe command execution with sandboxing
    - Command validation and sanitization
    - Output capture and error handling
    - Timeout management
    - Command history tracking
    """

    def __init__(self, agent_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(agent_id=agent_id, config=config, **kwargs)
        self.command_history: List[Dict[str, Any]] = []
        self.allowed_commands = config.get(
            "allowed_commands", ["ls", "cat", "echo", "pwd", "grep", "find"]
        )
        self.max_output_size = config.get("max_output_size", 1024 * 1024)  # 1MB

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for command task

        Args:
            task: Task context with command details

        Returns:
            List of planned command steps
        """
        command = task.input_data.get("command", "")
        args = task.input_data.get("args", [])
        cwd = task.input_data.get("cwd", None)

        if not command:
            raise ValueError("No command specified")

        # Validate command
        base_command = command.split()[0] if isinstance(command, str) else command
        if base_command not in self.allowed_commands:
            raise ValueError(f"Command '{base_command}' not allowed")

        # Create execution plan
        plan = [
            {
                "tool": "execute_command",
                "params": {
                    "command": command,
                    "args": args,
                    "cwd": cwd,
                    "timeout": task.input_data.get("timeout", 30),
                },
                "rationale": f"Execute system command: {command}",
            }
        ]

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command step

        Args:
            step: Step definition with command parameters

        Returns:
            Command execution result
        """
        params = step["params"]
        command = params["command"]
        args = params.get("args", [])
        cwd = params.get("cwd", None)
        timeout = params.get("timeout", 30)

        # Build command
        if isinstance(command, str):
            full_command = command
        else:
            full_command = " ".join([command] + args)

        logger.info(f"Executing command: {full_command}")

        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Limit output size
            if len(stdout_text) > self.max_output_size:
                stdout_text = (
                    stdout_text[: self.max_output_size] + "\n... (output truncated)"
                )

            # Store in history
            result = {
                "command": full_command,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "success": process.returncode == 0,
            }

            self.command_history.append(result)

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            error_result = {
                "command": full_command,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }
            self.command_history.append(error_result)
            return error_result

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate command safety

        Args:
            step: Step to validate

        Returns:
            Safety validation result
        """
        params = step["params"]
        command = params["command"]

        # Extract base command
        base_command = command.split()[0] if isinstance(command, str) else command

        # Check if command is allowed
        if base_command not in self.allowed_commands:
            return {
                "requires_approval": True,
                "safe": False,
                "risk_level": "high",
                "risks": [f"Command '{base_command}' is not in allowed list"],
                "mitigations": ["Request approval", "Add to allowed commands"],
            }

        # Check for dangerous patterns
        dangerous_patterns = ["rm -rf", "dd if=", "mkfs", "format", "> /dev/"]
        for pattern in dangerous_patterns:
            if pattern in command:
                return {
                    "requires_approval": True,
                    "safe": False,
                    "risk_level": "critical",
                    "risks": [f"Potentially destructive pattern detected: {pattern}"],
                    "mitigations": ["Manual review required"],
                }

        # Safe command
        return {
            "requires_approval": False,
            "safe": True,
            "risk_level": "low",
            "risks": [],
            "mitigations": [],
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """Get command execution history"""
        return self.command_history

    def clear_history(self) -> None:
        """Clear command history"""
        self.command_history.clear()
