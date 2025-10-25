"""
Data Corruption and Recovery Tests

Tests data corruption scenarios and recovery mechanisms including
corrupted files, invalid data, checksum failures, and recovery strategies.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pickle

from src.core.config import ConfigManager


class TestJSONCorruption:
    """Test JSON data corruption scenarios"""

    def test_invalid_json_syntax(self):
        """Test loading invalid JSON"""
        invalid_json = '{"key": "value", invalid}'

        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_truncated_json(self):
        """Test truncated JSON file"""
        truncated_json = '{"key": "value", "nested": {"incomplete":'

        with pytest.raises(json.JSONDecodeError):
            json.loads(truncated_json)

    def test_corrupted_json_with_null_bytes(self):
        """Test JSON with null bytes"""
        corrupted = '{"key": "val\x00ue"}'

        # Should still parse but data is corrupted
        data = json.loads(corrupted)
        assert '\x00' in data['key']

    def test_json_with_invalid_encoding(self):
        """Test JSON with encoding issues"""
        # Binary data that's not valid UTF-8
        invalid_bytes = b'\x80\x81\x82'

        with pytest.raises(UnicodeDecodeError):
            invalid_bytes.decode('utf-8')

    def test_malformed_json_recovery(self):
        """Test recovery from malformed JSON"""
        malformed = '{"key": "value"'  # Missing closing brace

        try:
            json.loads(malformed)
            pytest.fail("Should have raised JSONDecodeError")
        except json.JSONDecodeError as e:
            # Can attempt recovery by adding closing brace
            recovered = malformed + '}'
            data = json.loads(recovered)
            assert data['key'] == 'value'

    @pytest.mark.asyncio
    async def test_config_file_corruption_recovery(self):
        """Test config manager recovery from corrupted file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"corrupted": invalid json}')
            temp_path = f.name

        try:
            config = ConfigManager(temp_path)

            # Should handle corruption gracefully
            await config.load()

            # Should have default config
            assert config.config is not None
        finally:
            os.unlink(temp_path)

    def test_nested_json_corruption(self):
        """Test corruption in nested JSON structures"""
        corrupted_nested = '''
        {
            "level1": {
                "level2": {
                    "level3": "value",
                    "corrupted": null,
                }
            }
        }
        '''  # Extra comma before }

        with pytest.raises(json.JSONDecodeError):
            json.loads(corrupted_nested)


class TestPickleCorruption:
    """Test pickle data corruption"""

    def test_corrupted_pickle_data(self):
        """Test loading corrupted pickle data"""
        # Valid pickle data
        data = {"key": "value", "number": 42}
        pickled = pickle.dumps(data)

        # Corrupt it
        corrupted = pickled[:-10]  # Truncate

        with pytest.raises((pickle.UnpicklingError, EOFError)):
            pickle.loads(corrupted)

    def test_pickle_version_mismatch(self):
        """Test pickle protocol version issues"""
        # Create data with specific protocol
        data = {"test": "data"}

        # Protocol 5 (Python 3.8+)
        try:
            pickled_v5 = pickle.dumps(data, protocol=5)

            # Should load fine in compatible version
            loaded = pickle.loads(pickled_v5)
            assert loaded == data
        except ValueError:
            # Protocol not supported
            pytest.skip("Pickle protocol 5 not available")

    def test_pickle_modified_class(self):
        """Test unpickling with modified class definition"""
        class OriginalClass:
            def __init__(self, value):
                self.value = value

        obj = OriginalClass(42)
        pickled = pickle.dumps(obj)

        # Redefine class with different structure
        class OriginalClass:
            def __init__(self, value, new_field):
                self.value = value
                self.new_field = new_field

        # Unpickling should still work but might have issues
        loaded = pickle.loads(pickled)
        assert loaded.value == 42
        assert not hasattr(loaded, 'new_field')


class TestFileCorruption:
    """Test file corruption scenarios"""

    def test_empty_file_instead_of_data(self):
        """Test reading empty file when data expected"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name

        try:
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content == ""

            # Attempting to parse as JSON should fail
            with pytest.raises(json.JSONDecodeError):
                json.loads(content)
        finally:
            os.unlink(temp_path)

    def test_file_contains_binary_instead_of_text(self):
        """Test reading binary data when text expected"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\x04')
            temp_path = f.name

        try:
            with pytest.raises(UnicodeDecodeError):
                with open(temp_path, 'r', encoding='utf-8') as f:
                    f.read()
        finally:
            os.unlink(temp_path)

    def test_file_truncated_during_write(self):
        """Test handling partially written file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Simulate partial write
            f.write('{"key": "val')
            # File closed without completing write
            temp_path = f.name

        try:
            with open(temp_path, 'r') as f:
                content = f.read()

            with pytest.raises(json.JSONDecodeError):
                json.loads(content)
        finally:
            os.unlink(temp_path)

    def test_file_with_control_characters(self):
        """Test file containing control characters"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('{"key": "value\x00\x01\x02"}')
            temp_path = f.name

        try:
            with open(temp_path, 'r') as f:
                content = f.read()

            # Should parse but data contains control chars
            data = json.loads(content)
            assert '\x00' in data['key']
        finally:
            os.unlink(temp_path)

    def test_symlink_corruption(self):
        """Test broken symlink handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target.txt"
            link = Path(tmpdir) / "link.txt"

            # Create symlink to non-existent file
            link.symlink_to(target)

            # Reading should fail
            with pytest.raises(FileNotFoundError):
                link.read_text()


class TestDataValidationErrors:
    """Test data validation and corruption detection"""

    def test_checksum_mismatch(self):
        """Test checksum validation failure"""
        import hashlib

        data = b"important data"
        expected_checksum = hashlib.sha256(data).hexdigest()

        # Corrupt data
        corrupted_data = b"corrupted data"
        actual_checksum = hashlib.sha256(corrupted_data).hexdigest()

        assert expected_checksum != actual_checksum

    def test_data_schema_validation(self):
        """Test schema validation for corrupted data"""
        valid_data = {
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }

        corrupted_data = {
            "name": "John",
            "age": "thirty",  # Wrong type
            "email": "invalid-email"  # Invalid format
        }

        # Simple validation
        def validate_user(data):
            if not isinstance(data.get('age'), int):
                raise ValueError("Age must be integer")
            if '@' not in data.get('email', ''):
                raise ValueError("Invalid email")

        validate_user(valid_data)  # Should pass

        with pytest.raises(ValueError):
            validate_user(corrupted_data)

    def test_missing_required_fields(self):
        """Test data missing required fields"""
        complete_data = {
            "id": 1,
            "name": "Test",
            "value": 100
        }

        incomplete_data = {
            "id": 1,
            # Missing name and value
        }

        def validate_required(data, required_fields):
            missing = [f for f in required_fields if f not in data]
            if missing:
                raise ValueError(f"Missing fields: {missing}")

        validate_required(complete_data, ["id", "name", "value"])

        with pytest.raises(ValueError, match="Missing fields"):
            validate_required(incomplete_data, ["id", "name", "value"])

    def test_data_type_corruption(self):
        """Test data with wrong types"""
        def process_number(value):
            if not isinstance(value, (int, float)):
                raise TypeError(f"Expected number, got {type(value)}")
            return value * 2

        assert process_number(42) == 84

        with pytest.raises(TypeError):
            process_number("42")

    def test_circular_reference_detection(self):
        """Test detection of circular references"""
        data = {"key": "value"}
        data["self"] = data  # Circular reference

        with pytest.raises(ValueError):
            json.dumps(data)


class TestRecoveryMechanisms:
    """Test data recovery mechanisms"""

    def test_backup_file_recovery(self):
        """Test recovery from backup file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = Path(tmpdir) / "data.json"
            backup_file = Path(tmpdir) / "data.json.backup"

            # Create backup
            backup_data = {"backup": "data"}
            backup_file.write_text(json.dumps(backup_data))

            # Corrupt main file
            main_file.write_text("corrupted")

            # Recovery logic
            try:
                data = json.loads(main_file.read_text())
            except json.JSONDecodeError:
                if backup_file.exists():
                    data = json.loads(backup_file.read_text())

            assert data == backup_data

    def test_incremental_backup_recovery(self):
        """Test recovery from incremental backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            backups = []

            # Create multiple backup versions
            for i in range(3):
                backup_file = Path(tmpdir) / f"data.backup.{i}"
                backup_data = {"version": i, "data": f"state_{i}"}
                backup_file.write_text(json.dumps(backup_data))
                backups.append(backup_file)

            # Try loading from newest to oldest
            for backup in reversed(backups):
                try:
                    data = json.loads(backup.read_text())
                    break
                except Exception:
                    continue

            assert data["version"] == 2

    def test_transaction_log_recovery(self):
        """Test recovery using transaction log"""
        # Simulate transaction log
        transactions = [
            {"op": "set", "key": "a", "value": 1},
            {"op": "set", "key": "b", "value": 2},
            {"op": "set", "key": "c", "value": 3},
            {"op": "delete", "key": "a"},
        ]

        # Replay transactions
        state = {}
        for txn in transactions:
            if txn["op"] == "set":
                state[txn["key"]] = txn["value"]
            elif txn["op"] == "delete":
                state.pop(txn["key"], None)

        assert state == {"b": 2, "c": 3}

    def test_partial_data_recovery(self):
        """Test recovering partial valid data"""
        mixed_data = '''
        {"valid": "entry1"}
        {"corrupted": invalid}
        {"valid": "entry2"}
        '''

        valid_entries = []
        for line in mixed_data.strip().split('\n'):
            try:
                entry = json.loads(line.strip())
                valid_entries.append(entry)
            except json.JSONDecodeError:
                continue

        assert len(valid_entries) == 2
        assert valid_entries[0]["valid"] == "entry1"
        assert valid_entries[1]["valid"] == "entry2"

    def test_data_repair_attempt(self):
        """Test attempting to repair corrupted data"""
        corrupted = '{"key": "value", "missing_quote: "data"}'

        # Attempt repair by finding common issues
        repaired = corrupted

        # Add missing quote
        if 'missing_quote:' in repaired and 'missing_quote":' not in repaired:
            repaired = repaired.replace('missing_quote:', 'missing_quote":')

        data = json.loads(repaired)
        assert data["missing_quote"] == "data"


class TestDatabaseCorruption:
    """Test database corruption scenarios"""

    @pytest.mark.asyncio
    async def test_corrupted_sqlite_database(self):
        """Test handling corrupted SQLite database"""
        import sqlite3

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create database
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
            conn.commit()
            conn.close()

            # Corrupt the file
            with open(db_path, 'r+b') as f:
                f.seek(100)
                f.write(b'\x00' * 100)

            # Try to open corrupted database
            with pytest.raises(sqlite3.DatabaseError):
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT * FROM test")
                conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_concurrent_write_corruption(self):
        """Test corruption from concurrent writes"""
        import sqlite3

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create database
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
            conn.commit()

            # Simulate concurrent write without proper locking
            conn.execute("INSERT INTO test VALUES (1, 'value1')")
            # Don't commit, open another connection
            conn2 = sqlite3.connect(db_path)

            # This might cause locking issues
            try:
                conn2.execute("INSERT INTO test VALUES (1, 'value2')")
                conn2.commit()
            except sqlite3.IntegrityError:
                pass  # Expected due to PRIMARY KEY constraint

            conn.close()
            conn2.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
