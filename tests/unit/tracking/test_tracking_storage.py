"""
Unit tests for activity tracking storage.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from windows_use.tracking.storage import ActivityStorage


class TestActivityStorage:
    """Tests for ActivityStorage class."""
    
    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """Create temporary storage path."""
        return tmp_path / "test_data"
    
    @pytest.fixture
    def storage(self, temp_storage_path):
        """Create ActivityStorage instance with temp path."""
        return ActivityStorage(str(temp_storage_path))
    
    def test_storage_initialization(self, storage, temp_storage_path):
        """Test storage initializes with correct paths."""
        assert storage.base_dir == Path(temp_storage_path)
        assert storage.activities_dir.exists()
        assert storage.screenshots_dir.exists()
        assert storage.metadata_dir.exists()
        assert storage.summaries_dir.exists()
    
    def test_save_activity(self, storage):
        """Test saving activity data."""
        activity = {
            "app_name": "Chrome",
            "window_title": "Test Page",
            "start_time": datetime(2025, 11, 24, 14, 30, 0),
            "end_time": datetime(2025, 11, 24, 14, 35, 0),
            "duration_seconds": 300
        }
        
        storage.save_activity(activity)
        
        # Check file was created
        date_str = "2025-11-24"
        activity_file = storage.activities_dir / f"{date_str}.json"
        assert activity_file.exists()
        
        # Read and verify
        with open(activity_file, 'r') as f:
            data = json.load(f)
            assert len(data) > 0
            assert data[0]["app_name"] == "Chrome"
    
    def test_save_multiple_activities(self, storage):
        """Test saving multiple activities."""
        activities = [
            {
                "app_name": "Notepad",
                "window_title": "test.txt",
                "start_time": datetime(2025, 11, 24, 10, 0, 0),
                "end_time": datetime(2025, 11, 24, 10, 5, 0),
                "duration_seconds": 300
            },
            {
                "app_name": "Calculator",
                "window_title": "Calculator",
                "start_time": datetime(2025, 11, 24, 10, 5, 0),
                "end_time": datetime(2025, 11, 24, 10, 10, 0),
                "duration_seconds": 300
            }
        ]
        
        for activity in activities:
            storage.save_activity(activity)
        
        # Read and verify
        date_str = "2025-11-24"
        activity_file = storage.activities_dir / f"{date_str}.json"
        with open(activity_file, 'r') as f:
            data = json.load(f)
            assert len(data) >= 2
    
    def test_get_activities_for_date(self, storage):
        """Test retrieving activities for specific date."""
        # Save test activity
        activity = {
            "app_name": "VSCode",
            "window_title": "main.py",
            "start_time": datetime(2025, 11, 24, 15, 0, 0),
            "end_time": datetime(2025, 11, 24, 15, 30, 0),
            "duration_seconds": 1800
        }
        storage.save_activity(activity)
        
        # Retrieve
        activities = storage.get_activities_for_date("2025-11-24")
        
        assert len(activities) > 0
        assert activities[-1]["app_name"] == "VSCode"
    
    def test_get_activities_for_date_no_data(self, storage):
        """Test retrieving activities when no data exists."""
        activities = storage.get_activities_for_date("2099-12-31")
        
        assert activities == []
    
    def test_save_summary(self, storage):
        """Test saving daily summary."""
        summary = {
            "date": "2025-11-24",
            "total_active_time": 28800,
            "work_time": 21600,
            "entertainment_time": 7200,
            "focus_score": 85,
            "insights": "Good productivity day"
        }
        
        storage.save_summary(summary)
        
        # Check file was created
        summary_file = storage.summaries_dir / "2025-11-24.json"
        assert summary_file.exists()
        
        # Read and verify
        with open(summary_file, 'r') as f:
            data = json.load(f)
            assert data["focus_score"] == 85
    
    def test_get_summary(self, storage):
        """Test retrieving summary."""
        summary = {
            "date": "2025-11-24",
            "total_active_time": 14400,
            "focus_score": 75
        }
        storage.save_summary(summary)
        
        # Retrieve
        retrieved = storage.get_summary("2025-11-24")
        
        assert retrieved is not None
        assert retrieved["focus_score"] == 75
    
    def test_get_summary_no_data(self, storage):
        """Test retrieving summary when none exists."""
        summary = storage.get_summary("2099-12-31")
        
        assert summary is None
    
    def test_save_app_categories(self, storage):
        """Test saving app categories configuration."""
        categories = {
            "work": ["vscode", "visual studio", "pycharm"],
            "communication": ["slack", "teams", "outlook"],
            "entertainment": ["spotify", "youtube", "netflix"]
        }
        
        storage.save_app_categories(categories)
        
        # Check file was created
        categories_file = storage.metadata_dir / "app_categories.json"
        assert categories_file.exists()
        
        # Read and verify
        with open(categories_file, 'r') as f:
            data = json.load(f)
            assert "work" in data
            assert "vscode" in data["work"]
    
    def test_get_app_categories(self, storage):
        """Test retrieving app categories."""
        categories = {
            "work": ["notepad"],
            "entertainment": ["games"]
        }
        storage.save_app_categories(categories)
        
        # Retrieve
        retrieved = storage.get_app_categories()
        
        assert "work" in retrieved
        assert "notepad" in retrieved["work"]
    
    def test_get_app_categories_default(self, storage):
        """Test getting default app categories when none exist."""
        categories = storage.get_app_categories()
        
        # Should return default categories
        assert isinstance(categories, dict)
        assert len(categories) > 0









