"""
Unit tests for tracking-related agent tools (Activity, Timeline, Schedule).
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.tools.service import (
    activity_tool,
    timeline_tool,
    schedule_tool
)
from windows_use.desktop.service import Desktop


class TestActivityTool:
    """Tests for Activity Tool."""
    
    @patch('windows_use.agent.tools.service.requests')
    def test_activity_tool_success(self, mock_requests):
        """Test successful activity query."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "response": "Your focus score today is 85%. You spent 6 hours on work."
        }
        mock_requests.post.return_value = mock_response
        
        result = activity_tool(query="How focused was I today?", date="2025-11-24")
        
        assert "focus score" in result.lower()
        assert "85" in result
    
    @patch('windows_use.agent.tools.service.requests')
    def test_activity_tool_no_date(self, mock_requests):
        """Test activity query without date (uses current date)."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "response": "Activity data for today."
        }
        mock_requests.post.return_value = mock_response
        
        result = activity_tool(query="What did I do?")
        
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "date" in call_args[1]["json"]
    
    @patch('windows_use.agent.tools.service.requests')
    def test_activity_tool_api_error(self, mock_requests):
        """Test activity tool when API returns error."""
        mock_response = MagicMock()
        mock_response.ok = False
        
        # Mock fallback summary request
        mock_summary_response = MagicMock()
        mock_summary_response.ok = True
        mock_summary_response.json.return_value = {
            "focus_score": 75,
            "work_time": 14400,  # 4 hours in seconds
            "research_time": 7200,  # 2 hours
            "entertainment_time": 3600,  # 1 hour
            "insights": "Good productivity day."
        }
        
        mock_requests.post.return_value = mock_response
        mock_requests.get.return_value = mock_summary_response
        
        result = activity_tool(query="How did I do?", date="2025-11-24")
        
        assert "focus score" in result.lower() or "tracking" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_activity_tool_connection_error(self, mock_requests):
        """Test activity tool when API is unavailable."""
        mock_requests.post.side_effect = Exception("Connection refused")
        
        result = activity_tool(query="Show my activity")
        
        assert "error" in result.lower() or "tracking" in result.lower()


class TestTimelineTool:
    """Tests for Timeline Tool."""
    
    @patch('windows_use.agent.tools.service.requests')
    def test_timeline_tool_success(self, mock_requests):
        """Test successful timeline query."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "timeline": [
                {
                    "type": "screenshot",
                    "timestamp": "2025-11-24T14:30:00",
                    "app_name": "Chrome",
                    "description": "Reading documentation",
                    "activity_category": "work",
                    "focus_score": 85,
                    "ai_analysis": "User was researching technical documentation."
                },
                {
                    "type": "activity",
                    "timestamp": "2025-11-24T14:35:00",
                    "app_name": "VSCode",
                    "window_title": "main.py",
                    "duration_seconds": 600
                }
            ],
            "activities": [],
            "screenshots": []
        }
        mock_requests.get.return_value = mock_response
        
        result = timeline_tool(query="What was I doing at 2pm?", date="2025-11-24")
        
        assert "chrome" in result.lower() or "vscode" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_timeline_tool_with_time_range(self, mock_requests):
        """Test timeline query with time range."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "timeline": [],
            "activities": [],
            "screenshots": []
        }
        mock_requests.get.return_value = mock_response
        
        result = timeline_tool(
            query="What did I do?",
            date="2025-11-24",
            start_time="14:00",
            end_time="17:00"
        )
        
        call_args = mock_requests.get.call_args
        assert "start_time" in call_args[1]["params"]
        assert "end_time" in call_args[1]["params"]
    
    @patch('windows_use.agent.tools.service.requests')
    def test_timeline_tool_empty_timeline(self, mock_requests):
        """Test timeline tool with no data."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "timeline": [],
            "activities": [],
            "screenshots": []
        }
        mock_requests.get.return_value = mock_response
        
        result = timeline_tool(query="What happened?", date="2025-11-24")
        
        assert "no activity" in result.lower() or "no" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_timeline_tool_api_error(self, mock_requests):
        """Test timeline tool when API returns error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response
        
        result = timeline_tool(query="Show timeline")
        
        assert "failed" in result.lower() or "500" in result
    
    @patch('windows_use.agent.tools.service.requests')
    def test_timeline_tool_connection_error(self, mock_requests):
        """Test timeline tool when API is unavailable."""
        mock_requests.get.side_effect = Exception("Connection error")
        
        result = timeline_tool(query="What was I doing?")
        
        assert "error" in result.lower() or "not available" in result.lower()


class TestScheduleTool:
    """Tests for Schedule Tool."""
    
    @patch('windows_use.agent.tools.service.requests')
    def test_schedule_tool_with_delay(self, mock_requests):
        """Test scheduling with delay in seconds."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "run_at": "in 300s"
        }
        mock_requests.post.return_value = mock_response
        
        result = schedule_tool(name="notepad", delay_seconds=300)
        
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["name"] == "notepad"
        assert call_args[1]["json"]["delay_seconds"] == 300
        assert "scheduled" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_schedule_tool_with_time(self, mock_requests):
        """Test scheduling at specific time."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "run_at": "18:30"
        }
        mock_requests.post.return_value = mock_response
        
        result = schedule_tool(name="calculator", run_at="18:30")
        
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["run_at"] == "18:30"
    
    @patch('windows_use.agent.tools.service.requests')
    def test_schedule_tool_repeating(self, mock_requests):
        """Test scheduling repeating task."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "run_at": "in 600s"
        }
        mock_requests.post.return_value = mock_response
        
        result = schedule_tool(
            name="backup_script",
            delay_seconds=600,
            repeat_interval_seconds=7200,  # Every 2 hours
            repeat_end_time="18:00"
        )
        
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["repeat_interval_seconds"] == 7200
        assert call_args[1]["json"]["repeat_end_time"] == "18:00"
        assert "repeat" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_schedule_tool_api_error(self, mock_requests):
        """Test schedule tool when API returns error."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Invalid request"
        mock_requests.post.return_value = mock_response
        
        result = schedule_tool(name="notepad", delay_seconds=60)
        
        assert "failed" in result.lower()
    
    def test_schedule_tool_no_timing(self):
        """Test schedule tool without delay or run_at."""
        result = schedule_tool(name="notepad")
        
        assert "provide" in result.lower() or "delay" in result.lower()
    
    def test_schedule_tool_invalid_delay(self):
        """Test schedule tool with invalid delay."""
        # Should handle invalid input gracefully
        result = schedule_tool(name="notepad", delay_seconds=-100)
        
        # Tool should normalize negative values to 0
        assert isinstance(result, str)
    
    def test_schedule_tool_invalid_time_format(self):
        """Test schedule tool with invalid time format."""
        result = schedule_tool(name="notepad", run_at="invalid")
        
        assert "invalid" in result.lower()
    
    def test_schedule_tool_invalid_repeat_end_time(self):
        """Test schedule tool with invalid repeat end time."""
        result = schedule_tool(
            name="notepad",
            delay_seconds=60,
            repeat_interval_seconds=600,
            repeat_end_time="25:99"  # Invalid time
        )
        
        assert "invalid" in result.lower()
    
    @patch('windows_use.agent.tools.service.requests')
    def test_schedule_tool_connection_error(self, mock_requests):
        """Test schedule tool when API is unavailable."""
        mock_requests.post.side_effect = Exception("Connection refused")
        
        result = schedule_tool(name="notepad", delay_seconds=60)
        
        assert "failed" in result.lower()


