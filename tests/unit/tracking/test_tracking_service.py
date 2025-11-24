"""
Unit tests for activity tracking service.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from windows_use.tracking.service import ActivityTracker
from windows_use.tracking.storage import ActivityStorage
from windows_use.desktop.service import Desktop


class TestActivityTracker:
    """Tests for ActivityTracker class."""
    
    @pytest.fixture
    def mock_storage(self):
        """Mock storage instance."""
        return MagicMock(spec=ActivityStorage)
    
    @pytest.fixture
    def mock_desktop(self):
        """Mock desktop instance."""
        mock = MagicMock(spec=Desktop)
        mock_app = MagicMock()
        mock_app.name = "Chrome"
        mock_app.window_title = "Test Page"
        mock.get_active_app.return_value = mock_app
        return mock
    
    @pytest.fixture
    def tracker(self, mock_storage, mock_desktop):
        """Create ActivityTracker instance with mocks."""
        return ActivityTracker(
            storage=mock_storage,
            desktop=mock_desktop,
            poll_interval=1.0
        )
    
    def test_tracker_initialization(self, mock_storage, mock_desktop):
        """Test tracker initializes correctly."""
        tracker = ActivityTracker(mock_storage, mock_desktop, poll_interval=2.0)
        
        assert tracker.storage == mock_storage
        assert tracker.desktop == mock_desktop
        assert tracker.poll_interval == 2.0
        assert tracker.current_activity is None
        assert not tracker.is_running
    
    def test_track_activity_new_app(self, tracker, mock_desktop, mock_storage):
        """Test tracking new application activity."""
        mock_app = MagicMock()
        mock_app.name = "Notepad"
        mock_app.window_title = "Untitled"
        mock_desktop.get_active_app.return_value = mock_app
        
        tracker._track_activity()
        
        assert tracker.current_activity is not None
        assert tracker.current_activity["app_name"] == "Notepad"
        assert tracker.current_activity["window_title"] == "Untitled"
    
    def test_track_activity_same_app(self, tracker, mock_desktop):
        """Test tracking continues with same app."""
        mock_app = MagicMock()
        mock_app.name = "Chrome"
        mock_app.window_title = "Test Page"
        mock_desktop.get_active_app.return_value = mock_app
        
        # First track
        tracker._track_activity()
        first_activity = tracker.current_activity
        
        # Second track with same app
        tracker._track_activity()
        
        assert tracker.current_activity == first_activity
    
    def test_track_activity_app_change(self, tracker, mock_desktop, mock_storage):
        """Test tracking when app changes."""
        # First app
        mock_app1 = MagicMock()
        mock_app1.name = "Notepad"
        mock_app1.window_title = "Test.txt"
        mock_desktop.get_active_app.return_value = mock_app1
        
        tracker._track_activity()
        
        # Change to second app
        mock_app2 = MagicMock()
        mock_app2.name = "Calculator"
        mock_app2.window_title = "Calculator"
        mock_desktop.get_active_app.return_value = mock_app2
        
        tracker._track_activity()
        
        # Should save the first activity
        mock_storage.save_activity.assert_called_once()
        assert tracker.current_activity["app_name"] == "Calculator"
    
    def test_start_tracking(self, tracker):
        """Test starting the tracker."""
        with patch.object(tracker, '_tracking_loop'):
            tracker.start()
            assert tracker.is_running
    
    def test_stop_tracking(self, tracker, mock_storage):
        """Test stopping the tracker."""
        tracker.is_running = True
        tracker.current_activity = {
            "app_name": "Chrome",
            "window_title": "Test",
            "start_time": datetime.now()
        }
        
        tracker.stop()
        
        assert not tracker.is_running
        mock_storage.save_activity.assert_called_once()
    
    def test_get_current_activity(self, tracker):
        """Test getting current activity."""
        tracker.current_activity = {
            "app_name": "VSCode",
            "window_title": "main.py"
        }
        
        activity = tracker.get_current_activity()
        
        assert activity["app_name"] == "VSCode"
        assert activity["window_title"] == "main.py"
    
    def test_track_activity_no_app(self, tracker, mock_desktop):
        """Test tracking when no app is active."""
        mock_desktop.get_active_app.return_value = None
        
        tracker._track_activity()
        
        # Should handle gracefully
        assert tracker.current_activity is None or tracker.current_activity.get("app_name") == "Unknown"

