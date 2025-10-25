"""Pytest Configuration and Fixtures"""
import pytest
import asyncio
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def mock_database():
    from unittest.mock import MagicMock
    return MagicMock()
