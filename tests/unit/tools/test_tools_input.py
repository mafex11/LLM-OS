"""
Unit tests for input-related agent tools (Click, Type, Key, Shortcut, Clipboard).
"""

import pytest
from unittest.mock import MagicMock, patch, call
from windows_use.agent.tools.service import (
    click_tool,
    type_tool,
    key_tool,
    shortcut_tool,
    clipboard_tool
)
from windows_use.desktop.service import Desktop


class TestClickTool:
    """Tests for Click Tool."""
    
    @patch('windows_use.agent.tools.service.cursor')
    @patch('windows_use.agent.tools.service.pg')
    def test_click_tool_basic(self, mock_pg, mock_cursor):
        """Test basic click functionality."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "Button"
        mock_control.ControlTypeName = "ButtonControl"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = click_tool(loc=(100, 100), desktop=mock_desktop)
        
        mock_cursor.move_to.assert_called_once_with((100, 100), duration=0.8)
        mock_pg.click.assert_called_once_with(button='left', clicks=1)
        assert "clicked" in result.lower()
    
    @patch('windows_use.agent.tools.service.cursor')
    @patch('windows_use.agent.tools.service.pg')
    def test_click_tool_double_click(self, mock_pg, mock_cursor):
        """Test double click."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "File"
        mock_control.ControlTypeName = "ListItemControl"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = click_tool(loc=(100, 100), button='left', clicks=2, desktop=mock_desktop)
        
        mock_pg.click.assert_called_once_with(button='left', clicks=2)
        assert "double" in result.lower()
    
    @patch('windows_use.agent.tools.service.pg')
    def test_click_tool_out_of_bounds(self, mock_pg):
        """Test click with coordinates outside screen bounds."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        
        result = click_tool(loc=(3000, 3000), desktop=mock_desktop)
        
        assert "error" in result.lower()
        assert "outside" in result.lower()
    
    @patch('windows_use.agent.tools.service.cursor')
    @patch('windows_use.agent.tools.service.pg')
    def test_click_tool_right_button(self, mock_pg, mock_cursor):
        """Test right click."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "Menu"
        mock_control.ControlTypeName = "MenuControl"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = click_tool(loc=(500, 300), button='right', desktop=mock_desktop)
        
        mock_pg.click.assert_called_once_with(button='right', clicks=1)


class TestTypeTool:
    """Tests for Type Tool."""
    
    @patch('windows_use.agent.tools.service.cursor')
    @patch('windows_use.agent.tools.service.pg')
    def test_type_tool_basic(self, mock_pg, mock_cursor):
        """Test basic typing functionality."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "Text Box"
        mock_control.ControlTypeName = "EditControl"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = type_tool(loc=(100, 100), text="Hello World", desktop=mock_desktop)
        
        mock_cursor.move_to.assert_called_once_with((100, 100), duration=0.8)
        mock_pg.click.assert_called()
        mock_pg.typewrite.assert_called_once()
        assert "typed" in result.lower()
        assert "hello world" in result.lower()
    
    @patch('windows_use.agent.tools.service.cursor')
    @patch('windows_use.agent.tools.service.pg')
    def test_type_tool_with_clear(self, mock_pg, mock_cursor):
        """Test typing with clear option."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "Text Box"
        mock_control.ControlTypeName = "EditControl"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = type_tool(loc=(100, 100), text="New Text", clear='true', desktop=mock_desktop)
        
        # Check that Ctrl+A and backspace were called for clearing
        mock_pg.hotkey.assert_called_with('ctrl', 'a')
        mock_pg.press.assert_any_call('backspace')
        mock_pg.typewrite.assert_called_once()
    
    @patch('windows_use.agent.tools.service.cursor')
    @patch('windows_use.agent.tools.service.pg')
    def test_type_tool_with_enter(self, mock_pg, mock_cursor):
        """Test typing with enter press."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        mock_control = MagicMock()
        mock_control.Name = "Search Box"
        mock_control.ControlTypeName = "EditControl"
        mock_desktop.get_element_under_cursor.return_value = mock_control
        
        result = type_tool(
            loc=(100, 100), 
            text="Search query", 
            press_enter='true', 
            desktop=mock_desktop
        )
        
        mock_pg.typewrite.assert_called_once()
        mock_pg.press.assert_called_with('enter')
    
    @patch('windows_use.agent.tools.service.pg')
    def test_type_tool_out_of_bounds(self, mock_pg):
        """Test typing with coordinates outside screen bounds."""
        mock_pg.size.return_value = (1920, 1080)
        mock_desktop = MagicMock(spec=Desktop)
        
        result = type_tool(loc=(3000, 3000), text="test", desktop=mock_desktop)
        
        assert "error" in result.lower()
        assert "outside" in result.lower()


class TestKeyTool:
    """Tests for Key Tool."""
    
    @patch('windows_use.agent.tools.service.pg')
    def test_key_tool_basic(self, mock_pg):
        """Test basic key press."""
        result = key_tool(key='enter')
        
        mock_pg.press.assert_called_once_with('enter')
        assert "pressed" in result.lower()
        assert "enter" in result.lower()
    
    @patch('windows_use.agent.tools.service.pg')
    def test_key_tool_special_keys(self, mock_pg):
        """Test special key presses."""
        special_keys = ['escape', 'tab', 'backspace', 'delete', 'up', 'down', 'left', 'right']
        
        for key in special_keys:
            mock_pg.reset_mock()
            result = key_tool(key=key)
            mock_pg.press.assert_called_once_with(key)
            assert key in result.lower()
    
    @patch('windows_use.agent.tools.service.pg')
    def test_key_tool_function_keys(self, mock_pg):
        """Test function key presses."""
        result = key_tool(key='f1')
        
        mock_pg.press.assert_called_once_with('f1')
        assert "f1" in result.lower()


class TestShortcutTool:
    """Tests for Shortcut Tool."""
    
    @patch('windows_use.agent.tools.service.pg')
    def test_shortcut_tool_copy(self, mock_pg):
        """Test copy shortcut."""
        result = shortcut_tool(shortcut=['ctrl', 'c'])
        
        mock_pg.hotkey.assert_called_once_with('ctrl', 'c')
        assert "ctrl+c" in result.lower()
    
    @patch('windows_use.agent.tools.service.pg')
    def test_shortcut_tool_paste(self, mock_pg):
        """Test paste shortcut."""
        result = shortcut_tool(shortcut=['ctrl', 'v'])
        
        mock_pg.hotkey.assert_called_once_with('ctrl', 'v')
        assert "ctrl+v" in result.lower()
    
    @patch('windows_use.agent.tools.service.pg')
    def test_shortcut_tool_multiple_keys(self, mock_pg):
        """Test multi-key shortcut."""
        result = shortcut_tool(shortcut=['ctrl', 'shift', 's'])
        
        mock_pg.hotkey.assert_called_once_with('ctrl', 'shift', 's')
        assert "ctrl" in result.lower()
        assert "shift" in result.lower()
        assert "s" in result.lower()


class TestClipboardTool:
    """Tests for Clipboard Tool."""
    
    @patch('windows_use.agent.tools.service.pc')
    def test_clipboard_tool_copy(self, mock_pc):
        """Test copy to clipboard."""
        result = clipboard_tool(mode='copy', text='Test text')
        
        mock_pc.copy.assert_called_once_with('Test text')
        assert "copied" in result.lower()
        assert "test text" in result.lower()
    
    @patch('windows_use.agent.tools.service.pc')
    def test_clipboard_tool_paste(self, mock_pc):
        """Test paste from clipboard."""
        mock_pc.paste.return_value = 'Retrieved text'
        
        result = clipboard_tool(mode='paste')
        
        mock_pc.paste.assert_called_once()
        assert "retrieved text" in result.lower()
    
    def test_clipboard_tool_copy_no_text(self):
        """Test copy without providing text."""
        with pytest.raises(ValueError) as exc_info:
            clipboard_tool(mode='copy', text=None)
        
        assert "no text provided" in str(exc_info.value).lower()
    
    def test_clipboard_tool_invalid_mode(self):
        """Test clipboard tool with invalid mode."""
        with pytest.raises(ValueError) as exc_info:
            clipboard_tool(mode='invalid')
        
        assert "invalid mode" in str(exc_info.value).lower()


