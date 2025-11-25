"""
Unit tests for basic agent tools (Done, Wait, Launch, Switch).
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.tools.service import (
    done_tool,
    wait_tool,
    launch_tool,
    switch_tool
)
from windows_use.desktop.service import Desktop


class TestDoneTool:
    """Tests for Done Tool."""
    
    def test_done_tool_returns_answer(self):
        """Test that done_tool returns the answer string."""
        answer = "Task completed successfully"
        result = done_tool(answer=answer)
        assert result == answer
    
    def test_done_tool_with_empty_answer(self):
        """Test done_tool with empty answer."""
        answer = ""
        result = done_tool(answer=answer)
        assert result == ""
    
    def test_done_tool_with_long_answer(self):
        """Test done_tool with long answer text."""
        answer = "This is a very long answer " * 100
        result = done_tool(answer=answer)
        assert result == answer


class TestWaitTool:
    """Tests for Wait Tool."""
    
    @patch('windows_use.agent.tools.service.pg.sleep')
    def test_wait_tool_basic(self, mock_sleep):
        """Test wait_tool waits specified duration."""
        duration = 5
        result = wait_tool(duration=duration)
        
        mock_sleep.assert_called_once_with(duration)
        assert f'{duration} seconds' in result
    
    @patch('windows_use.agent.tools.service.pg.sleep')
    def test_wait_tool_zero_duration(self, mock_sleep):
        """Test wait_tool with zero duration."""
        result = wait_tool(duration=0)
        
        mock_sleep.assert_called_once_with(0)
        assert '0 seconds' in result
    
    @patch('windows_use.agent.tools.service.pg.sleep')
    def test_wait_tool_long_duration(self, mock_sleep):
        """Test wait_tool with long duration."""
        duration = 3600  # 1 hour
        result = wait_tool(duration=duration)
        
        mock_sleep.assert_called_once_with(duration)
        assert f'{duration} seconds' in result


class TestLaunchTool:
    """Tests for Launch Tool."""
    
    @patch('windows_use.agent.tools.service.pg.sleep')
    def test_launch_tool_success(self, mock_sleep):
        """Test successful app launch."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.launch_app.return_value = ("notepad", "Launched successfully", 0)
        mock_desktop.is_app_running.return_value = True
        mock_desktop.get_state.return_value = MagicMock()
        
        result = launch_tool(name="notepad", desktop=mock_desktop)
        
        mock_desktop.launch_app.assert_called_once_with("notepad")
        assert "notepad" in result.lower()
    
    @patch('windows_use.agent.tools.service.pg.sleep')
    def test_launch_tool_already_running(self, mock_sleep):
        """Test launching app that's already running."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.launch_app.return_value = (
            "calculator", 
            "Calculator is already running. Switched to it.", 
            0
        )
        
        result = launch_tool(name="calculator", desktop=mock_desktop)
        
        assert "calculator" in result.lower()
        assert "switch" in result.lower() or "already" in result.lower()
    
    def test_launch_tool_failure(self):
        """Test failed app launch."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.launch_app.return_value = (
            "nonexistent", 
            "App not found", 
            1  # Non-zero status indicates failure
        )
        
        result = launch_tool(name="nonexistent", desktop=mock_desktop)
        
        assert "failed" in result.lower()


class TestSwitchTool:
    """Tests for Switch Tool."""
    
    def test_switch_tool_success(self):
        """Test successful app switch."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.switch_app.return_value = ("Switched to notepad", 0)
        
        result = switch_tool(name="notepad", desktop=mock_desktop)
        
        mock_desktop.switch_app.assert_called_once_with("notepad")
        assert "notepad" in result.lower()
    
    def test_switch_tool_failure_raises_exception(self):
        """Test switch tool raises exception on failure."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.switch_app.return_value = ("App not found", 1)
        
        with pytest.raises(RuntimeError) as exc_info:
            switch_tool(name="nonexistent", desktop=mock_desktop)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_switch_tool_case_insensitive(self):
        """Test switch tool works with different cases."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.switch_app.return_value = ("Switched to Notepad", 0)
        
        result = switch_tool(name="NoTePaD", desktop=mock_desktop)
        
        mock_desktop.switch_app.assert_called_once_with("NoTePaD")


