"""
Context-aware command suggestion system for AI-Shell

Provides intelligent command suggestions based on:
- Command history
- Current context
- User patterns
- Similar commands
- Semantic understanding
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, deque
from datetime import datetime, timedelta
import difflib
import json

logger = logging.getLogger(__name__)


@dataclass
class CommandContext:
    """Context information for command suggestions"""
    current_command: str
    command_history: List[str] = field(default_factory=list)
    current_directory: str = "/"
    active_connections: List[str] = field(default_factory=list)
    last_error: Optional[str] = None
    session_duration: float = 0.0
    user_patterns: Dict[str, int] = field(default_factory=dict)


@dataclass
class Suggestion:
    """Command suggestion with metadata"""
    command: str
    description: str
    confidence: float
    category: str
    usage_example: Optional[str] = None
    shortcut: Optional[str] = None


class CommandSuggester:
    """Intelligent command suggestion system"""

    def __init__(self, llm_manager=None):
        """Initialize command suggester

        Args:
            llm_manager: Optional LLM manager for semantic understanding
        """
        self.llm_manager = llm_manager
        self.command_history = deque(maxlen=100)
        self.command_patterns = Counter()
        self.error_patterns = {}
        self.session_start = datetime.now()

        # Command database with categories and descriptions
        self.commands = {
            "database": [
                ("query <sql>", "Execute SQL query", "SELECT * FROM users"),
                ("show tables", "List all tables in database", None),
                ("describe <table>", "Show table structure", "describe users"),
                ("analyze <query>", "Analyze query performance", "analyze SELECT * FROM orders")
            ],
            "ai": [
                ("ask <question>", "Ask AI assistant", "ask How do I optimize this query?"),
                ("agent <task>", "Delegate task to agents", "agent analyze database performance"),
                ("agents", "List available agents", None),
                ("llm generate <prompt>", "Generate text with LLM", "llm generate Write a SQL query")
            ],
            "mcp": [
                ("mcp resources", "List MCP resources", None),
                ("mcp tools", "List MCP tools", None),
                ("mcp connect <type>", "Create MCP connection", "mcp connect postgresql"),
                ("mcp status", "Show connection status", None)
            ],
            "llm": [
                ("llm providers", "List LLM providers", None),
                ("llm switch <provider>", "Switch LLM provider", "llm switch openai gpt-4"),
                ("llm status", "Show LLM status", None),
                ("llm generate <text>", "Generate text", "llm generate Explain this code")
            ],
            "system": [
                ("health", "Show system health", None),
                ("metrics", "Show performance metrics", None),
                ("history", "Show command history", None),
                ("help [command]", "Get help on commands", "help query")
            ],
            "navigation": [
                ("cd <path>", "Change directory", "cd /home/user"),
                ("ls [path]", "List directory contents", "ls -la"),
                ("pwd", "Show current directory", None),
                ("find <pattern>", "Find files", "find *.py")
            ]
        }

        # Command shortcuts
        self.shortcuts = {
            "q": "query",
            "a": "ask",
            "ag": "agent",
            "h": "help",
            "m": "metrics",
            "s": "mcp status",
            "ll": "llm",
            "x": "exit"
        }

        # Common command sequences
        self.sequences = [
            ["mcp connect", "mcp status", "query"],
            ["llm switch", "llm generate"],
            ["agent", "metrics"],
            ["query", "analyze"],
            ["show tables", "describe"]
        ]

    def add_to_history(self, command: str) -> None:
        """Add command to history and update patterns

        Args:
            command: Command to add to history
        """
        self.command_history.append(command)

        # Extract command prefix
        prefix = command.split()[0] if command else ""
        self.command_patterns[prefix] += 1

        # Track command pairs for sequence learning
        if len(self.command_history) >= 2:
            prev_cmd = self.command_history[-2].split()[0]
            curr_cmd = prefix
            pair = f"{prev_cmd}->{curr_cmd}"
            self.command_patterns[pair] += 1

    def record_error(self, command: str, error: str) -> None:
        """Record command error for learning

        Args:
            command: Command that caused error
            error: Error message
        """
        if command not in self.error_patterns:
            self.error_patterns[command] = []
        self.error_patterns[command].append(error)

    def get_suggestions(self, context: CommandContext, limit: int = 5) -> List[Suggestion]:
        """Get command suggestions based on context

        Args:
            context: Current command context
            limit: Maximum number of suggestions

        Returns:
            List of command suggestions
        """
        suggestions = []

        # 1. Partial command completion
        if context.current_command:
            suggestions.extend(self._get_completion_suggestions(context.current_command))

        # 2. Error recovery suggestions
        if context.last_error:
            suggestions.extend(self._get_error_recovery_suggestions(context.last_error))

        # 3. Sequence-based suggestions
        if context.command_history:
            suggestions.extend(self._get_sequence_suggestions(context.command_history))

        # 4. Context-based suggestions
        suggestions.extend(self._get_context_suggestions(context))

        # 5. Popular commands
        suggestions.extend(self._get_popular_suggestions())

        # Remove duplicates and sort by confidence
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s.command not in seen:
                seen.add(s.command)
                unique_suggestions.append(s)

        # Sort by confidence and return top suggestions
        unique_suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return unique_suggestions[:limit]

    def _get_completion_suggestions(self, partial: str) -> List[Suggestion]:
        """Get command completion suggestions

        Args:
            partial: Partial command string

        Returns:
            List of completion suggestions
        """
        suggestions = []
        partial_lower = partial.lower()

        # Check all commands for matches
        for category, commands in self.commands.items():
            for cmd_template, description, example in commands:
                cmd_prefix = cmd_template.split()[0]

                # Check if command starts with partial
                if cmd_prefix.startswith(partial_lower):
                    confidence = 0.9 if cmd_prefix == partial_lower else 0.7
                    suggestions.append(Suggestion(
                        command=cmd_template,
                        description=description,
                        confidence=confidence,
                        category=category,
                        usage_example=example
                    ))

                # Fuzzy matching for typos
                elif difflib.SequenceMatcher(None, partial_lower, cmd_prefix).ratio() > 0.7:
                    suggestions.append(Suggestion(
                        command=cmd_template,
                        description=f"{description} (did you mean?)",
                        confidence=0.5,
                        category=category,
                        usage_example=example
                    ))

        # Check shortcuts
        if partial_lower in self.shortcuts:
            full_cmd = self.shortcuts[partial_lower]
            suggestions.append(Suggestion(
                command=full_cmd,
                description=f"Shortcut for {full_cmd}",
                confidence=0.95,
                category="shortcut",
                shortcut=partial_lower
            ))

        return suggestions

    def _get_error_recovery_suggestions(self, error: str) -> List[Suggestion]:
        """Get suggestions for error recovery

        Args:
            error: Error message

        Returns:
            List of recovery suggestions
        """
        suggestions = []
        error_lower = error.lower()

        # Connection errors
        if "connection" in error_lower or "connect" in error_lower:
            suggestions.append(Suggestion(
                command="mcp status",
                description="Check connection status",
                confidence=0.8,
                category="recovery"
            ))
            suggestions.append(Suggestion(
                command="mcp connect",
                description="Reconnect to database",
                confidence=0.7,
                category="recovery"
            ))

        # SQL syntax errors
        if "syntax" in error_lower or "sql" in error_lower:
            suggestions.append(Suggestion(
                command="ask How to fix SQL syntax error?",
                description="Get AI help with SQL",
                confidence=0.8,
                category="recovery"
            ))
            suggestions.append(Suggestion(
                command="help query",
                description="Show query help",
                confidence=0.6,
                category="recovery"
            ))

        # Permission errors
        if "permission" in error_lower or "denied" in error_lower:
            suggestions.append(Suggestion(
                command="health",
                description="Check system status",
                confidence=0.7,
                category="recovery"
            ))

        # LLM errors
        if "llm" in error_lower or "provider" in error_lower:
            suggestions.append(Suggestion(
                command="llm status",
                description="Check LLM status",
                confidence=0.8,
                category="recovery"
            ))
            suggestions.append(Suggestion(
                command="llm switch mock",
                description="Switch to mock provider",
                confidence=0.6,
                category="recovery"
            ))

        return suggestions

    def _get_sequence_suggestions(self, history: List[str]) -> List[Suggestion]:
        """Get suggestions based on command sequences

        Args:
            history: Command history

        Returns:
            List of sequence-based suggestions
        """
        suggestions = []

        if not history:
            return suggestions

        last_cmd = history[-1].split()[0] if history else ""

        # Check known sequences
        for sequence in self.sequences:
            try:
                idx = sequence.index(last_cmd)
                if idx < len(sequence) - 1:
                    next_cmd = sequence[idx + 1]
                    # Find full command details
                    for category, commands in self.commands.items():
                        for cmd_template, description, example in commands:
                            if cmd_template.startswith(next_cmd):
                                suggestions.append(Suggestion(
                                    command=cmd_template,
                                    description=f"{description} (common sequence)",
                                    confidence=0.7,
                                    category=category,
                                    usage_example=example
                                ))
                                break
            except ValueError:
                continue

        # Check learned patterns
        for pattern, count in self.command_patterns.most_common(5):
            if "->" in pattern and pattern.startswith(f"{last_cmd}->"):
                next_cmd = pattern.split("->")[1]
                confidence = min(0.6 + (count * 0.05), 0.9)
                suggestions.append(Suggestion(
                    command=next_cmd,
                    description=f"Frequently used after {last_cmd}",
                    confidence=confidence,
                    category="pattern"
                ))

        return suggestions

    def _get_context_suggestions(self, context: CommandContext) -> List[Suggestion]:
        """Get context-aware suggestions

        Args:
            context: Current context

        Returns:
            List of context-based suggestions
        """
        suggestions = []

        # If no active connections, suggest connecting
        if not context.active_connections:
            suggestions.append(Suggestion(
                command="mcp connect postgresql",
                description="Connect to PostgreSQL database",
                confidence=0.6,
                category="mcp"
            ))

        # If session just started, suggest common starting commands
        if context.session_duration < 60:  # Less than 1 minute
            suggestions.append(Suggestion(
                command="health",
                description="Check system health",
                confidence=0.5,
                category="system"
            ))
            suggestions.append(Suggestion(
                command="help",
                description="Show available commands",
                confidence=0.5,
                category="system"
            ))

        # Time-based suggestions
        current_hour = datetime.now().hour
        if 9 <= current_hour < 12:  # Morning
            suggestions.append(Suggestion(
                command="metrics",
                description="Check morning metrics",
                confidence=0.4,
                category="system"
            ))

        return suggestions

    def _get_popular_suggestions(self) -> List[Suggestion]:
        """Get suggestions based on popular commands

        Returns:
            List of popular command suggestions
        """
        suggestions = []

        # Get top used commands
        for cmd, count in self.command_patterns.most_common(3):
            if "->" not in cmd:  # Skip sequence patterns
                confidence = min(0.3 + (count * 0.05), 0.7)

                # Find full command details
                for category, commands in self.commands.items():
                    for cmd_template, description, example in commands:
                        if cmd_template.startswith(cmd):
                            suggestions.append(Suggestion(
                                command=cmd_template,
                                description=f"{description} (frequently used)",
                                confidence=confidence,
                                category=category,
                                usage_example=example
                            ))
                            break

        return suggestions

    def explain_command(self, command: str) -> str:
        """Explain what a command does

        Args:
            command: Command to explain

        Returns:
            Explanation of the command
        """
        cmd_parts = command.split()
        cmd_prefix = cmd_parts[0] if cmd_parts else ""

        # Find command in database
        for category, commands in self.commands.items():
            for cmd_template, description, example in commands:
                if cmd_template.split()[0] == cmd_prefix:
                    explanation = f"Command: {cmd_template}\n"
                    explanation += f"Description: {description}\n"
                    explanation += f"Category: {category}\n"
                    if example:
                        explanation += f"Example: {example}"
                    return explanation

        # Check if it's a shortcut
        if cmd_prefix in self.shortcuts:
            return f"'{cmd_prefix}' is a shortcut for '{self.shortcuts[cmd_prefix]}'"

        return f"Unknown command: {cmd_prefix}"

    def get_command_help(self, category: Optional[str] = None) -> str:
        """Get help text for commands

        Args:
            category: Optional category to filter by

        Returns:
            Help text
        """
        help_text = "Available Commands:\n" + "=" * 50 + "\n\n"

        categories_to_show = [category] if category else self.commands.keys()

        for cat in categories_to_show:
            if cat not in self.commands:
                continue

            help_text += f"{cat.upper()} COMMANDS:\n"
            help_text += "-" * 30 + "\n"

            for cmd_template, description, example in self.commands[cat]:
                help_text += f"  {cmd_template:<25} - {description}\n"
                if example:
                    help_text += f"    Example: {example}\n"
            help_text += "\n"

        # Add shortcuts section
        if not category or category == "shortcuts":
            help_text += "SHORTCUTS:\n"
            help_text += "-" * 30 + "\n"
            for shortcut, full_cmd in self.shortcuts.items():
                help_text += f"  {shortcut:<5} -> {full_cmd}\n"

        return help_text

    async def get_ai_suggestion(self, context: CommandContext) -> Optional[str]:
        """Get AI-powered suggestion using LLM

        Args:
            context: Current context

        Returns:
            AI suggestion or None
        """
        if not self.llm_manager or not self.llm_manager.initialized:
            return None

        try:
            # Build prompt for LLM
            prompt = f"""Given the following context, suggest the most appropriate next command:

Current command: {context.current_command}
Last commands: {', '.join(context.command_history[-3:])}
Last error: {context.last_error or 'None'}
Active connections: {', '.join(context.active_connections) or 'None'}

Suggest a single command that would be most helpful. Only return the command, no explanation."""

            response = self.llm_manager.provider.generate(prompt, max_tokens=50)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to get AI suggestion: {e}")
            return None