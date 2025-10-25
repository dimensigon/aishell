"""
Conversation Manager for AI Query Assistant

Maintains conversation context and history for multi-turn interactions.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class Conversation:
    """A conversation session with the AI assistant"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get recent messages from conversation"""
        return self.messages[-count:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary"""
        return {
            'session_id': self.session_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


class ConversationManager:
    """
    Manages conversation context for AI query assistant

    Features:
    - Maintains conversation history
    - Provides context for multi-turn interactions
    - Tracks query patterns and user preferences
    - Supports conversation persistence
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize conversation manager

        Args:
            max_history: Maximum number of messages to keep in memory
        """
        self.max_history = max_history
        self.conversations: Dict[str, Conversation] = {}
        self.current_session: Optional[str] = None

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new conversation session

        Args:
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        conversation = Conversation(session_id=session_id)
        self.conversations[session_id] = conversation
        self.current_session = session_id

        logger.info(f"Started new conversation session: {session_id}")
        return session_id

    def add_user_message(
        self,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Add user message to conversation"""
        sid = session_id or self.current_session
        if not sid or sid not in self.conversations:
            sid = self.start_session(sid)

        self.conversations[sid].add_message('user', content, metadata)
        self._trim_conversation(sid)

    def add_assistant_message(
        self,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Add assistant message to conversation"""
        sid = session_id or self.current_session
        if not sid or sid not in self.conversations:
            logger.warning("No active session, creating new one")
            sid = self.start_session(sid)

        self.conversations[sid].add_message('assistant', content, metadata)
        self._trim_conversation(sid)

    def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        count: Optional[int] = None
    ) -> List[Message]:
        """
        Get conversation history

        Args:
            session_id: Session ID (uses current session if None)
            count: Number of recent messages to retrieve

        Returns:
            List of messages
        """
        sid = session_id or self.current_session
        if not sid or sid not in self.conversations:
            return []

        conversation = self.conversations[sid]
        if count:
            return conversation.get_recent_messages(count)
        return conversation.messages

    def get_context_for_api(
        self,
        session_id: Optional[str] = None,
        message_count: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for API calls

        Args:
            session_id: Session ID
            message_count: Number of recent messages

        Returns:
            List of message dicts with 'role' and 'content'
        """
        messages = self.get_conversation_history(session_id, message_count)
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
        ]

    def clear_session(self, session_id: Optional[str] = None):
        """Clear conversation session"""
        sid = session_id or self.current_session
        if sid and sid in self.conversations:
            del self.conversations[sid]
            if self.current_session == sid:
                self.current_session = None
            logger.info(f"Cleared conversation session: {sid}")

    def save_conversation(
        self,
        filepath: str,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Save conversation to file

        Args:
            filepath: Path to save conversation
            session_id: Session ID to save

        Returns:
            True if successful
        """
        sid = session_id or self.current_session
        if not sid or sid not in self.conversations:
            logger.error("No conversation to save")
            return False

        try:
            conversation = self.conversations[sid]
            with open(filepath, 'w') as f:
                json.dump(conversation.to_dict(), f, indent=2)

            logger.info(f"Saved conversation to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False

    def load_conversation(self, filepath: str) -> Optional[str]:
        """
        Load conversation from file

        Args:
            filepath: Path to conversation file

        Returns:
            Session ID if successful, None otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            session_id = data['session_id']
            conversation = Conversation(
                session_id=session_id,
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at']),
                metadata=data.get('metadata', {})
            )

            # Restore messages
            for msg_data in data['messages']:
                message = Message(
                    role=msg_data['role'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['timestamp']),
                    metadata=msg_data.get('metadata', {})
                )
                conversation.messages.append(message)

            self.conversations[session_id] = conversation
            self.current_session = session_id

            logger.info(f"Loaded conversation from {filepath}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return None

    def get_conversation_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of conversation

        Args:
            session_id: Session ID

        Returns:
            Dictionary with conversation summary
        """
        sid = session_id or self.current_session
        if not sid or sid not in self.conversations:
            return {}

        conversation = self.conversations[sid]
        messages = conversation.messages

        user_messages = [m for m in messages if m.role == 'user']
        assistant_messages = [m for m in messages if m.role == 'assistant']

        return {
            'session_id': sid,
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'duration_minutes': (conversation.updated_at - conversation.created_at).total_seconds() / 60
        }

    def _trim_conversation(self, session_id: str):
        """Trim conversation to max_history limit"""
        if session_id not in self.conversations:
            return

        conversation = self.conversations[session_id]
        if len(conversation.messages) > self.max_history:
            # Keep most recent messages
            conversation.messages = conversation.messages[-self.max_history:]
            logger.debug(f"Trimmed conversation {session_id} to {self.max_history} messages")
