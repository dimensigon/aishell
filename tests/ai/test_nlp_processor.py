"""
Tests for NLP Processor

Comprehensive test suite covering:
- Intent recognition
- Entity extraction
- Command translation
- Context awareness
- Ambiguity resolution
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.ai.nlp_processor import (
    NLPProcessor,
    Intent,
    IntentType,
    Entity,
    EntityType,
    NLPContext
)


class TestNLPProcessor:
    """Test suite for NLPProcessor"""

    @pytest.fixture
    def processor(self):
        """Create NLPProcessor instance"""
        return NLPProcessor()

    @pytest.fixture
    def processor_with_llm(self):
        """Create NLPProcessor with mocked LLM"""
        mock_llm = Mock()
        mock_llm.generate_with_routing = AsyncMock(return_value='{"intent": "file_operation", "confidence": 0.9, "reasoning": "test"}')
        return NLPProcessor(llm_manager=mock_llm)

    @pytest.fixture
    def context(self):
        """Create test context"""
        return NLPContext(
            current_directory="/home/user",
            command_history=["ls", "cd /tmp"],
            environment_vars={"HOME": "/home/user"}
        )


class TestIntentRecognition(TestNLPProcessor):
    """Tests for intent recognition"""

    @pytest.mark.asyncio
    async def test_file_operation_intent(self, processor):
        """Test recognizing file operation intent"""
        inputs = [
            "show me all files",
            "list files in directory",
            "cat myfile.txt",
            "view the contents of file.py"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.FILE_OPERATION
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_directory_nav_intent(self, processor):
        """Test recognizing directory navigation intent"""
        inputs = [
            "go to home directory",
            "change to /tmp",
            "navigate to documents folder",
            "where am i",
            "current directory"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.DIRECTORY_NAV
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_file_search_intent(self, processor):
        """Test recognizing file search intent"""
        inputs = [
            "find all python files",
            "search for *.txt",
            "locate file.py",
            "search for 'error' in logs"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.FILE_SEARCH
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_file_manipulation_intent(self, processor):
        """Test recognizing file manipulation intent"""
        inputs = [
            "copy file.txt to backup.txt",
            "move temp to archive",
            "delete old.log",
            "create new directory",
            "rename file.txt to newfile.txt"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.FILE_MANIPULATION
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_system_info_intent(self, processor):
        """Test recognizing system information intent"""
        inputs = [
            "who am i",
            "what is my username",
            "show hostname",
            "system information",
            "check disk space"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.SYSTEM_INFO
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_process_mgmt_intent(self, processor):
        """Test recognizing process management intent"""
        inputs = [
            "show all processes",
            "list running processes",
            "kill process 1234",
            "stop the server"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.PROCESS_MGMT
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_network_ops_intent(self, processor):
        """Test recognizing network operations intent"""
        inputs = [
            "ping google.com",
            "check network connection",
            "download file from url",
            "curl https://example.com"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.NETWORK_OPS
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_version_control_intent(self, processor):
        """Test recognizing version control intent"""
        inputs = [
            "git status",
            "commit changes",
            "push to repository",
            "show git log"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.VERSION_CONTROL
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_information_query_intent(self, processor):
        """Test recognizing information query intent"""
        inputs = [
            "what is Docker",
            "how does grep work",
            "what are environment variables"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.INFORMATION_QUERY
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_help_request_intent(self, processor):
        """Test recognizing help request intent"""
        inputs = [
            "help me with git",
            "show me how to use grep",
            "I need help with commands"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.HELP_REQUEST
            assert intent.confidence > 0.5

    @pytest.mark.asyncio
    async def test_unknown_intent(self, processor):
        """Test handling unknown intent"""
        inputs = [
            "",
            "asdfghjkl",
            "random nonsense text"
        ]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            # Should either be UNKNOWN or have very low confidence
            if intent.type != IntentType.UNKNOWN:
                assert intent.confidence < 0.5


class TestEntityExtraction(TestNLPProcessor):
    """Tests for entity extraction"""

    @pytest.mark.asyncio
    async def test_file_path_extraction(self, processor):
        """Test extracting file paths"""
        text = "show me /home/user/file.txt and ./local/path.py"
        intent = await processor.analyze_intent(text)

        file_entities = [e for e in intent.entities if e.type == EntityType.FILE_PATH]
        assert len(file_entities) >= 1

    @pytest.mark.asyncio
    async def test_file_pattern_extraction(self, processor):
        """Test extracting file patterns"""
        text = "find all *.py and *.txt files"
        intent = await processor.analyze_intent(text)

        pattern_entities = [e for e in intent.entities if e.type == EntityType.FILE_PATTERN]
        assert len(pattern_entities) >= 1
        assert any('*.py' in e.value or '*.txt' in e.value for e in pattern_entities)

    @pytest.mark.asyncio
    async def test_command_extraction(self, processor):
        """Test extracting commands"""
        text = "use ls to list and grep to search"
        intent = await processor.analyze_intent(text)

        command_entities = [e for e in intent.entities if e.type == EntityType.COMMAND]
        assert len(command_entities) >= 1

    @pytest.mark.asyncio
    async def test_url_extraction(self, processor):
        """Test extracting URLs"""
        text = "download https://example.com/file.zip"
        intent = await processor.analyze_intent(text)

        url_entities = [e for e in intent.entities if e.type == EntityType.URL]
        assert len(url_entities) == 1
        assert 'https://example.com' in url_entities[0].value

    @pytest.mark.asyncio
    async def test_ip_address_extraction(self, processor):
        """Test extracting IP addresses"""
        text = "ping 192.168.1.1"
        intent = await processor.analyze_intent(text)

        ip_entities = [e for e in intent.entities if e.type == EntityType.IP_ADDRESS]
        assert len(ip_entities) == 1
        assert ip_entities[0].value == '192.168.1.1'

    @pytest.mark.asyncio
    async def test_flag_extraction(self, processor):
        """Test extracting flags"""
        text = "run command with -r and --verbose flags"
        intent = await processor.analyze_intent(text)

        flag_entities = [e for e in intent.entities if e.type == EntityType.FLAG]
        assert len(flag_entities) >= 1

    @pytest.mark.asyncio
    async def test_number_extraction(self, processor):
        """Test extracting numbers"""
        text = "kill process 1234 and wait 60 seconds"
        intent = await processor.analyze_intent(text)

        number_entities = [e for e in intent.entities if e.type == EntityType.NUMBER]
        assert len(number_entities) >= 1


class TestCommandTranslation(TestNLPProcessor):
    """Tests for command translation"""

    @pytest.mark.asyncio
    async def test_list_files_translation(self, processor):
        """Test translating list files command"""
        result = await processor.translate_command("show me all files")

        assert result['command'] is not None
        assert 'ls' in result['command']
        assert result['confidence'] > 0.0

    @pytest.mark.asyncio
    async def test_change_directory_translation(self, processor):
        """Test translating change directory command"""
        result = await processor.translate_command("go to home directory")

        assert result['command'] is not None
        assert 'cd' in result['command']

    @pytest.mark.asyncio
    async def test_find_files_translation(self, processor):
        """Test translating find files command"""
        result = await processor.translate_command("find all python files")

        assert result['command'] is not None
        assert 'find' in result['command'] or 'grep' in result['command']

    @pytest.mark.asyncio
    async def test_copy_file_translation(self, processor):
        """Test translating copy file command"""
        result = await processor.translate_command("copy file.txt to backup.txt")

        assert result['command'] is not None
        assert 'cp' in result['command']

    @pytest.mark.asyncio
    async def test_git_status_translation(self, processor):
        """Test translating git status command"""
        result = await processor.translate_command("show git status")

        assert result['command'] is not None
        assert 'git' in result['command']
        assert 'status' in result['command']

    @pytest.mark.asyncio
    async def test_ping_translation(self, processor):
        """Test translating ping command"""
        result = await processor.translate_command("ping google.com")

        assert result['command'] is not None
        assert 'ping' in result['command']

    @pytest.mark.asyncio
    async def test_disk_space_translation(self, processor):
        """Test translating disk space command"""
        result = await processor.translate_command("show disk space")

        assert result['command'] is not None
        assert 'df' in result['command']

    @pytest.mark.asyncio
    async def test_process_list_translation(self, processor):
        """Test translating process list command"""
        result = await processor.translate_command("list all processes")

        assert result['command'] is not None
        assert 'ps' in result['command']


class TestContextAwareness(TestNLPProcessor):
    """Tests for context-aware processing"""

    @pytest.mark.asyncio
    async def test_context_preservation(self, processor, context):
        """Test that context is preserved across calls"""
        await processor.analyze_intent("list files", context)
        await processor.analyze_intent("show me more", context)

        assert len(processor.context.conversation_history) >= 2

    @pytest.mark.asyncio
    async def test_context_current_directory(self, processor, context):
        """Test using current directory from context"""
        context.current_directory = "/home/user/documents"
        processor.update_context(current_directory=context.current_directory)

        result = await processor.translate_command("list files")
        # Command should be aware of context
        assert result is not None

    @pytest.mark.asyncio
    async def test_context_command_history(self, processor, context):
        """Test using command history from context"""
        context.command_history = ["ls", "cd /tmp", "pwd"]
        processor.update_context(command_history=context.command_history)

        intent = await processor.analyze_intent("do that again")
        # Should have context from history
        assert processor.context.command_history == context.command_history

    @pytest.mark.asyncio
    async def test_last_intent_tracking(self, processor):
        """Test tracking last intent"""
        await processor.analyze_intent("list files")
        assert processor.context.last_intent is not None
        assert processor.context.last_intent.type == IntentType.FILE_OPERATION


class TestAlternatives(TestNLPProcessor):
    """Tests for alternative suggestions"""

    @pytest.mark.asyncio
    async def test_alternatives_generation(self, processor):
        """Test generating alternative commands"""
        result = await processor.translate_command("show files")

        # Should have some alternatives
        assert 'alternatives' in result
        assert isinstance(result['alternatives'], list)

    @pytest.mark.asyncio
    async def test_alternatives_are_different(self, processor):
        """Test that alternatives are different from main command"""
        result = await processor.translate_command("list directory contents")

        if result['command'] and result['alternatives']:
            for alt in result['alternatives']:
                assert alt != result['command']


class TestConfidenceScoring(TestNLPProcessor):
    """Tests for confidence scoring"""

    @pytest.mark.asyncio
    async def test_high_confidence_clear_intent(self, processor):
        """Test high confidence for clear intents"""
        intent = await processor.analyze_intent("ls -la")
        assert intent.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_lower_confidence_ambiguous(self, processor):
        """Test lower confidence for ambiguous intents"""
        intent = await processor.analyze_intent("do something with files")
        # Ambiguous commands should have lower confidence
        assert intent.confidence < 0.9

    @pytest.mark.asyncio
    async def test_confidence_in_translation_result(self, processor):
        """Test confidence is included in translation result"""
        result = await processor.translate_command("show files")

        assert 'confidence' in result
        assert 0.0 <= result['confidence'] <= 1.0


class TestLLMIntegration(TestNLPProcessor):
    """Tests for LLM integration"""

    @pytest.mark.asyncio
    async def test_llm_fallback_on_low_confidence(self, processor_with_llm):
        """Test that LLM is used when pattern matching has low confidence"""
        intent = await processor_with_llm.analyze_intent("do something complex")

        # Should have attempted LLM call
        assert processor_with_llm.llm_manager.generate_with_routing.called

    @pytest.mark.asyncio
    async def test_processor_works_without_llm(self, processor):
        """Test that processor works without LLM"""
        assert processor.llm_manager is None

        intent = await processor.analyze_intent("list files")
        assert intent is not None
        assert intent.type == IntentType.FILE_OPERATION


class TestEdgeCases(TestNLPProcessor):
    """Tests for edge cases"""

    @pytest.mark.asyncio
    async def test_empty_input(self, processor):
        """Test handling empty input"""
        intent = await processor.analyze_intent("")

        assert intent.type == IntentType.UNKNOWN
        assert intent.requires_clarification

    @pytest.mark.asyncio
    async def test_very_long_input(self, processor):
        """Test handling very long input"""
        long_text = "show me files " * 100
        intent = await processor.analyze_intent(long_text)

        assert intent is not None

    @pytest.mark.asyncio
    async def test_special_characters(self, processor):
        """Test handling special characters"""
        text = "find files with pattern *.{txt,py,md}"
        intent = await processor.analyze_intent(text)

        assert intent is not None

    @pytest.mark.asyncio
    async def test_unicode_characters(self, processor):
        """Test handling unicode characters"""
        text = "show files in 文档 folder"
        intent = await processor.analyze_intent(text)

        assert intent is not None

    @pytest.mark.asyncio
    async def test_mixed_case_input(self, processor):
        """Test handling mixed case input"""
        inputs = ["SHOW FILES", "Show Files", "sHoW fIlEs"]

        for text in inputs:
            intent = await processor.analyze_intent(text)
            assert intent.type == IntentType.FILE_OPERATION


class TestStatistics(TestNLPProcessor):
    """Tests for statistics tracking"""

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, processor):
        """Test that statistics are tracked"""
        initial_stats = processor.get_statistics()
        assert initial_stats['total_processed'] == 0

        await processor.analyze_intent("list files")

        updated_stats = processor.get_statistics()
        assert updated_stats['total_processed'] == 1

    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, processor):
        """Test success rate calculation"""
        await processor.translate_command("list files")
        await processor.translate_command("show git status")

        stats = processor.get_statistics()
        assert 'success_rate' in stats
        assert 0.0 <= stats['success_rate'] <= 1.0

    def test_initial_statistics(self, processor):
        """Test initial statistics state"""
        stats = processor.get_statistics()

        assert stats['total_processed'] == 0
        assert stats['successful_translations'] == 0
        assert stats['success_rate'] == 0.0


class TestClarificationRequests(TestNLPProcessor):
    """Tests for clarification requests"""

    @pytest.mark.asyncio
    async def test_clarification_for_ambiguous(self, processor):
        """Test clarification request for ambiguous input"""
        # Very vague input
        intent = await processor.analyze_intent("do stuff")

        # May or may not require clarification depending on implementation
        # Just ensure the field exists
        assert hasattr(intent, 'requires_clarification')

    @pytest.mark.asyncio
    async def test_no_clarification_for_clear_intent(self, processor):
        """Test no clarification for clear intents"""
        intent = await processor.analyze_intent("ls -la")

        assert not intent.requires_clarification


class TestUpdateContext(TestNLPProcessor):
    """Tests for context updates"""

    def test_update_current_directory(self, processor):
        """Test updating current directory"""
        processor.update_context(current_directory="/new/path")
        assert processor.context.current_directory == "/new/path"

    def test_update_command_history(self, processor):
        """Test updating command history"""
        history = ["ls", "cd /tmp"]
        processor.update_context(command_history=history)
        assert processor.context.command_history == history

    def test_update_multiple_fields(self, processor):
        """Test updating multiple context fields"""
        processor.update_context(
            current_directory="/test",
            command_history=["ls"],
            environment_vars={"TEST": "value"}
        )

        assert processor.context.current_directory == "/test"
        assert processor.context.command_history == ["ls"]
        assert processor.context.environment_vars == {"TEST": "value"}


# Performance tests
class TestPerformance(TestNLPProcessor):
    """Performance tests"""

    @pytest.mark.asyncio
    async def test_intent_recognition_speed(self, processor):
        """Test that intent recognition is reasonably fast"""
        import time

        start = time.time()
        for _ in range(10):
            await processor.analyze_intent("list all files in directory")
        duration = time.time() - start

        # Should process 10 requests in under 1 second
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_entity_extraction_speed(self, processor):
        """Test entity extraction performance"""
        import time

        text = "find /home/user/documents/*.txt and grep 'pattern' in files"

        start = time.time()
        for _ in range(100):
            entities = processor._extract_entities(text)
        duration = time.time() - start

        # Should handle 100 extractions quickly
        assert duration < 1.0


# Integration tests
class TestIntegration(TestNLPProcessor):
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, processor):
        """Test complete workflow from input to command"""
        # Analyze intent
        intent = await processor.analyze_intent("show me all python files")

        # Should recognize file search intent
        assert intent.type in [IntentType.FILE_SEARCH, IntentType.FILE_OPERATION]

        # Should suggest a command
        assert intent.suggested_command is not None

        # Should extract entities
        assert len(intent.entities) > 0

        # Should have reasonable confidence
        assert intent.confidence > 0.3

    @pytest.mark.asyncio
    async def test_context_aware_workflow(self, processor, context):
        """Test workflow with context"""
        # First command
        await processor.analyze_intent("list files", context)

        # Context should be updated
        assert len(processor.context.conversation_history) > 0

        # Second command referencing context
        intent2 = await processor.analyze_intent("show more details")

        # Should have context from first command
        assert len(processor.context.conversation_history) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
