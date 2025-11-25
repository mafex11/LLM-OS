"""
Unit tests for navigation-related agent tools (Scroll, Drag, Move, Resize).
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.tools.service import (
    scroll_tool,
    drag_tool,
    move_tool,
    resize_tool
)
from windows_use.desktop.service import Desktop


class TestScrollTool:
    """Tests for Scroll Tool."""
    
    @patch('windows_use.agent.tools.service.uia')
    @patch('windows_use.agent.tools.service.cursor')
    def test_scroll_tool_down(self, mock_cursor, mock_uia):
        """Test scrolling down."""
        result = scroll_tool(loc=(500, 500), type='vertical', direction='down', wheel_times=3)
        
        mock_cursor.move_to.assert_called_once_with((500, 500), duration=0.8)
        mock_uia.WheelDown.assert_called_once_with(3)
        assert "down" in result.lower()
    
    @patch('windows_use.agent.tools.service.uia')
    @patch('windows_use.agent.tools.service.cursor')
    def test_scroll_tool_up(self, mock_cursor, mock_uia):
        """Test scrolling up."""
        result = scroll_tool(loc=(500, 500), type='vertical', direction='up', wheel_times=5)
        
        mock_cursor.move_to.assert_called_once_with((500, 500), duration=0.8)
        mock_uia.WheelUp.assert_called_once_with(5)
        assert "up" in result.lower()
    
    @patch('windows_use.agent.tools.service.uia')
    @patch('windows_use.agent.tools.service.cursor')
    def test_scroll_tool_no_location(self, mock_cursor, mock_uia):
        """Test scrolling at current cursor position."""
        result = scroll_tool(type='vertical', direction='down', wheel_times=1)
        
        mock_cursor.move_to.assert_not_called()
        mock_uia.WheelDown.assert_called_once_with(1)
    
    @patch('windows_use.agent.tools.service.uia')
    @patch('windows_use.agent.tools.service.pg')
    @patch('windows_use.agent.tools.service.cursor')
    def test_scroll_tool_horizontal_left(self, mock_cursor, mock_pg, mock_uia):
        """Test horizontal scrolling left."""
        result = scroll_tool(type='horizontal', direction='left', wheel_times=2)
        
        mock_pg.keyDown.assert_called_with('Shift')
        mock_uia.WheelUp.assert_called_once_with(2)
        mock_pg.keyUp.assert_called_with('Shift')
        assert "left" in result.lower()
    
    @patch('windows_use.agent.tools.service.uia')
    @patch('windows_use.agent.tools.service.pg')
    @patch('windows_use.agent.tools.service.cursor')
    def test_scroll_tool_horizontal_right(self, mock_cursor, mock_pg, mock_uia):
        """Test horizontal scrolling right."""
        result = scroll_tool(type='horizontal', direction='right', wheel_times=2)
        
        mock_pg.keyDown.assert_called_with('Shift')
        mock_uia.WheelDown.assert_called_once_with(2)
        mock_pg.keyUp.assert_called_with('Shift')
        assert "right" in result.lower()
    
    def test_scroll_tool_invalid_direction(self):
        """Test scroll tool with invalid direction."""
        result = scroll_tool(type='vertical', direction='invalid')
        
        assert "invalid" in result.lower()
    
    def test_scroll_tool_invalid_type(self):
        """Test scroll tool with invalid type."""
        result = scroll_tool(type='invalid', direction='down')
        
        assert "invalid" in result.lower()


class TestDragTool:
    """Tests for Drag Tool."""
    
    @patch('windows_use.agent.tools.service.cursor')
    def test_drag_tool_basic(self, mock_cursor):
        """Test basic drag and drop."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "File.txt"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = drag_tool(from_loc=(100, 100), to_loc=(500, 500), desktop=mock_desktop)
        
        mock_cursor.drag_and_drop.assert_called_once_with((100, 100), (500, 500))
        assert "dragged" in result.lower()
    
    @patch('windows_use.agent.tools.service.cursor')
    def test_drag_tool_different_coordinates(self, mock_cursor):
        """Test drag with various coordinate combinations."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "Element"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        test_cases = [
            ((0, 0), (100, 100)),
            ((1920, 1080), (500, 500)),
            ((500, 300), (800, 700))
        ]
        
        for from_loc, to_loc in test_cases:
            mock_cursor.reset_mock()
            result = drag_tool(from_loc=from_loc, to_loc=to_loc, desktop=mock_desktop)
            mock_cursor.drag_and_drop.assert_called_once_with(from_loc, to_loc)


class TestMoveTool:
    """Tests for Move Tool."""
    
    @patch('windows_use.agent.tools.service.cursor')
    def test_move_tool_basic(self, mock_cursor):
        """Test basic cursor movement."""
        result = move_tool(to_loc=(300, 400))
        
        mock_cursor.move_to.assert_called_once_with((300, 400), duration=0.8)
        assert "moved" in result.lower()
    
    @patch('windows_use.agent.tools.service.cursor')
    def test_move_tool_different_positions(self, mock_cursor):
        """Test moving to various positions."""
        positions = [(0, 0), (1920, 1080), (500, 500), (100, 100)]
        
        for pos in positions:
            mock_cursor.reset_mock()
            result = move_tool(to_loc=pos)
            mock_cursor.move_to.assert_called_once_with(pos, duration=0.8)


class TestResizeTool:
    """Tests for Resize Tool."""
    
    def test_resize_tool_size_only(self):
        """Test resizing window with size only."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.resize_app.return_value = ("Resized notepad", 0)
        
        result = resize_tool(name="notepad", size=(800, 600), desktop=mock_desktop)
        
        mock_desktop.resize_app.assert_called_once_with("notepad", None, (800, 600))
        assert "resized" in result.lower()
    
    def test_resize_tool_location_and_size(self):
        """Test resizing and moving window."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.resize_app.return_value = ("Moved and resized calculator", 0)
        
        result = resize_tool(
            name="calculator", 
            loc=(100, 100), 
            size=(400, 300), 
            desktop=mock_desktop
        )
        
        mock_desktop.resize_app.assert_called_once_with("calculator", (100, 100), (400, 300))
    
    def test_resize_tool_location_only(self):
        """Test moving window without resizing."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.resize_app.return_value = ("Moved chrome", 0)
        
        result = resize_tool(name="chrome", loc=(200, 200), desktop=mock_desktop)
        
        mock_desktop.resize_app.assert_called_once_with("chrome", (200, 200), None)
    
    def test_resize_tool_failure(self):
        """Test resize tool when operation fails."""
        mock_desktop = MagicMock(spec=Desktop)
        mock_desktop.resize_app.return_value = ("App not found", 1)
        
        result = resize_tool(name="nonexistent", size=(800, 600), desktop=mock_desktop)
        
        assert "not found" in result.lower()


