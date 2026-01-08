"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_desktop():
    """Provide a mock Desktop instance for tests."""
    from windows_use.desktop.service import Desktop
    mock = MagicMock(spec=Desktop)
    
    # Setup common return values
    mock.get_state.return_value = MagicMock(
        active_app=MagicMock(name="TestApp", handle=12345),
        apps=[],
        tree_state=MagicMock(
            interactive_nodes=[],
            informative_nodes=[],
            scrollable_nodes=[]
        )
    )
    mock.get_apps.return_value = []
    mock.get_active_app.return_value = MagicMock(name="TestApp")
    mock.launch_app.return_value = ("app", "Success", 0)
    mock.switch_app.return_value = ("Switched", 0)
    mock.execute_command.return_value = ("Output", 0)
    mock.is_app_running.return_value = False
    
    return mock


@pytest.fixture
def mock_llm():
    """Provide a mock LLM for agent tests."""
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage
    
    mock = MagicMock(spec=BaseChatModel)
    mock.invoke.return_value = AIMessage(
        content='<thought>Test thought</thought><action_name>Done Tool</action_name><action_input>{"answer": "Complete"}</action_input>'
    )
    
    return mock


@pytest.fixture
def mock_storage(tmp_path):
    """Provide a mock ActivityStorage with temp directory."""
    from windows_use.tracking.storage import ActivityStorage
    
    storage_path = tmp_path / "test_storage"
    storage = ActivityStorage(str(storage_path))
    
    return storage


@pytest.fixture
def sample_activity():
    """Provide sample activity data for tests."""
    from datetime import datetime
    
    return {
        "app_name": "Chrome",
        "window_title": "Test Page",
        "start_time": datetime(2025, 11, 24, 14, 0, 0),
        "end_time": datetime(2025, 11, 24, 14, 30, 0),
        "duration_seconds": 1800,
        "category": "work"
    }


@pytest.fixture
def sample_activities():
    """Provide multiple sample activities."""
    from datetime import datetime
    
    return [
        {
            "app_name": "VSCode",
            "window_title": "main.py",
            "start_time": datetime(2025, 11, 24, 9, 0, 0),
            "end_time": datetime(2025, 11, 24, 11, 0, 0),
            "duration_seconds": 7200,
            "category": "work"
        },
        {
            "app_name": "Chrome",
            "window_title": "Documentation",
            "start_time": datetime(2025, 11, 24, 11, 0, 0),
            "end_time": datetime(2025, 11, 24, 12, 0, 0),
            "duration_seconds": 3600,
            "category": "research"
        },
        {
            "app_name": "Spotify",
            "window_title": "Music",
            "start_time": datetime(2025, 11, 24, 12, 0, 0),
            "end_time": datetime(2025, 11, 24, 12, 30, 0),
            "duration_seconds": 1800,
            "category": "entertainment"
        }
    ]


@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress logging output during tests for cleaner output."""
    import logging
    
    # Save original level
    original_level = logging.root.level
    
    # Set to ERROR to suppress INFO and DEBUG
    logging.root.setLevel(logging.ERROR)
    
    yield
    
    # Restore original level
    logging.root.setLevel(original_level)


@pytest.fixture
def mock_ui_control():
    """Provide a mock UI control for tree/desktop tests."""
    mock = MagicMock()
    mock.Name = "Test Control"
    mock.ControlTypeName = "ButtonControl"
    mock.BoundingRectangle = MagicMock(
        left=100, top=100, right=200, bottom=150,
        width=100, height=50
    )
    mock.IsEnabled = True
    mock.NativeWindowHandle = 12345
    
    return mock


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may be slower)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add marker based on test path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)









