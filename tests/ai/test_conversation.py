"""
Comprehensive tests for Conversation Manager

Tests conversation context, history management, and persistence.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
import json
import tempfile
import os

from src.ai.conversation_manager import (
    ConversationManager,
    Conversation,
    Message
)


class TestMessageDataclass:
    """Test Message dataclass"""

    def test_message_creation(self):
        """Test creating a message"""
        msg = Message(
            role="user",
            content="Hello",
            metadata={"intent": "greeting"}
        )

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {"intent": "greeting"}
        assert isinstance(msg.timestamp, datetime)

    def test_message_to_dict(self):
        """Test message serialization"""
        msg = Message(role="assistant", content="Hi there")
        result = msg.to_dict()

        assert result['role'] == "assistant"
        assert result['content'] == "Hi there"
        assert 'timestamp' in result
        assert 'metadata' in result


class TestConversationDataclass:
    """Test Conversation dataclass"""

    def test_conversation_creation(self):
        """Test creating a conversation"""
        conv = Conversation(session_id="test-123")

        assert conv.session_id == "test-123"
        assert conv.messages == []
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)

    def test_add_message(self):
        """Test adding messages to conversation"""
        conv = Conversation(session_id="test")

        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi", metadata={"model": "claude"})

        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[1].metadata == {"model": "claude"}

    def test_add_message_updates_timestamp(self):
        """Test adding message updates conversation timestamp"""
        conv = Conversation(session_id="test")
        original_time = conv.updated_at

        # Add message
        conv.add_message("user", "test")

        assert conv.updated_at > original_time

    def test_get_recent_messages(self):
        """Test retrieving recent messages"""
        conv = Conversation(session_id="test")

        # Add 15 messages
        for i in range(15):
            conv.add_message("user", f"Message {i}")

        recent = conv.get_recent_messages(count=5)

        assert len(recent) == 5
        assert recent[0].content == "Message 10"
        assert recent[4].content == "Message 14"

    def test_get_recent_messages_less_than_count(self):
        """Test getting recent when fewer messages exist"""
        conv = Conversation(session_id="test")

        conv.add_message("user", "Message 1")
        conv.add_message("user", "Message 2")

        recent = conv.get_recent_messages(count=10)

        assert len(recent) == 2

    def test_conversation_to_dict(self):
        """Test conversation serialization"""
        conv = Conversation(session_id="test-123")
        conv.add_message("user", "Hello")

        result = conv.to_dict()

        assert result['session_id'] == "test-123"
        assert len(result['messages']) == 1
        assert 'created_at' in result
        assert 'updated_at' in result
        assert 'metadata' in result


class TestConversationManagerInitialization:
    """Test ConversationManager initialization"""

    def test_init_default_values(self):
        """Test initialization with defaults"""
        manager = ConversationManager()

        assert manager.max_history == 50
        assert manager.conversations == {}
        assert manager.current_session is None

    def test_init_custom_max_history(self):
        """Test initialization with custom max_history"""
        manager = ConversationManager(max_history=100)

        assert manager.max_history == 100


class TestSessionManagement:
    """Test conversation session management"""

    def test_start_session_default_id(self):
        """Test starting session with auto-generated ID"""
        manager = ConversationManager()

        session_id = manager.start_session()

        assert session_id is not None
        assert session_id.startswith("session_")
        assert session_id in manager.conversations
        assert manager.current_session == session_id

    def test_start_session_custom_id(self):
        """Test starting session with custom ID"""
        manager = ConversationManager()

        session_id = manager.start_session("my-custom-id")

        assert session_id == "my-custom-id"
        assert session_id in manager.conversations
        assert manager.current_session == "my-custom-id"

    def test_start_multiple_sessions(self):
        """Test starting multiple sessions"""
        manager = ConversationManager()

        sid1 = manager.start_session("session1")
        sid2 = manager.start_session("session2")

        assert len(manager.conversations) == 2
        assert manager.current_session == "session2"

    def test_clear_session_by_id(self):
        """Test clearing specific session"""
        manager = ConversationManager()

        sid = manager.start_session("test")
        manager.add_user_message("Hello", sid)

        manager.clear_session(sid)

        assert sid not in manager.conversations
        assert manager.current_session is None

    def test_clear_current_session(self):
        """Test clearing current session"""
        manager = ConversationManager()

        manager.start_session()
        manager.clear_session()

        assert len(manager.conversations) == 0
        assert manager.current_session is None

    def test_clear_session_preserves_others(self):
        """Test clearing one session doesn't affect others"""
        manager = ConversationManager()

        sid1 = manager.start_session("session1")
        sid2 = manager.start_session("session2")

        manager.clear_session(sid1)

        assert sid1 not in manager.conversations
        assert sid2 in manager.conversations


class TestMessageManagement:
    """Test message management"""

    def test_add_user_message_to_current_session(self):
        """Test adding user message to current session"""
        manager = ConversationManager()
        sid = manager.start_session()

        manager.add_user_message("Hello")

        messages = manager.get_conversation_history()
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"

    def test_add_user_message_to_specific_session(self):
        """Test adding user message to specific session"""
        manager = ConversationManager()

        sid1 = manager.start_session("session1")
        sid2 = manager.start_session("session2")

        manager.add_user_message("Message 1", session_id=sid1)
        manager.add_user_message("Message 2", session_id=sid2)

        messages1 = manager.get_conversation_history(sid1)
        messages2 = manager.get_conversation_history(sid2)

        assert len(messages1) == 1
        assert len(messages2) == 1
        assert messages1[0].content == "Message 1"
        assert messages2[0].content == "Message 2"

    def test_add_user_message_auto_creates_session(self):
        """Test adding message auto-creates session if none exists"""
        manager = ConversationManager()

        manager.add_user_message("Hello")

        assert manager.current_session is not None
        assert len(manager.conversations) == 1

    def test_add_user_message_with_metadata(self):
        """Test adding user message with metadata"""
        manager = ConversationManager()
        manager.start_session()

        manager.add_user_message("Test", metadata={"intent": "query"})

        messages = manager.get_conversation_history()
        assert messages[0].metadata == {"intent": "query"}

    def test_add_assistant_message(self):
        """Test adding assistant message"""
        manager = ConversationManager()
        manager.start_session()

        manager.add_assistant_message("Hello!", metadata={"model": "claude"})

        messages = manager.get_conversation_history()
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Hello!"

    def test_add_assistant_message_auto_creates_session(self):
        """Test assistant message auto-creates session"""
        manager = ConversationManager()

        manager.add_assistant_message("Response")

        assert len(manager.conversations) == 1
        messages = manager.get_conversation_history()
        assert messages[0].role == "assistant"

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation"""
        manager = ConversationManager()
        manager.start_session()

        manager.add_user_message("What is Python?")
        manager.add_assistant_message("Python is a programming language.")
        manager.add_user_message("Tell me more")
        manager.add_assistant_message("It's widely used for web dev and data science.")

        messages = manager.get_conversation_history()

        assert len(messages) == 4
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[2].role == "user"
        assert messages[3].role == "assistant"


class TestHistoryRetrieval:
    """Test conversation history retrieval"""

    def test_get_conversation_history_no_session(self):
        """Test getting history when no session exists"""
        manager = ConversationManager()

        messages = manager.get_conversation_history()

        assert messages == []

    def test_get_conversation_history_with_count(self):
        """Test getting limited history"""
        manager = ConversationManager()
        sid = manager.start_session()

        for i in range(10):
            manager.add_user_message(f"Message {i}", sid)

        messages = manager.get_conversation_history(sid, count=3)

        assert len(messages) == 3
        assert messages[0].content == "Message 7"
        assert messages[2].content == "Message 9"

    def test_get_context_for_api(self):
        """Test getting context formatted for API calls"""
        manager = ConversationManager()
        manager.start_session()

        manager.add_user_message("Hello")
        manager.add_assistant_message("Hi")
        manager.add_user_message("How are you?")

        context = manager.get_context_for_api()

        assert len(context) == 3
        assert all('role' in msg and 'content' in msg for msg in context)
        assert context[0] == {'role': 'user', 'content': 'Hello'}
        assert context[1] == {'role': 'assistant', 'content': 'Hi'}

    def test_get_context_for_api_with_limit(self):
        """Test getting limited context for API"""
        manager = ConversationManager()
        manager.start_session()

        for i in range(15):
            manager.add_user_message(f"Message {i}")

        context = manager.get_context_for_api(message_count=5)

        assert len(context) == 5

    def test_get_context_for_api_specific_session(self):
        """Test getting context for specific session"""
        manager = ConversationManager()

        sid1 = manager.start_session("session1")
        sid2 = manager.start_session("session2")

        manager.add_user_message("Session 1 message", sid1)
        manager.add_user_message("Session 2 message", sid2)

        context1 = manager.get_context_for_api(sid1)
        context2 = manager.get_context_for_api(sid2)

        assert len(context1) == 1
        assert len(context2) == 1
        assert context1[0]['content'] == "Session 1 message"
        assert context2[0]['content'] == "Session 2 message"


class TestConversationSummary:
    """Test conversation summary generation"""

    def test_get_conversation_summary_no_session(self):
        """Test getting summary when no session exists"""
        manager = ConversationManager()

        summary = manager.get_conversation_summary()

        assert summary == {}

    def test_get_conversation_summary(self):
        """Test getting conversation summary"""
        manager = ConversationManager()
        sid = manager.start_session()

        manager.add_user_message("Question 1", sid)
        manager.add_assistant_message("Answer 1", sid)
        manager.add_user_message("Question 2", sid)
        manager.add_assistant_message("Answer 2", sid)

        summary = manager.get_conversation_summary(sid)

        assert summary['session_id'] == sid
        assert summary['total_messages'] == 4
        assert summary['user_messages'] == 2
        assert summary['assistant_messages'] == 2
        assert 'created_at' in summary
        assert 'updated_at' in summary
        assert 'duration_minutes' in summary
        assert summary['duration_minutes'] >= 0


class TestHistoryTrimming:
    """Test conversation history trimming"""

    def test_trim_conversation_on_max_limit(self):
        """Test conversation is trimmed when exceeding max_history"""
        manager = ConversationManager(max_history=10)
        sid = manager.start_session()

        # Add 15 messages
        for i in range(15):
            manager.add_user_message(f"Message {i}", sid)

        messages = manager.get_conversation_history(sid)

        # Should only keep last 10
        assert len(messages) == 10
        assert messages[0].content == "Message 5"
        assert messages[9].content == "Message 14"

    def test_trim_preserves_recent_messages(self):
        """Test trimming preserves most recent messages"""
        manager = ConversationManager(max_history=5)
        sid = manager.start_session()

        for i in range(10):
            manager.add_user_message(f"Message {i}", sid)

        messages = manager.get_conversation_history(sid)

        # Should have messages 5-9
        assert all(int(msg.content.split()[-1]) >= 5 for msg in messages)


class TestConversationPersistence:
    """Test conversation save/load functionality"""

    def test_save_conversation_success(self):
        """Test saving conversation to file"""
        manager = ConversationManager()
        sid = manager.start_session("test-save")
        manager.add_user_message("Test message", sid)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            result = manager.save_conversation(filepath, sid)

            assert result is True
            assert os.path.exists(filepath)

            # Verify file contents
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert data['session_id'] == "test-save"
            assert len(data['messages']) == 1

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_save_conversation_no_session(self):
        """Test saving non-existent conversation"""
        manager = ConversationManager()

        result = manager.save_conversation("test.json", "non-existent")

        assert result is False

    def test_save_conversation_current_session(self):
        """Test saving current session without specifying ID"""
        manager = ConversationManager()
        manager.start_session()
        manager.add_user_message("Test")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            result = manager.save_conversation(filepath)

            assert result is True
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_load_conversation_success(self):
        """Test loading conversation from file"""
        manager = ConversationManager()

        # Create test conversation data
        conversation_data = {
            'session_id': 'loaded-session',
            'messages': [
                {
                    'role': 'user',
                    'content': 'Hello',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {}
                }
            ],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': {}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(conversation_data, f)
            filepath = f.name

        try:
            session_id = manager.load_conversation(filepath)

            assert session_id == 'loaded-session'
            assert session_id in manager.conversations
            assert manager.current_session == session_id

            messages = manager.get_conversation_history(session_id)
            assert len(messages) == 1
            assert messages[0].content == 'Hello'

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_load_conversation_invalid_file(self):
        """Test loading from non-existent file"""
        manager = ConversationManager()

        result = manager.load_conversation("non-existent.json")

        assert result is None

    def test_load_conversation_invalid_json(self):
        """Test loading invalid JSON file"""
        manager = ConversationManager()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("invalid json {")
            filepath = f.name

        try:
            result = manager.load_conversation(filepath)

            assert result is None

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_save_and_load_roundtrip(self):
        """Test saving and loading preserves conversation"""
        manager1 = ConversationManager()
        sid = manager1.start_session("roundtrip-test")

        manager1.add_user_message("Question 1", sid)
        manager1.add_assistant_message("Answer 1", sid)
        manager1.add_user_message("Question 2", sid)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            # Save
            manager1.save_conversation(filepath, sid)

            # Load into new manager
            manager2 = ConversationManager()
            loaded_sid = manager2.load_conversation(filepath)

            # Verify
            original_messages = manager1.get_conversation_history(sid)
            loaded_messages = manager2.get_conversation_history(loaded_sid)

            assert len(original_messages) == len(loaded_messages)
            for orig, loaded in zip(original_messages, loaded_messages):
                assert orig.role == loaded.role
                assert orig.content == loaded.content

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_multiple_concurrent_sessions(self):
        """Test managing multiple concurrent sessions"""
        manager = ConversationManager()

        # Create multiple sessions
        sessions = []
        for i in range(5):
            sid = manager.start_session(f"user-{i}")
            sessions.append(sid)
            manager.add_user_message(f"Hello from user {i}", sid)

        # Verify all sessions exist and are independent
        assert len(manager.conversations) == 5

        for i, sid in enumerate(sessions):
            messages = manager.get_conversation_history(sid)
            assert len(messages) == 1
            assert f"user {i}" in messages[0].content

    def test_long_conversation_with_trimming(self):
        """Test long conversation with automatic trimming"""
        manager = ConversationManager(max_history=20)
        sid = manager.start_session()

        # Simulate long conversation
        for i in range(50):
            manager.add_user_message(f"User message {i}", sid)
            manager.add_assistant_message(f"Assistant response {i}", sid)

        messages = manager.get_conversation_history(sid)

        # Should be trimmed to 20
        assert len(messages) == 20
        # Should contain most recent messages
        assert "message 40" in messages[0].content or "response 40" in messages[0].content

    def test_conversation_analytics(self):
        """Test gathering conversation analytics"""
        manager = ConversationManager()
        sid = manager.start_session()

        # Simulate conversation
        for i in range(10):
            manager.add_user_message(f"Question {i}", sid)
            manager.add_assistant_message(f"Answer {i}", sid)

        summary = manager.get_conversation_summary(sid)

        assert summary['total_messages'] == 20
        assert summary['user_messages'] == 10
        assert summary['assistant_messages'] == 10
        assert summary['duration_minutes'] >= 0
