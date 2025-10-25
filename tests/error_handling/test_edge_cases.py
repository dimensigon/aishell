"""
Edge Case Tests

Tests for boundary conditions, null/empty values, unicode issues,
and other edge cases across all modules.
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.event_bus import AsyncEventBus, Event, EventPriority
from src.llm.manager import LocalLLMManager


class TestNullAndEmpty:
    """Test null and empty value handling"""

    def test_none_values(self):
        """Test handling of None values"""
        test_cases = [
            (None, "default"),
            ("", "default"),
            (0, "default"),
            (False, "default"),
        ]

        def get_value_or_default(value, default):
            return value if value is not None else default

        results = [get_value_or_default(v, d) for v, d in test_cases]

        assert results[0] == "default"  # None
        assert results[1] == ""  # Empty string is not None
        assert results[2] == 0  # Zero is not None
        assert results[3] is False  # False is not None

    def test_empty_string_operations(self):
        """Test operations on empty strings"""
        empty = ""

        assert len(empty) == 0
        assert empty.split() == []
        assert empty.strip() == ""
        assert empty.upper() == ""
        assert empty.lower() == ""
        assert "" in empty
        assert empty + "test" == "test"
        assert empty * 5 == ""

    def test_empty_collections(self):
        """Test empty collection behavior"""
        empty_list = []
        empty_dict = {}
        empty_set = set()
        empty_tuple = ()

        assert not empty_list
        assert not empty_dict
        assert not empty_set
        assert not empty_tuple

        assert len(empty_list) == 0
        assert len(empty_dict) == 0
        assert len(empty_set) == 0
        assert len(empty_tuple) == 0

    @pytest.mark.asyncio
    async def test_none_in_event_data(self):
        """Test event with None data"""
        bus = AsyncEventBus()
        await bus.start()

        received = []

        async def handler(event):
            received.append(event.data)

        bus.subscribe("test", handler)

        # Test various None/empty scenarios
        await bus.publish(Event("test", data=None))
        await bus.publish(Event("test", data={}))
        await bus.publish(Event("test", data={"key": None}))

        await asyncio.sleep(0.1)
        await bus.stop()

        assert len(received) == 3
        assert received[0] == {}  # None becomes {}
        assert received[1] == {}
        assert received[2] == {"key": None}

    def test_llm_manager_with_empty_input(self):
        """Test LLM manager with empty strings"""
        manager = LocalLLMManager()

        # Empty query
        anonymized, mapping = manager.anonymize_query("")
        assert anonymized == ""
        assert mapping == {}

        # Deanonymize empty
        result = manager.deanonymize_result("", {})
        assert result == ""

        # Empty mapping
        result = manager.deanonymize_result("test", {})
        assert result == "test"


class TestBoundaryValues:
    """Test boundary value scenarios"""

    def test_integer_boundaries(self):
        """Test integer min/max boundaries"""
        # Python 3 integers are unbounded
        large = 10 ** 100
        assert large > 0

        small = -(10 ** 100)
        assert small < 0

        # System-dependent boundaries
        max_int = sys.maxsize
        assert max_int > 0

        min_int = -sys.maxsize - 1
        assert min_int < 0

    def test_float_boundaries(self):
        """Test float boundaries and special values"""
        import math

        # Special float values
        assert math.isnan(float('nan'))
        assert math.isinf(float('inf'))
        assert math.isinf(float('-inf'))

        # Operations with infinity
        assert float('inf') > 0
        assert float('-inf') < 0
        assert float('inf') + 1 == float('inf')
        assert float('inf') * 2 == float('inf')

        # NaN comparisons
        nan = float('nan')
        assert nan != nan
        assert not (nan == nan)
        assert not (nan < 0)
        assert not (nan > 0)

    def test_string_length_boundaries(self):
        """Test very long strings"""
        # Small string
        small = ""
        assert len(small) == 0

        # Medium string
        medium = "x" * 1000
        assert len(medium) == 1000

        # Large string
        large = "x" * 1_000_000
        assert len(large) == 1_000_000

        del large  # Free memory

    def test_list_boundaries(self):
        """Test list size boundaries"""
        # Empty
        empty = []
        assert len(empty) == 0

        # Single element
        single = [1]
        assert len(single) == 1

        # Large list
        large = list(range(1_000_000))
        assert len(large) == 1_000_000
        assert large[0] == 0
        assert large[-1] == 999_999

        del large

    @pytest.mark.asyncio
    async def test_event_priority_boundaries(self):
        """Test event priority boundary values"""
        bus = AsyncEventBus()
        await bus.start()

        # Test all priority levels
        priorities = [
            EventPriority.CRITICAL,
            EventPriority.HIGH,
            EventPriority.NORMAL,
            EventPriority.LOW,
        ]

        for priority in priorities:
            event = Event("test", priority=priority)
            await bus.publish(event)

        await asyncio.sleep(0.1)
        await bus.stop()

    def test_off_by_one_errors(self):
        """Test off-by-one boundary scenarios"""
        items = [0, 1, 2, 3, 4]

        # Valid indices
        assert items[0] == 0
        assert items[4] == 4
        assert items[-1] == 4
        assert items[-5] == 0

        # Invalid indices
        with pytest.raises(IndexError):
            _ = items[5]

        with pytest.raises(IndexError):
            _ = items[-6]

        # Slicing edge cases
        assert items[:0] == []
        assert items[5:] == []
        assert items[0:5] == items
        assert items[0:6] == items  # Beyond end is OK


class TestUnicodeEdgeCases:
    """Test unicode and encoding edge cases"""

    def test_unicode_characters(self):
        """Test various unicode characters"""
        test_strings = [
            "Hello",  # ASCII
            "Héllo",  # Latin with accent
            "你好",  # Chinese
            "Привет",  # Cyrillic
            "مرحبا",  # Arabic
            "🎉🎊",  # Emoji
            "👨‍👩‍👧‍👦",  # Family emoji (multiple codepoints)
        ]

        for s in test_strings:
            assert len(s) >= 0
            assert s.encode('utf-8').decode('utf-8') == s

    def test_zero_width_characters(self):
        """Test zero-width unicode characters"""
        # Zero-width space
        zwsp = "\u200b"
        assert len(zwsp) == 1
        assert zwsp.strip() == zwsp  # Not stripped

        # Zero-width joiner
        zwj = "\u200d"
        assert len(zwj) == 1

        # Combined
        text = f"Hello{zwsp}World"
        assert text != "HelloWorld"
        assert "Hello" in text
        assert "World" in text

    def test_unicode_normalization(self):
        """Test unicode normalization forms"""
        import unicodedata

        # Composed vs decomposed
        composed = "é"  # Single codepoint
        decomposed = "é"  # e + combining accent

        # May look same but different
        nfc = unicodedata.normalize('NFC', decomposed)
        nfd = unicodedata.normalize('NFD', composed)

        assert unicodedata.normalize('NFC', composed) == unicodedata.normalize('NFC', decomposed)

    def test_invalid_utf8_handling(self):
        """Test handling of invalid UTF-8"""
        # Invalid UTF-8 bytes
        invalid_bytes = b'\x80\x81\x82'

        with pytest.raises(UnicodeDecodeError):
            invalid_bytes.decode('utf-8')

        # With error handling
        result = invalid_bytes.decode('utf-8', errors='replace')
        assert '\ufffd' in result  # Replacement character

        result = invalid_bytes.decode('utf-8', errors='ignore')
        assert result == ''  # Ignored

    def test_surrogate_pairs(self):
        """Test surrogate pair handling"""
        # Emoji using surrogate pair
        emoji = "😀"
        assert len(emoji) == 1  # One character

        # In UTF-16 it's a surrogate pair
        utf16 = emoji.encode('utf-16')
        assert len(utf16) > 2

    def test_right_to_left_text(self):
        """Test right-to-left text handling"""
        rtl = "مرحبا"
        ltr = "Hello"

        combined = f"{ltr} {rtl}"
        assert ltr in combined
        assert rtl in combined


class TestNumericEdgeCases:
    """Test numeric edge cases"""

    def test_division_edge_cases(self):
        """Test division edge cases"""
        # Division by zero
        with pytest.raises(ZeroDivisionError):
            _ = 1 / 0

        with pytest.raises(ZeroDivisionError):
            _ = 1 // 0

        # Float division
        assert 1.0 / 2.0 == 0.5
        assert 1 / 2 == 0.5  # Python 3

        # Integer division
        assert 7 // 2 == 3
        assert -7 // 2 == -4  # Floor division

        # Modulo with zero
        with pytest.raises(ZeroDivisionError):
            _ = 5 % 0

    def test_negative_zero(self):
        """Test negative zero float"""
        pos_zero = 0.0
        neg_zero = -0.0

        assert pos_zero == neg_zero
        assert str(pos_zero) == "0.0"
        assert str(neg_zero) == "-0.0"  # Different representation

    def test_floating_point_precision(self):
        """Test floating point precision issues"""
        # Classic 0.1 + 0.2 problem
        result = 0.1 + 0.2
        assert result != 0.3  # Due to floating point precision
        assert abs(result - 0.3) < 1e-10  # But very close

        # Use pytest.approx for comparisons
        assert result == pytest.approx(0.3)

    def test_very_small_numbers(self):
        """Test very small numbers"""
        import sys

        epsilon = sys.float_info.epsilon
        assert epsilon > 0
        assert 1.0 + epsilon > 1.0
        assert 1.0 + (epsilon / 2) == 1.0  # Too small to matter

        # Denormalized numbers
        tiny = sys.float_info.min
        assert tiny > 0
        assert tiny / 2 > 0  # Subnormal

    def test_numeric_overflow(self):
        """Test numeric overflow handling"""
        import math

        # Float overflow
        large = 1e308
        assert not math.isinf(large)

        very_large = 1e309
        assert math.isinf(very_large)

        # Integer overflow doesn't happen in Python 3
        huge = 10 ** 1000
        assert huge > 0


class TestCollectionEdgeCases:
    """Test edge cases with collections"""

    def test_dict_key_edge_cases(self):
        """Test unusual dict keys"""
        # Various key types
        d = {
            None: "none",
            0: "zero",
            False: "false",  # Overwrites 0
            "": "empty",
            (): "empty_tuple",
            (1, 2): "tuple",
        }

        assert d[None] == "none"
        assert d[0] == "false"  # False == 0
        assert d[False] == "false"
        assert d[""] == "empty"
        assert d[()] == "empty_tuple"

        # Unhashable keys fail
        with pytest.raises(TypeError):
            d[[1, 2]] = "list"  # Lists are unhashable

    def test_dict_insertion_order(self):
        """Test dict maintains insertion order (Python 3.7+)"""
        d = {}
        for i in range(100):
            d[i] = i * 2

        assert list(d.keys()) == list(range(100))

    def test_set_edge_cases(self):
        """Test set edge cases"""
        # Empty set
        s = set()
        assert len(s) == 0

        # Set with None
        s = {None, 1, 2}
        assert None in s
        assert len(s) == 3

        # Set operations
        s1 = {1, 2, 3}
        s2 = set()

        assert s1 | s2 == s1  # Union with empty
        assert s1 & s2 == set()  # Intersection with empty
        assert s1 - s2 == s1  # Difference

    def test_nested_collections(self):
        """Test deeply nested collections"""
        # Nested lists
        nested = [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]
        assert nested[0][0][0][0] == 1
        assert nested[0][1][1][1] == 8

        # Nested dicts
        nested_dict = {
            "a": {
                "b": {
                    "c": {
                        "d": "value"
                    }
                }
            }
        }
        assert nested_dict["a"]["b"]["c"]["d"] == "value"

    def test_circular_reference(self):
        """Test circular references in collections"""
        lst = [1, 2, 3]
        lst.append(lst)  # Circular reference

        assert lst[3] is lst
        assert lst[3][3] is lst

        # Can't convert to JSON
        import json
        with pytest.raises(ValueError):
            json.dumps(lst)


class TestAsyncEdgeCases:
    """Test async/await edge cases"""

    @pytest.mark.asyncio
    async def test_empty_gather(self):
        """Test gather with no tasks"""
        result = await asyncio.gather()
        assert result == []

    @pytest.mark.asyncio
    async def test_gather_with_none(self):
        """Test gather with None values"""
        async def return_none():
            return None

        results = await asyncio.gather(
            return_none(),
            return_none(),
            return_none()
        )

        assert results == [None, None, None]

    @pytest.mark.asyncio
    async def test_zero_sleep(self):
        """Test sleep with zero duration"""
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0)
        elapsed = asyncio.get_event_loop().time() - start

        # Should yield control but return quickly
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_negative_sleep(self):
        """Test sleep with negative duration"""
        # Negative sleep is treated as 0
        await asyncio.sleep(-1)

    @pytest.mark.asyncio
    async def test_cancelled_task(self):
        """Test cancelled task handling"""
        async def long_task():
            await asyncio.sleep(10)
            return "done"

        task = asyncio.create_task(long_task())
        await asyncio.sleep(0.01)

        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_double_await(self):
        """Test awaiting same coroutine twice"""
        async def simple_coro():
            return 42

        coro = simple_coro()
        result1 = await coro

        # Can't await same coroutine twice
        with pytest.raises(RuntimeError):
            result2 = await coro


class TestPathEdgeCases:
    """Test path and filesystem edge cases"""

    def test_empty_path(self):
        """Test empty path string"""
        p = Path("")
        assert str(p) == "."

    def test_root_path(self):
        """Test root path"""
        p = Path("/")
        assert p.is_absolute()
        assert p.parent == p  # Root parent is itself

    def test_current_directory(self):
        """Test current directory references"""
        p = Path(".")
        assert p.exists()

        p2 = Path("./././.")
        assert p2.resolve() == p.resolve()

    def test_parent_directory(self):
        """Test parent directory references"""
        p = Path("..")
        assert p.exists()

        # Multiple parents
        p2 = Path("../../..")
        assert str(p2) == "../../.."

    def test_path_with_special_characters(self):
        """Test paths with special characters"""
        import tempfile

        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            for name in special_names:
                path = Path(tmpdir) / name
                path.write_text("test")
                assert path.exists()
                assert path.read_text() == "test"


class TestErrorMessageEdgeCases:
    """Test edge cases in error messages"""

    def test_very_long_error_message(self):
        """Test very long error messages"""
        long_msg = "x" * 10000

        try:
            raise ValueError(long_msg)
        except ValueError as e:
            assert str(e) == long_msg

    def test_unicode_in_error_message(self):
        """Test unicode characters in error messages"""
        msg = "Error: 你好 🎉"

        try:
            raise ValueError(msg)
        except ValueError as e:
            assert str(e) == msg

    def test_empty_error_message(self):
        """Test empty error message"""
        try:
            raise ValueError("")
        except ValueError as e:
            assert str(e) == ""

    def test_none_error_message(self):
        """Test None as error message"""
        try:
            raise ValueError(None)
        except ValueError as e:
            assert str(e) == "None"
