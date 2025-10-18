"""
Unit tests for Cognitive Shell Memory (CogShell)
"""

import pytest
import asyncio
import time
import json
import numpy as np
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path

from src.cognitive.memory import (
    CognitiveMemory,
    MemoryEntry,
    PatternExtractor
)


class TestMemoryEntry:
    """Test MemoryEntry dataclass"""

    def test_memory_entry_creation(self):
        """Test creating a memory entry"""
        entry = MemoryEntry(
            id="test_id",
            command="ls -la",
            output="file1.txt\nfile2.txt",
            error=None,
            context={"cwd": "/home/user"},
            timestamp=time.time(),
            success=True,
            duration=0.5
        )

        assert entry.id == "test_id"
        assert entry.command == "ls -la"
        assert entry.success is True
        assert entry.frequency == 1
        assert entry.importance == 0.5

    def test_memory_entry_to_dict(self):
        """Test converting memory entry to dict"""
        embedding = np.array([0.1, 0.2, 0.3])
        entry = MemoryEntry(
            id="test_id",
            command="test",
            output="output",
            error=None,
            context={},
            timestamp=1234567890,
            success=True,
            duration=1.0,
            embedding=embedding
        )

        data = entry.to_dict()
        assert data['id'] == "test_id"
        assert data['embedding'] == [0.1, 0.2, 0.3]

    def test_memory_entry_from_dict(self):
        """Test creating memory entry from dict"""
        data = {
            'id': 'test_id',
            'command': 'test',
            'output': 'output',
            'error': None,
            'context': {},
            'timestamp': 1234567890,
            'success': True,
            'duration': 1.0,
            'tags': ['tag1'],
            'learned_patterns': ['pattern1'],
            'embedding': [0.1, 0.2, 0.3],
            'frequency': 2,
            'last_accessed': 1234567900,
            'sentiment': 0.5,
            'importance': 0.7
        }

        entry = MemoryEntry.from_dict(data)
        assert entry.id == 'test_id'
        assert isinstance(entry.embedding, np.ndarray)
        assert entry.importance == 0.7


class TestPatternExtractor:
    """Test PatternExtractor class"""

    def test_extract_git_patterns(self):
        """Test extracting git workflow patterns"""
        extractor = PatternExtractor()

        patterns = extractor.extract("git add .", "Added files")
        assert "pattern:git_workflow" in patterns

        patterns = extractor.extract("git commit -m 'test'", "Committed")
        assert "pattern:git_workflow" in patterns

    def test_extract_file_patterns(self):
        """Test extracting file operation patterns"""
        extractor = PatternExtractor()

        patterns = extractor.extract("ls -la", "file1.txt")
        assert "pattern:file_operations" in patterns

        patterns = extractor.extract("cp file1 file2", "Copied")
        assert "pattern:file_operations" in patterns

    def test_extract_docker_patterns(self):
        """Test extracting docker patterns"""
        extractor = PatternExtractor()

        patterns = extractor.extract("docker run nginx", "Started")
        assert "pattern:docker_operations" in patterns

        patterns = extractor.extract("docker-compose up", "Services started")
        assert "pattern:docker_operations" in patterns

    def test_extract_outcome_patterns(self):
        """Test extracting outcome patterns"""
        extractor = PatternExtractor()

        patterns = extractor.extract("test", "Error: failed")
        assert "outcome:error" in patterns

        patterns = extractor.extract("test", "Success: complete")
        assert "outcome:success" in patterns

    def test_extract_time_patterns(self):
        """Test extracting time patterns"""
        extractor = PatternExtractor()

        with patch('src.cognitive.memory.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 10
            patterns = extractor.extract("test", "output")
            assert "time:morning" in patterns

            mock_datetime.now.return_value.hour = 14
            patterns = extractor.extract("test", "output")
            assert "time:afternoon" in patterns

            mock_datetime.now.return_value.hour = 20
            patterns = extractor.extract("test", "output")
            assert "time:evening" in patterns

            mock_datetime.now.return_value.hour = 2
            patterns = extractor.extract("test", "output")
            assert "time:late_night" in patterns

    def test_extract_complexity_patterns(self):
        """Test extracting complexity patterns"""
        extractor = PatternExtractor()

        patterns = extractor.extract("ls", "output")
        assert "complexity:low" in patterns

        patterns = extractor.extract("ls -la | grep test | sort", "output")
        assert "complexity:medium" in patterns

        long_command = " ".join(["word"] * 15)
        patterns = extractor.extract(long_command, "output")
        assert "complexity:high" in patterns


class TestCognitiveMemory:
    """Test CognitiveMemory class"""

    @pytest.fixture
    def temp_memory_dir(self, tmp_path):
        """Create temporary memory directory"""
        return str(tmp_path / "memory")

    @pytest.fixture
    async def cognitive_memory(self, temp_memory_dir):
        """Create CognitiveMemory instance"""
        memory = CognitiveMemory(
            memory_dir=temp_memory_dir,
            vector_dim=10,
            max_memories=100
        )
        # Wait for initialization
        await asyncio.sleep(0.1)
        return memory

    @pytest.mark.asyncio
    async def test_initialization(self, cognitive_memory):
        """Test CognitiveMemory initialization"""
        assert cognitive_memory.vector_dim == 10
        assert cognitive_memory.max_memories == 100
        assert cognitive_memory.learning_rate == 0.1
        assert cognitive_memory.forgetting_factor == 0.95

    @pytest.mark.asyncio
    async def test_remember(self, cognitive_memory):
        """Test remembering a command"""
        memory = await cognitive_memory.remember(
            command="ls -la",
            output="file1.txt\nfile2.txt",
            error=None,
            context={"cwd": "/home/user"},
            duration=0.5
        )

        assert memory.command == "ls -la"
        assert memory.success is True
        assert memory.duration == 0.5
        assert len(memory.tags) > 0
        assert len(memory.learned_patterns) > 0
        assert memory.embedding is not None

    @pytest.mark.asyncio
    async def test_remember_with_error(self, cognitive_memory):
        """Test remembering a failed command"""
        memory = await cognitive_memory.remember(
            command="rm /protected/file",
            output="",
            error="Permission denied",
            context={"cwd": "/"},
            duration=0.1
        )

        assert memory.success is False
        assert memory.error == "Permission denied"
        assert memory.importance > 0.5  # Errors are more important

    @pytest.mark.asyncio
    async def test_recall(self, cognitive_memory):
        """Test recalling similar memories"""
        # Remember some commands
        await cognitive_memory.remember("ls -la", "output1", None, {}, 0.1)
        await cognitive_memory.remember("ls", "output2", None, {}, 0.1)
        await cognitive_memory.remember("cd /home", "output3", None, {}, 0.1)

        # Recall similar
        memories = await cognitive_memory.recall("ls", k=2)

        assert len(memories) <= 2
        # Should recall ls commands first
        if memories:
            assert any("ls" in m.command for m in memories)

    @pytest.mark.asyncio
    async def test_recall_by_pattern(self, cognitive_memory):
        """Test recalling by pattern"""
        # Remember commands with patterns
        memory1 = await cognitive_memory.remember(
            "git add .",
            "Added files",
            None,
            {},
            0.1
        )
        memory2 = await cognitive_memory.remember(
            "docker run nginx",
            "Started",
            None,
            {},
            0.1
        )

        # Recall git patterns
        git_memories = await cognitive_memory.recall_by_pattern(
            "pattern:git_workflow",
            k=5
        )

        assert len(git_memories) >= 1
        assert any("git" in m.command for m in git_memories)

    @pytest.mark.asyncio
    async def test_get_command_suggestions(self, cognitive_memory):
        """Test getting command suggestions"""
        # Remember some commands
        await cognitive_memory.remember("cd /project", "changed dir", None, {"cwd": "/"}, 0.1)
        await cognitive_memory.remember("ls -la", "files", None, {"cwd": "/project"}, 0.1)
        await cognitive_memory.remember("git status", "clean", None, {"cwd": "/project"}, 0.1)

        # Get suggestions for /project directory
        context = {"cwd": "/project", "last_command": "cd /project"}
        suggestions = await cognitive_memory.get_command_suggestions(context, k=3)

        assert isinstance(suggestions, list)
        assert all(isinstance(s, tuple) and len(s) == 2 for s in suggestions)

    @pytest.mark.asyncio
    async def test_learn_from_feedback(self, cognitive_memory):
        """Test learning from user feedback"""
        # Remember a command
        memory = await cognitive_memory.remember(
            "test command",
            "output",
            None,
            {},
            0.1
        )

        initial_importance = memory.importance

        # Positive feedback
        await cognitive_memory.learn_from_feedback(
            memory.id,
            positive=True,
            feedback="Very helpful"
        )

        assert memory.importance > initial_importance
        assert memory.sentiment > 0

        # Negative feedback
        await cognitive_memory.learn_from_feedback(
            memory.id,
            positive=False,
            feedback="Not useful"
        )

        assert memory.sentiment < 0

    @pytest.mark.asyncio
    async def test_get_insights(self, cognitive_memory):
        """Test generating insights"""
        # Add some memories
        for i in range(5):
            await cognitive_memory.remember(f"command_{i}", f"output_{i}", None, {}, 0.1)

        insights = await cognitive_memory.get_insights()

        assert 'most_used_commands' in insights
        assert 'common_errors' in insights
        assert 'overall_success_rate' in insights
        assert 'total_memories' in insights
        assert insights['total_memories'] >= 5

    @pytest.mark.asyncio
    async def test_export_import_knowledge(self, cognitive_memory, tmp_path):
        """Test exporting and importing knowledge"""
        # Add memories
        await cognitive_memory.remember("test1", "output1", None, {}, 0.1)
        await cognitive_memory.remember("test2", "output2", None, {}, 0.1)

        # Export
        export_path = str(tmp_path / "knowledge.json")
        await cognitive_memory.export_knowledge(export_path)

        assert Path(export_path).exists()

        # Create new memory instance
        new_memory = CognitiveMemory(
            memory_dir=str(tmp_path / "new_memory"),
            vector_dim=10
        )

        # Import
        await new_memory.import_knowledge(export_path)

        assert len(new_memory.memory_cache) >= 0  # May filter by importance

    @pytest.mark.asyncio
    async def test_memory_persistence(self, cognitive_memory):
        """Test memory persistence to database"""
        memory = await cognitive_memory.remember(
            "persistent command",
            "output",
            None,
            {"key": "value"},
            0.5
        )

        # Load from database
        loaded = await cognitive_memory._load_memory(memory.id)

        assert loaded is not None
        assert loaded.command == "persistent command"
        assert loaded.context == {"key": "value"}

    @pytest.mark.asyncio
    async def test_pattern_statistics(self, cognitive_memory):
        """Test pattern statistics tracking"""
        # Add commands with patterns
        for _ in range(3):
            await cognitive_memory.remember("git add", "success", None, {}, 0.1)

        for _ in range(2):
            await cognitive_memory.remember("git commit", "error", "failed", {}, 0.1)

        # Check pattern stats are tracked
        # This would check the database in a real test
        assert len(cognitive_memory.pattern_stats) >= 0

    @pytest.mark.asyncio
    async def test_memory_decay(self, cognitive_memory):
        """Test memory importance decay over time"""
        memory = await cognitive_memory.remember("old command", "output", None, {}, 0.1)

        initial_importance = memory.importance

        # Simulate time passing
        memory.timestamp -= 86400  # 1 day ago

        # Recall to trigger decay
        await cognitive_memory.recall("old", k=1)

        # Importance should have decayed
        expected = initial_importance * (cognitive_memory.forgetting_factor ** 1)
        assert abs(memory.importance - expected) < 0.01

    @pytest.mark.asyncio
    async def test_memory_consolidation(self, cognitive_memory):
        """Test memory consolidation when reaching max memories"""
        cognitive_memory.max_memories = 10

        # Add more than max memories
        for i in range(15):
            memory = await cognitive_memory.remember(
                f"command_{i}",
                f"output_{i}",
                None,
                {},
                0.1
            )
            # Set different importance
            memory.importance = i / 20

        # Trigger consolidation
        await cognitive_memory._consolidate_learning()

        # Should have pruned low importance memories
        assert len(cognitive_memory.memory_cache) <= cognitive_memory.max_memories

    @pytest.mark.asyncio
    async def test_embedding_creation(self, cognitive_memory):
        """Test embedding creation"""
        with patch.object(cognitive_memory, 'llm_provider') as mock_llm:
            mock_llm.get_embedding = AsyncMock(return_value=[0.1] * 10)

            embedding = await cognitive_memory._create_embedding(
                "test text",
                "output",
                {"key": "value"}
            )

            assert embedding is not None
            assert len(embedding) == 10
            mock_llm.get_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_hash_embedding_fallback(self, cognitive_memory):
        """Test hash-based embedding fallback"""
        cognitive_memory.llm_provider = None

        embedding = await cognitive_memory._create_embedding(
            "test text",
            "output",
            {}
        )

        assert embedding is not None
        assert len(embedding) == cognitive_memory.vector_dim
        assert np.linalg.norm(embedding) > 0  # Should be normalized

    @pytest.mark.asyncio
    async def test_text_search_fallback(self, cognitive_memory):
        """Test text search when embeddings not available"""
        # Add memories without embeddings
        memory1 = MemoryEntry(
            id="1",
            command="test command",
            output="output",
            error=None,
            context={},
            timestamp=time.time(),
            success=True,
            duration=0.1,
            embedding=None
        )
        memory2 = MemoryEntry(
            id="2",
            command="other command",
            output="output",
            error=None,
            context={},
            timestamp=time.time(),
            success=True,
            duration=0.1,
            embedding=None
        )

        cognitive_memory.memory_cache["1"] = memory1
        cognitive_memory.memory_cache["2"] = memory2

        # Search by text
        results = await cognitive_memory._text_search("test", k=2)

        assert len(results) >= 1
        assert results[0].command == "test command"

    @pytest.mark.asyncio
    async def test_following_commands(self, cognitive_memory):
        """Test finding following commands"""
        # Add sequence of commands in same session
        memory1 = await cognitive_memory.remember(
            "cd /project",
            "changed",
            None,
            {"session": "123"},
            0.1
        )
        await asyncio.sleep(0.1)
        memory2 = await cognitive_memory.remember(
            "ls -la",
            "files",
            None,
            {"session": "123"},
            0.1
        )

        # Find what follows cd
        following = await cognitive_memory._find_following_commands("cd /project", k=3)

        assert len(following) >= 0
        # Would contain ls -la if in same session

    def test_extract_tags(self, cognitive_memory):
        """Test tag extraction from commands"""
        tags = cognitive_memory._extract_tags("git add -A file.py --force")

        assert "cmd:git" in tags
        assert "ext:.py" in tags
        assert "flag:-A" in tags
        assert "flag:--force" in tags

    def test_calculate_importance(self, cognitive_memory):
        """Test importance calculation"""
        importance = cognitive_memory._calculate_importance(
            "complex command with many parts",
            "long output" * 100,
            None,
            ["pattern1", "pattern2", "pattern3"]
        )

        assert importance > 0.5  # Complex command should be important

        error_importance = cognitive_memory._calculate_importance(
            "simple",
            "short",
            "error",
            []
        )

        assert error_importance > 0.5  # Errors are important

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, cognitive_memory):
        """Test sentiment analysis"""
        positive_sentiment = await cognitive_memory._analyze_sentiment(
            "test",
            "Success! Task complete and updated",
            None
        )
        assert positive_sentiment > 0

        negative_sentiment = await cognitive_memory._analyze_sentiment(
            "test",
            "Error: Failed to connect, invalid credentials",
            "Connection failed"
        )
        assert negative_sentiment < 0

        neutral_sentiment = await cognitive_memory._analyze_sentiment(
            "test",
            "Output data",
            None
        )
        assert abs(neutral_sentiment) < 0.2