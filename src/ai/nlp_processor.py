"""
NLP Processor - Natural Language Processing for AI-Shell

Provides sophisticated natural language understanding for command-line interactions:
- Intent recognition and classification
- Entity extraction (files, paths, commands, parameters)
- Natural language to shell command translation
- Context-aware command suggestions
- Ambiguity resolution with confidence scoring
- Multi-turn conversation support
"""

import re
import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents"""
    # Command execution intents
    FILE_OPERATION = "file_operation"      # ls, cat, find, etc.
    DIRECTORY_NAV = "directory_nav"        # cd, pwd, tree
    FILE_SEARCH = "file_search"            # find, grep, locate
    FILE_MANIPULATION = "file_manipulation" # cp, mv, rm, mkdir
    SYSTEM_INFO = "system_info"            # whoami, hostname, uptime
    PROCESS_MGMT = "process_mgmt"          # ps, kill, top
    NETWORK_OPS = "network_ops"            # ping, curl, wget
    PACKAGE_MGMT = "package_mgmt"          # apt, pip, npm
    VERSION_CONTROL = "version_control"    # git commands

    # Query intents
    INFORMATION_QUERY = "information_query" # "What is...", "How does..."
    HELP_REQUEST = "help_request"           # "Help me with...", "Show me how..."
    EXPLANATION = "explanation"             # "Explain...", "Why..."

    # Interactive intents
    CONVERSATION = "conversation"           # General chat
    CLARIFICATION = "clarification"         # Asking for clarification
    CONFIRMATION = "confirmation"           # Yes/No responses

    # Meta intents
    MODE_CHANGE = "mode_change"            # Switching shell modes
    CONFIG_CHANGE = "config_change"        # Changing settings
    UNKNOWN = "unknown"                    # Could not determine


class EntityType(Enum):
    """Types of entities that can be extracted"""
    FILE_PATH = "file_path"
    DIRECTORY = "directory"
    FILE_PATTERN = "file_pattern"
    COMMAND = "command"
    PARAMETER = "parameter"
    FLAG = "flag"
    NUMBER = "number"
    STRING_LITERAL = "string_literal"
    ENVIRONMENT_VAR = "environment_var"
    URL = "url"
    IP_ADDRESS = "ip_address"
    PACKAGE_NAME = "package_name"
    GIT_BRANCH = "git_branch"
    PROCESS_NAME = "process_name"


@dataclass
class Entity:
    """Extracted entity from natural language"""
    type: EntityType
    value: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intent:
    """Recognized intent from natural language"""
    type: IntentType
    confidence: float
    entities: List[Entity] = field(default_factory=list)
    suggested_command: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NLPContext:
    """Context for natural language processing"""
    current_directory: str = "~"
    command_history: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    recent_files: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    last_intent: Optional[Intent] = None


class NLPProcessor:
    """
    Advanced NLP processor for AI-Shell

    Features:
    - Intent recognition using pattern matching and ML (when LLM available)
    - Entity extraction with high precision
    - Command translation with confidence scoring
    - Context-aware suggestions
    - Ambiguity detection and resolution
    - Multi-language command support
    """

    def __init__(self, llm_manager=None):
        """
        Initialize NLP processor

        Args:
            llm_manager: Optional LLM manager for advanced processing
        """
        self.llm_manager = llm_manager
        self.context = NLPContext()

        # Initialize pattern libraries
        self._init_patterns()
        self._init_command_templates()
        self._init_entity_patterns()

        # Performance tracking
        self.total_processed = 0
        self.successful_translations = 0

    def _init_patterns(self):
        """Initialize intent recognition patterns"""
        self.intent_patterns = {
            IntentType.FILE_OPERATION: [
                r'\b(show|list|display|view)\b.*\b(file|files|content)\b',
                r'\b(cat|less|more|head|tail)\b',
                r'\bls\b',
                r'\bshow me\b.*\bfile',
            ],
            IntentType.DIRECTORY_NAV: [
                r'\b(go to|navigate to|change to|move to)\b',
                r'\b(cd|pushd|popd)\b',
                r'\bwhere am i\b',
                r'\bcurrent (directory|folder|location)\b',
                r'\bchange to\b',
                r'\bgo to\b',
            ],
            IntentType.FILE_SEARCH: [
                r'\b(find|search|locate|look for)\b.*\b(file|files)\b',
                r'\b(find|search|locate)\b.*\b(python|txt|log)',
                r'\b(search for)\b',
                r'\bgrep\b',
            ],
            IntentType.FILE_MANIPULATION: [
                r'\b(copy|move|delete|remove|rename)\b',
                r'\b(cp|mv|rm|mkdir|rmdir|touch)\b',
                r'\bcreate (directory|folder)\b',
            ],
            IntentType.SYSTEM_INFO: [
                r'\b(system|computer|machine)\b.*\b(info|information|details)\b',
                r'\b(who am i|hostname|uptime|uname)\b',
                r'\b(show|check|display)\b.*\b(disk space|memory|hostname)\b',
                r'\b(my|the) (username|hostname)\b',
            ],
            IntentType.PROCESS_MGMT: [
                r'\b(show|list|kill|stop|terminate)\b.*\b(process|processes|server)\b',
                r'\b(ps|top|htop|kill)\b',
                r'\bstop the\b',
            ],
            IntentType.NETWORK_OPS: [
                r'\b(ping|curl|wget|download|fetch)\b',
                r'\bcheck.*\b(network|connection|url)\b',
            ],
            IntentType.PACKAGE_MGMT: [
                r'\b(install|uninstall|update|upgrade)\b.*\b(package|library|module)\b',
                r'\b(apt|pip|npm|yarn|brew)\b',
            ],
            IntentType.VERSION_CONTROL: [
                r'\bgit\b',
                r'\b(commit|push|pull|clone|branch)\b',
            ],
            IntentType.HELP_REQUEST: [
                r'\b(help me|assist|guide)\b',
                r'\bshow me how\b',
                r'\bi (don\'t know|need help)\b',
            ],
            IntentType.INFORMATION_QUERY: [
                r'\b(what is|what are|what\'s)\b',
                r'\b(how does|how do)\b',
                r'\b(can you (tell me|explain))\b',
            ],
            IntentType.EXPLANATION: [
                r'\b(explain|describe|clarify)\b',
                r'\bwhy (does|do|is|are)\b',
            ],
            IntentType.MODE_CHANGE: [
                r'\b(switch|change|enter)\b.*\bmode\b',
            ],
        }

    def _init_command_templates(self):
        """Initialize command translation templates"""
        self.command_templates = {
            # File operations
            "list files": "ls -lah {path}",
            "show files": "ls -lah {path}",
            "list directory": "ls -lah {path}",
            "view file": "cat {file}",
            "show file": "cat {file}",
            "read file": "cat {file}",
            "file contents": "cat {file}",

            # File search
            "find file": "find {path} -name {pattern}",
            "search file": "find {path} -name {pattern}",
            "locate file": "find {path} -name {pattern}",
            "search in files": "grep -r {pattern} {path}",
            "find text": "grep -r {pattern} {path}",

            # File manipulation
            "copy file": "cp {source} {dest}",
            "move file": "mv {source} {dest}",
            "rename file": "mv {source} {dest}",
            "delete file": "rm {file}",
            "remove file": "rm {file}",
            "create directory": "mkdir -p {path}",
            "make directory": "mkdir -p {path}",
            "create file": "touch {file}",

            # Directory navigation
            "change directory": "cd {path}",
            "go to directory": "cd {path}",
            "navigate to": "cd {path}",
            "current directory": "pwd",
            "where am i": "pwd",

            # System info
            "who am i": "whoami",
            "current user": "whoami",
            "hostname": "hostname",
            "system info": "uname -a",
            "disk space": "df -h",
            "disk usage": "du -sh {path}",
            "memory usage": "free -h",

            # Process management
            "list processes": "ps aux",
            "show processes": "ps aux",
            "kill process": "kill {pid}",
            "process tree": "pstree",

            # Network operations
            "ping host": "ping -c 4 {host}",
            "check network": "ping -c 4 8.8.8.8",
            "download file": "wget {url}",
            "fetch url": "curl {url}",

            # Git operations
            "git status": "git status",
            "git commit": "git commit -m {message}",
            "git push": "git push",
            "git pull": "git pull",
            "git log": "git log --oneline -10",
        }

    def _init_entity_patterns(self):
        """Initialize entity extraction patterns"""
        self.entity_patterns = {
            EntityType.FILE_PATH: [
                r'(?:^|\s)((?:[~/]|\.{1,2})?(?:[a-zA-Z0-9_\-./]+)+)',
                r'(?:^|\s)(["\'](?:[^"\']+)["\'])',
            ],
            EntityType.FILE_PATTERN: [
                r'\*\.[a-zA-Z0-9]+',
                r'\*[a-zA-Z0-9_\-]*\*',
            ],
            EntityType.COMMAND: [
                r'\b(ls|cd|pwd|cat|grep|find|cp|mv|rm|mkdir|touch|chmod|chown)\b',
                r'\b(git|docker|npm|pip|apt|brew)\b',
            ],
            EntityType.FLAG: [
                r'-[a-zA-Z]+',
                r'--[a-zA-Z\-]+',
            ],
            EntityType.URL: [
                r'https?://[^\s]+',
            ],
            EntityType.IP_ADDRESS: [
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            ],
            EntityType.NUMBER: [
                r'\b\d+\b',
            ],
        }

    async def analyze_intent(self, text: str, context: Optional[NLPContext] = None) -> Intent:
        """
        Analyze user input and determine intent

        Args:
            text: Natural language input
            context: Optional context for analysis

        Returns:
            Intent object with confidence and entities
        """
        self.total_processed += 1

        if context:
            self.context = context

        # Update context
        self.context.conversation_history.append({
            'role': 'user',
            'content': text,
            'timestamp': asyncio.get_event_loop().time()
        })

        text_lower = text.lower().strip()

        # Check for empty input
        if not text_lower:
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                requires_clarification=True,
                clarification_question="What would you like me to do?"
            )

        # Try pattern-based recognition first
        pattern_intent = self._pattern_based_recognition(text_lower)

        # Extract entities
        entities = self._extract_entities(text)

        # If we have LLM, use it for advanced understanding
        if self.llm_manager and pattern_intent.confidence < 0.7:
            try:
                llm_intent = await self._llm_based_recognition(text, pattern_intent, entities)
                if llm_intent.confidence > pattern_intent.confidence:
                    pattern_intent = llm_intent
            except Exception as e:
                logger.warning(f"LLM-based recognition failed: {e}")

        # Add extracted entities
        pattern_intent.entities = entities

        # Generate command suggestion if applicable
        if self._is_command_intent(pattern_intent.type):
            command = self._translate_to_command(text_lower, pattern_intent, entities)
            pattern_intent.suggested_command = command

            # Generate alternatives
            alternatives = self._generate_alternatives(text_lower, pattern_intent, entities)
            pattern_intent.alternatives = alternatives

        # Update context
        self.context.last_intent = pattern_intent

        return pattern_intent

    def _pattern_based_recognition(self, text: str) -> Intent:
        """
        Recognize intent using pattern matching

        Args:
            text: Normalized text

        Returns:
            Intent with confidence score
        """
        best_match = (IntentType.UNKNOWN, 0.0)

        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Calculate confidence based on pattern specificity
                    confidence = min(0.9, 0.6 + (len(pattern) / 200))
                    if confidence > best_match[1]:
                        best_match = (intent_type, confidence)

        return Intent(
            type=best_match[0],
            confidence=best_match[1],
            metadata={'method': 'pattern_matching'}
        )

    async def _llm_based_recognition(
        self,
        text: str,
        fallback_intent: Intent,
        entities: List[Entity]
    ) -> Intent:
        """
        Use LLM for advanced intent recognition

        Args:
            text: Original text
            fallback_intent: Fallback intent from pattern matching
            entities: Extracted entities

        Returns:
            Enhanced intent
        """
        # Build prompt for LLM
        prompt = self._build_intent_prompt(text, self.context)

        # Get LLM response
        from src.llm.model_registry import TaskType
        response = await self.llm_manager.generate_with_routing(
            prompt=prompt,
            task_type=TaskType.GENERAL,
            max_tokens=200,
            temperature=0.3
        )

        # Parse response
        intent = self._parse_llm_intent_response(response, entities)
        return intent

    def _build_intent_prompt(self, text: str, context: NLPContext) -> str:
        """Build prompt for LLM intent recognition"""
        recent_commands = "\n".join(context.command_history[-5:]) if context.command_history else "None"

        prompt = f"""Analyze this user input and determine their intent:

User input: "{text}"

Current directory: {context.current_directory}
Recent commands:
{recent_commands}

Classify the intent as one of:
- file_operation (viewing, listing files)
- directory_nav (changing directories)
- file_search (finding files)
- file_manipulation (copying, moving, deleting)
- system_info (system information)
- process_mgmt (managing processes)
- network_ops (network operations)
- package_mgmt (installing packages)
- version_control (git operations)
- information_query (asking what/how questions)
- help_request (asking for help)
- explanation (asking for explanations)
- conversation (general chat)
- unknown (cannot determine)

Respond with JSON:
{{
  "intent": "intent_type",
  "confidence": 0.0-1.0,
  "reasoning": "why you chose this intent"
}}"""
        return prompt

    def _parse_llm_intent_response(self, response: str, entities: List[Entity]) -> Intent:
        """Parse LLM response into Intent object"""
        import json

        try:
            # Extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response

            data = json.loads(json_str)

            intent_type = IntentType[data['intent'].upper()]
            confidence = float(data['confidence'])

            return Intent(
                type=intent_type,
                confidence=confidence,
                entities=entities,
                metadata={
                    'method': 'llm',
                    'reasoning': data.get('reasoning', '')
                }
            )
        except Exception as e:
            logger.warning(f"Failed to parse LLM intent response: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                entities=entities
            )

    def _extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        entities = []

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity = Entity(
                        type=entity_type,
                        value=match.group().strip(),
                        confidence=0.8,
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)

        # Remove duplicates and sort by position
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda e: e.start_pos)

        return entities

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities, keeping highest confidence"""
        seen = {}
        for entity in entities:
            key = (entity.type, entity.value)
            if key not in seen or entity.confidence > seen[key].confidence:
                seen[key] = entity
        return list(seen.values())

    def _is_command_intent(self, intent_type: IntentType) -> bool:
        """Check if intent requires command translation"""
        command_intents = {
            IntentType.FILE_OPERATION,
            IntentType.DIRECTORY_NAV,
            IntentType.FILE_SEARCH,
            IntentType.FILE_MANIPULATION,
            IntentType.SYSTEM_INFO,
            IntentType.PROCESS_MGMT,
            IntentType.NETWORK_OPS,
            IntentType.PACKAGE_MGMT,
            IntentType.VERSION_CONTROL,
        }
        return intent_type in command_intents

    def _translate_to_command(
        self,
        text: str,
        intent: Intent,
        entities: List[Entity]
    ) -> Optional[str]:
        """
        Translate natural language to shell command

        Args:
            text: Natural language text
            intent: Recognized intent
            entities: Extracted entities

        Returns:
            Shell command or None
        """
        # Find matching template
        best_match = None
        best_score = 0.0

        for template_key, template_cmd in self.command_templates.items():
            score = self._calculate_similarity(text, template_key)
            if score > best_score:
                best_score = score
                best_match = (template_key, template_cmd)

        if not best_match or best_score < 0.3:
            return None

        # Fill template with entities
        command = best_match[1]
        command = self._fill_command_template(command, text, entities)

        self.successful_translations += 1
        return command

    def _fill_command_template(
        self,
        template: str,
        text: str,
        entities: List[Entity]
    ) -> str:
        """Fill command template with extracted entities"""
        # Extract placeholders from template
        placeholders = re.findall(r'\{(\w+)\}', template)

        filled = template
        for placeholder in placeholders:
            value = self._find_entity_for_placeholder(placeholder, text, entities)
            if value:
                filled = filled.replace(f"{{{placeholder}}}", value)
            else:
                # Use sensible defaults
                defaults = {
                    'path': '.',
                    'file': '',
                    'pattern': '*',
                    'source': '',
                    'dest': '',
                    'host': '',
                    'url': '',
                    'pid': '',
                    'message': '""',
                }
                filled = filled.replace(f"{{{placeholder}}}", defaults.get(placeholder, ''))

        return filled.strip()

    def _find_entity_for_placeholder(
        self,
        placeholder: str,
        text: str,
        entities: List[Entity]
    ) -> Optional[str]:
        """Find appropriate entity value for placeholder"""
        placeholder_mapping = {
            'path': [EntityType.FILE_PATH, EntityType.DIRECTORY],
            'file': [EntityType.FILE_PATH],
            'pattern': [EntityType.FILE_PATTERN],
            'source': [EntityType.FILE_PATH],
            'dest': [EntityType.FILE_PATH],
            'host': [EntityType.IP_ADDRESS, EntityType.URL],
            'url': [EntityType.URL],
            'pid': [EntityType.NUMBER],
            'message': [EntityType.STRING_LITERAL],
        }

        valid_types = placeholder_mapping.get(placeholder, [])

        for entity in entities:
            if entity.type in valid_types:
                return entity.value

        # If no entity found, try to extract from text
        return self._extract_placeholder_from_text(placeholder, text)

    def _extract_placeholder_from_text(self, placeholder: str, text: str) -> Optional[str]:
        """Extract placeholder value directly from text"""
        # Look for quoted strings
        if placeholder == 'message':
            quoted = re.findall(r'["\']([^"\']+)["\']', text)
            if quoted:
                return f'"{quoted[0]}"'

        # Look for file extensions
        if placeholder == 'pattern':
            extensions = re.findall(r'\b(\w+)\s+files?\b', text)
            if extensions:
                return f'*.{extensions[0]}'

        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _generate_alternatives(
        self,
        text: str,
        intent: Intent,
        entities: List[Entity]
    ) -> List[str]:
        """Generate alternative command interpretations"""
        alternatives = []

        # Find similar templates
        for template_key, template_cmd in self.command_templates.items():
            score = self._calculate_similarity(text, template_key)
            if 0.3 <= score < 0.7:  # Similar but not best match
                cmd = self._fill_command_template(template_cmd, text, entities)
                if cmd and cmd != intent.suggested_command:
                    alternatives.append(cmd)

        return alternatives[:3]  # Return top 3 alternatives

    async def translate_command(
        self,
        text: str,
        context: Optional[NLPContext] = None
    ) -> Dict[str, Any]:
        """
        Translate natural language to shell command

        Args:
            text: Natural language input
            context: Optional context

        Returns:
            Dictionary with command, confidence, and alternatives
        """
        intent = await self.analyze_intent(text, context)

        return {
            'intent': intent.type.value,
            'command': intent.suggested_command,
            'confidence': intent.confidence,
            'alternatives': intent.alternatives,
            'entities': [
                {
                    'type': e.type.value,
                    'value': e.value,
                    'confidence': e.confidence
                }
                for e in intent.entities
            ],
            'requires_clarification': intent.requires_clarification,
            'clarification_question': intent.clarification_question
        }

    def update_context(self, **kwargs):
        """Update NLP context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        success_rate = (
            self.successful_translations / self.total_processed
            if self.total_processed > 0 else 0.0
        )

        return {
            'total_processed': self.total_processed,
            'successful_translations': self.successful_translations,
            'success_rate': success_rate,
            'context_size': len(self.context.conversation_history),
            'llm_available': self.llm_manager is not None
        }
